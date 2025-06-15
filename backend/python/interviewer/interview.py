import logging
import traceback
import json
import time
import random
import asyncio
import base64

from fastapi import WebSocket, WebSocketDisconnect
from google.adk.sessions import InMemorySessionService, BaseSessionService, Session
from google.adk.runners import InMemoryRunner, Runner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
from google.adk.events import Event
from typing import Optional, AsyncGenerator

from .agent import root_agent
from .preparer import preparation_agent
from . import socket


class Interviewer:
  app_name: str
  name: str
  voice: str
  background: str

  def __init__(self, app_name: str, name: str, voice: str, session_service: InMemorySessionService):
    self.app_name = app_name 
    self.name = name
    self.voice = voice
    self.session_service: InMemorySessionService = session_service

  async def prep_background(self, session_id: str, resume: str, job_description: str) -> str:
    """
    Run Synthesizer agent to prepare background information.
    """
    self.resume = resume
    self.job_description = job_description

    runner: Runner = Runner(
      app_name=self.app_name,
      agent=preparation_agent,
      session_service=self.session_service
    )
    session = await self.session_service.create_session(
      app_name=self.app_name,
      user_id=session_id,
      session_id=session_id,
      state={
        "interviewer_name": self.name,
        "resume": resume,
        "job_description": job_description
      }
    )

    results = []
    async for event in runner.run_async(
      user_id=session_id,
      session_id=session_id,
      new_message=types.Content(
        role="user",
        parts=[types.Part(text="")]
      )
    ):
      if event.is_final_response():
        results.append(event.content.parts[0].text)

    if not results:
      raise Exception("Agents failed to generate a proper response.")
    if results[-1].startswith("Invalid inputs: "):
      raise ValueError(results[-1])
    
    self.background = results[-1]
    return results[-1]

  def get_run_configs(self) -> RunConfig:
    """
    Generate run configs from presets and dynamic values.
    """
    return RunConfig(
      streaming_mode=StreamingMode.BIDI,
      speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
          prebuilt_voice_config=types.PrebuiltVoiceConfig(
            voice_name=self.voice
          )
        )
      ),
      response_modalities=["AUDIO"],
      output_audio_transcription=types.AudioTranscriptionConfig(),
      input_audio_transcription=types.AudioTranscriptionConfig(),
    )


class InterviewRound:
  """
  Represents a single round of the interview.    
  """
  app_name: str
  interviewer: Interviewer
  session_id: str
  socket: WebSocket
  latest_signal: float
  live_events: AsyncGenerator[Event, None]
  live_request_queue: LiveRequestQueue
  audio_queue: asyncio.Queue
  
  def __init__(
    self, 
    app_name: str,
    session_id: str, 
    interviewer: Interviewer,
  ):
    self.app_name = app_name
    self.session_id = session_id
    self.interviewer = interviewer
    self.audio_queue = asyncio.Queue()

  async def initialize_agent(self, resume: str, job_description: str):
    """
    Start the interview round.
    """
    try:
      runner = InMemoryRunner(
        app_name=self.app_name,
        agent=root_agent,
      )

      # Create a Session
      session = await runner.session_service.create_session(
        app_name=self.app_name,
        user_id=self.session_id,  # Replace with actual user ID
        state={
          "interviewer_name": self.interviewer.name,
          "interviewer_background": self.interviewer.background,
          # "interviewee_name": "Mike",
          "resume": resume,
          "job_description": job_description,
          "phase": "greeting"
        }
      )
      self.live_request_queue = LiveRequestQueue()
      self.live_events = runner.run_live(
        session=session,
        live_request_queue=self.live_request_queue,
        run_config=self.interviewer.get_run_configs()
      )
    except Exception as e:
      logging.error(f"Unhandled error in client_to_agent_messaging: {e}")
      logging.error(traceback.format_exc())

  def is_ready(self) -> bool:
    """
    Check if the interview round is ready to accept connections.
    """
    return self.live_events is not None
  
  async def run(self, websocket: WebSocket) -> None:
    """
    Run the interview round with the given WebSocket connection.
    """
    await websocket.accept()

    # Start tasks
    receive_and_process_responses_task = asyncio.create_task(
      socket.receive_and_process_responses(websocket, self.live_events)
    )
    client_to_agent_task = asyncio.create_task(socket.client_to_agent_messaging(
      websocket, 
      self.live_request_queue, 
      self.audio_queue
    ))
    process_and_send_audio_task = asyncio.create_task(
      socket.process_and_send_audio(self.live_request_queue, self.audio_queue)
    )

    # Wait until the websocket is disconnected or an error occurs
    tasks = [client_to_agent_task, process_and_send_audio_task, receive_and_process_responses_task]
    await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    for task in tasks:
      if task.done() and task.exception():
        exc = task.exception()
        logging.error(f"❌ Unhandled exception in task {task.get_coro().__name__}: {exc}")
        tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logging.error(tb)

    # Close LiveRequestQueue
    self.live_request_queue.close()

    # Disconnected
    logging.info(f"Client #{self.session_id} disconnected")

  def close(self):
    """
    Close the interview round and clean up resources.
    """
    if self.live_request_queue:
      self.live_request_queue.close()
    logging.info(f"Interview round {self.session_id} closed.")


class InterviewManager:
  """
  Facilitate adding/removing interview rounds
  and managing their lifecycle.
  """
  def __init__(self, config: dict):
    self.interviews: dict[str, InterviewRound] = {}
    self.config = config
    self.session_service = InMemorySessionService()

  async def initialize_interview(self, session_id: str, resume: str, job_description: str):
    """
    Prepare the interview round.
    Setup interviewer with background.
    Initialize agent.
    """
    if session_id in self.interviews:
      logging.warning(f"Session {session_id} already exists. Overwriting existing interview round.")
      self.disconnect(session_id)
    
    choice = random.choice(self.config["voices"]) 
    interviewer = Interviewer(
      self.config["name"], 
      choice["name"], 
      choice["voice"], 
      self.session_service
    )
    await interviewer.prep_background(session_id, resume, job_description)

    interview_round = InterviewRound(
      app_name=self.config["name"],
      session_id=session_id,
      interviewer=interviewer
    )
    interview_round.initialize_agent(resume, job_description)
    self.interviews[session_id] = interview_round
    
  async def connect(self, websocket: WebSocket, session_id: str, tries: int = 3):
    """
    Check if Interview Round is ready. Once ready, accept websocket connection.
    """
    if session_id not in self.interviews:
      logging.error(f"Session {session_id} not found. Cannot connect to interview round.")
      raise WebSocketDisconnect(f"Session {session_id} not found.")
    
    interview_round = self.interviews.get(session_id, None)
    if interview_round.is_ready():
      return await interview_round.run(websocket)

    if tries > 0:
      await asyncio.sleep(1)
      return await self.connect(websocket, session_id, tries - 1)
    else:
      self._disconnect(interview_round)
      raise WebSocketDisconnect(f"Interview Round {session_id} is not ready.")

  def _disconnect(self, interview_round: InterviewRound):
    interview_round.close()
    del self.interviews[interview_round.session_id]

  def disconnect(self, session_id: str):
    if session_id in self.interviews:
      self._disconnect(self.interviews[session_id])
  
  

