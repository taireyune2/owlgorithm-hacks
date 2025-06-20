from typing import Callable, AsyncGenerator, Optional
import logging
import asyncio

from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.events import Event, EventActions
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

# _instruction = """You're name is {interviewer_name}.

# You are an interviewer that conducts interviews with interviewees.

# Use the instructions from 'get_instructions_tool' to conduct the interview. 

# Do not deviate from the instructions provided by the 'get_instructions_tool'.
# """
from .agent import live_agent

class LiveAgentSystem:
  def __init__(self):
    self.app_name = None
    self.runner: InMemoryRunner = None
    self.live_request_queue: LiveRequestQueue = None
    self.session: Optional[Session] = None
    self.live_events: AsyncGenerator[Event, None] = None

  async def start_session(
    self,
    app_name: str, 
    session_id: str,
    interviewer_name: str,
    voice: str,
    background: str,
    model: str,
    get_instructions: Callable[..., str],
  ):
    self.app_name = app_name
    # get_instructions_tool = FunctionTool(func=get_instructions)
    # root_agent = LlmAgent(
    #   name="interviewer",
    #   description="Agent that conducts live interviews by following the tool-call instructions.",
    #   model=model,
    #   instruction=_instruction,
    #   tools=[get_instructions_tool],
    # )
    self.runner = InMemoryRunner(
      app_name=self.app_name,
      agent=live_agent,
    )
    self.live_request_queue = LiveRequestQueue()
    self.session = await self.runner.session_service.create_session(
      app_name=self.app_name,
      user_id=session_id, 
      state={
        "interviewer_name": interviewer_name,
        "interviewer_background": background,
        "phase": "greeting",
        "question": "",
      }
    )
    self.live_events = self.runner.run_live(
      session=self.session,
      live_request_queue=self.live_request_queue,
      run_config=self.get_run_configs(voice)
    )

    ### agent need to initiate the conversation
    self.live_request_queue.send_content(
      types.Content(
        role="user", 
        parts=[types.Part(text="[System] Please start by saying 'hi' or 'hello'")]
      )
    )

  async def close(self):
    """
    Close the runner and clean up resources.
    """
    if self.live_request_queue:
      await self.live_request_queue.close()
    await self.runner.close()

  def get_run_configs(self, voice: str) -> RunConfig:
    return RunConfig(
      streaming_mode=StreamingMode.BIDI,
      speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
          prebuilt_voice_config=types.PrebuiltVoiceConfig(
            voice_name=voice
          )
        )
      ),
      response_modalities=["AUDIO"],
      output_audio_transcription=types.AudioTranscriptionConfig(),
      input_audio_transcription=types.AudioTranscriptionConfig(),
    )
  
  async def update(self, *, phase: str, question: str) -> None:
    """
    Update the agent internal state from thought
    """
    state_delta = {
      "phase": phase,
      "question": question,
    }
    logging.info(f"Updating live agent state: {state_delta}")
    system_event = Event(
      invocation_id="phase_change",
      author="system",
      actions=EventActions(state_delta=state_delta),
    )
    await self.runner.session_service.append_event(self.session, system_event)

  async def get_state(self) -> dict:
    """
    Obtain the current phase of the interview from session state.

    Returns:
      dict: Current state of the interview.
    """
    # session = await self.runner.session_service.get_session(
    #   app_name=self.session.app_name,
    #   user_id=self.session.id,
    # )
    logging.info(f"Live agent state: {self.session.state}")
    return self.session.state.copy()