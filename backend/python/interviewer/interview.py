import logging
import traceback
import json
import time
import random
import asyncio
import base64
from typing import Optional, AsyncGenerator

from fastapi import WebSocket, WebSocketDisconnect
from google.adk.sessions import InMemorySessionService, BaseSessionService, Session
from google.adk.runners import InMemoryRunner, Runner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
from google.adk.events import Event, EventActions
from google.adk.tools import ToolContext, FunctionTool


# from .agent import root_agent
from .dummy_agent import get_step, root_agent
from .preparer import preparation_agent
from . import socket
from google.adk.agents import LlmAgent


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
  session: Session
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
    self._index = 1

  def _get_dynamic_instruction(self) -> str:
    """
    Generate dynamic instruction for the agent.

    Returns:
      str: Instruction for the agent.
    """
    instructions = [
      "Say you studied mathematics",
      "Say you graduated 2014",
      "Say you work at Google",
    ]
    current = instructions[self._index]
    logging.info(f"Dynamic instruction: {current}")
    return current

  def get_root_agent(self):
    instruction = """You are an interviewer named {interviewer_name}.

Please ALWAYS follow the instructions from 'get_instruction_tool'.

"""
    get_instruction_tool = FunctionTool(func=self._get_dynamic_instruction)
    return LlmAgent(
      name="interviewer",
      description="Converse with the user by following the instructions from 'get_instruction_tool'.",
      model="gemini-2.0-flash-exp",
      instruction=instruction,
      tools=[get_instruction_tool], 
      generate_content_config=types.GenerateContentConfig(
        temperature=2.0
      ),
      include_contents='none',
    )

  async def initialize_agent(self, resume: str, job_description: str) -> tuple[AsyncGenerator[Event, None], LiveRequestQueue]:
    """
    Start the interview round.
    """
    try:
      self.root_agent = self.get_root_agent()
      self.runner = InMemoryRunner(
        app_name=self.app_name,
        agent=self.root_agent,
      )

      # Create a Session
      self.session = await self.runner.session_service.create_session(
        app_name=self.app_name,
        user_id=self.session_id,  # Replace with actual user ID
        state={
          "interviewer_name": self.interviewer.name,
          "interviewer_background": self.interviewer.background,
          # "interviewee_name": "Mike",
          "resume": resume,
          "job_description": job_description,
          "phase": "greeting",
          "count": 0,
        }
      )
      self.live_request_queue = LiveRequestQueue()
      self.live_events = self.runner.run_live(
        session=self.session,
        live_request_queue=self.live_request_queue,
        run_config=self.interviewer.get_run_configs()
      )
      logging.info(f"Interview round {self.session_id} initialized with interviewer {self.interviewer.name}.")
    except Exception as e:
      logging.error(f"Unhandled error in initialize_agent: {e}")
      logging.error(traceback.format_exc())
      raise e

  def is_ready(self) -> bool:
    """
    Check if the interview round is ready to accept connections.
    """
    return self.live_events is not None
  
  async def broadcast_state(self, websocket: WebSocket) -> None:
    while True:
      actions_with_update = EventActions(
        state_delta={"count": (self.session.state["count"] + 1) % 3}
      )
      self._index = (self._index + 1) % 3
      system_event = Event(
        invocation_id="update_count",
        author="system", # Or 'agent', 'tool' etc.
        actions=actions_with_update,
        # content might be None or represent the action taken
      )
      await self.runner.session_service.append_event(self.session, system_event)
      logging.info(f"Broadcasting state: index={self._index} phase={self.session.state['phase']}, count={self.session.state['count']}")
      
      # await websocket.send_text(json.dumps(message))
      await asyncio.sleep(5)

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

    broadcast_state_task = asyncio.create_task(
      self.broadcast_state(websocket)
    )
    # Wait until the websocket is disconnected or an error occurs
    tasks = [
      client_to_agent_task, 
      process_and_send_audio_task, 
      receive_and_process_responses_task,
      broadcast_state_task,
    ]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    # Cancel any pending tasks immediately
    for task in pending:
      task.cancel()
      try:
        await task
      except asyncio.CancelledError:
        logging.info(f"✅ Cancelled task: {task.get_coro().__name__}")

    # Handle exceptions and cancellations for completed tasks
    for task in done:
      if task.cancelled():
        logging.info(f"⚠️ Task {task.get_coro().__name__} was cancelled")
      elif task.exception():
        exc = task.exception()
        errorCode = exc.code
        if errorCode == 1000:
          logging.info(f"✅ Session ended by user: {task.get_coro().__name__}")
        else:
          logging.error(f"❌ Unhandled exception in task {task.get_coro().__name__}: {exc}")
          tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
          logging.error(tb)
          raise exc

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
    self.interviews[session_id] = interview_round
    await interview_round.initialize_agent(resume, job_description)

  async def connect(self, websocket: WebSocket, session_id: str, tries: int = 3):
    """
    Check if Interview Round is ready. Once ready, accept websocket connection.
    """
    interview_round = self.interviews.get(session_id, None)
    if not interview_round or not interview_round.is_ready():
      if tries > 0:
        logging.info(f"Interview Round {session_id} is not ready. Retrying in 1 second with {tries} retries...")
        await asyncio.sleep(1)
        return await self.connect(websocket, session_id, tries - 1)
      else:
        logging.error(f"Interview Round {session_id} is not ready after retries. Disconnecting.")
        self.disconnect(session_id)
        raise WebSocketDisconnect(f"Interview Round {session_id} is not ready after retries.")
    
    return await interview_round.run(websocket)

  def disconnect(self, session_id: str):
    interview_round = self.interviews.get(session_id, None)
    if interview_round:
      interview_round.close()
      del self.interviews[interview_round.session_id]

