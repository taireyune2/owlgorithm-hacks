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

    results = []
    async for event in runner.run_async(
      user_id=self.session_id,
      session_id=self.session_id,
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
    return results[-1] 

        
  async def start_session(self, interviewer_background: str):
    """
    Start the interview round.
    """
    runner = InMemoryRunner(
      app_name=self.configs["name"],
      agent=root_agent,
    )

    # Create a Session
    session = await runner.session_service.create_session(
      app_name=self.configs["name"],
      user_id=self.session_id,  # Replace with actual user ID
      state={
        # "interviewer_name": "Alex",
        "interviewer_background": interviewer_background,
        # "interviewee_name": "Mike",
        "resume": self.resume,
        "job_description": self.job_description,
        "phase": "greeting"
      }
    )  

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

  async def prep_background(self, session_id: str, resume: str, job_description: str):
    """
    Add resume and job description to the interview round.
    """
    if session_id in self.interviews:
      logging.warning(f"Session {session_id} already exists. Overwriting existing interview round.")
      self.disconnect(session_id)
    
    interview = InterviewRound(
      session_id=session_id,
      session_service=self.session_service,
      run_config=self.get_run_configs(),
      configs=self.config
    )
    return await interview.prep_background(resume, job_description)

  async def connect(self, websocket: WebSocket, session_id: str, tries: int = 3) -> InterviewRound:
    """
    Check if Interview Round is ready. Once ready, accept websocket connection.
    """

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
  
  
  

