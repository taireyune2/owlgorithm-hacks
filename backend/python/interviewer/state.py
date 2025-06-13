import logging
import json
import time
import random
import asyncio

from fastapi import WebSocket, WebSocketDisconnect
from google.adk.sessions import InMemorySessionService, BaseSessionService, Session
from google.adk.runners import InMemoryRunner, Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

from .agent import root_agent
from .preparer import preparation_agent


class InterviewRound:
  """
  Represents a single round of the interview.    
  """
  manager: InterviewManager
  user_id: str
  session_id: str
  resume: str
  job_description: str
  socket: WebSocket
  latest_signal: float

  run_config: RunConfig
  session_service: InMemorySessionService
  configs: dict

  def __init__(
    self, 
    session_id: str, 
    session_service: InMemorySessionService, 
    run_config: RunConfig, 
    configs: dict,
  ):
    self.session_id = session_id
    self.run_config = run_config
    self.session_service: InMemorySessionService = session_service
    self.configs = configs

  async def start_session(self):
    """
    Start the interview round.
    """
    if not self.resume or not self.job_description:
      logging.error("Interview Round is not ready. Missing resume or job description.")
      raise ValueError("Interview Round is not ready. Missing resume or job description.")
    
    if not self.socket:
      logging.error("Interview Round is not ready. Missing socket.")
      raise ValueError("Interview Round is not ready. Missing socket.")
    
  async def prep_background(self, resume: str, job_description: str) -> str:
    """
    Run Synthesizer agent to prepare background information.
    """
    self.resume = resume
    self.job_description = job_description

    runner: Runner = Runner(
      app_name=self.configs["name"] + "-setup",
      agent=preparation_agent,
      session_service=self.session_service
    )
    session = await self.session_service.create_session(
      app_name=self.configs["name"] + "-setup",
      user_id=self.session_id,
      session_id=self.session_id,
      state={
        "resume": resume,
        "job_description": job_description
      }
    )

    async for event in runner.run_async(
      user_id=self.session_id,
      session_id=self.session_id,
      new_message=types.Content(
        role="user",
        parts=[types.Part(text="")]
      )
    ):
      if event.is_final_response():
        return event.content.parts[0].text
        
  def run_session(self):
    pass


class InterviewManager:
  """
  Facilitate adding/removing interview rounds
  and managing their lifecycle.
  """
  def __init__(self, config: dict):
    self.interviews: dict[str, InterviewRound] = {}
    self.config = config
    self.session_service = InMemorySessionService()

    self.interview_runner: InMemoryRunner = InMemoryRunner(
      app_name=self.config["name"],
      agent=root_agent,
    )

  def add_info(self, session_id: str, resume: str, job_description: str):
    """
    Add resume and job description to the interview round.
    """
    interview = self.interviews.set_default(session_id, InterviewRound(session_id, session_id))
    interview.resume = resume
    interview.job_description = job_description
    logging.info(f"Added info for session {session_id}: resume and job description.")

  async def connect(self, websocket: WebSocket, session_id: str, tries: int = 3) -> InterviewRound:
    """
    Check if Interview Round is ready. Once ready, accept websocket connection.
    """
    interview = self.interviews.set_default(session_id, InterviewRound(session_id, session_id))
    for _ in range(tries):
      if interview.resume and interview.job_description:
        interview.socket = websocket
        interview.latest_signal = time.time()
        websocket.accept()
        return interview
      await asyncio.sleep(0.5)

    self.disconnect(session_id)
    raise WebSocketDisconnect(f"Interview Round {session_id} is not ready.")

  def disconnect(self, session_id: str):
    pass

  def cleanup(self, timeout: int = 30):
    pass

  def get_run_configs(self) -> RunConfig:
    """
    Generate run configs from presets and dynamic values.
    """
    return RunConfig(
      streaming_mode=StreamingMode.BIDI,
      speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
          prebuilt_voice_config=types.PrebuiltVoiceConfig(
            voice_name=random.choice(self.configs["voice_names"])
          )
        )
      ),
      response_modalities=["AUDIO"],
      output_audio_transcription=types.AudioTranscriptionConfig(),
      input_audio_transcription=types.AudioTranscriptionConfig(),
    )
  
  
  

