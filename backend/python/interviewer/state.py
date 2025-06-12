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


class InterviewRound:
  """
  Represents a single round of the interview.    
  """
  user_id: str
  session_id: str
  resume: str
  job_description: str
  socket: WebSocket
  latest_signal: float

  def __init__(self, user_id: str, session_id: str):
    self.user_id = user_id
    self.session_id = session_id

  def run(self):
    """
    Start the interview round.
    """
    if not self.resume or not self.job_description:
      logging.error("Interview Round is not ready. Missing resume or job description.")
      raise ValueError("Interview Round is not ready. Missing resume or job description.")
    
    if not self.socket:
      logging.error("Interview Round is not ready. Missing socket.")
      raise ValueError("Interview Round is not ready. Missing socket.")


class InterviewManager:
  """
  Facilitate adding/removing interview rounds
  and managing their lifecycle.
  """
  def __init__(self, config: dict):
    self.interviews: dict[str, InterviewRound] = {}
    self.setup_runner: Runner = Runner(
      app_name=self.config["name"] + "-setup",
      agent=root_agent,
      session_service=InMemorySessionService(),
    )
    self.interview_runner: InMemoryRunner = InMemoryRunner(
      app_name=self.config["name"],
      agent=root_agent,
    )

  async def connect(self, websocket: WebSocket, session_id: str, tries: int = 3) -> InterviewRound:
    """
    Check if Interview Round is ready. Once ready, accept websocket connection.
    """
    interview = self.interviews.set_default(session_id, InterviewRound())
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

  def get_run_configs(self) -> types.RunConfig:
    """
    Generate run configs from presets and dynamic values.
    """
    return RunConfig(
      streaming_mode=StreamingMode.BIDI,
      speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
          prebuilt_voice_config=types.PrebuiltVoiceConfig(
            voice_name=random.choice(self.config["voice_names"])
          )
        )
      ),
      response_modalities=["AUDIO"],
      output_audio_transcription=types.AudioTranscriptionConfig(),
      input_audio_transcription=types.AudioTranscriptionConfig(),
    )
  
  
  

