from typing import Callable

from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.events import Event
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

_instruction = """You are an interviewer agent that conducts interviews with candidates.

This is your background information:
{}
You will always use the instructions from the 'get_instruction_tool' function to guide your actions.

DO NOT deviate from the instructions provided by the tool.
"""


class LiveAgentSystem:
  def __init__(self, app_name: str, voice: str, get_instructions: Callable[..., str]):
    """
    Handles the lifecycle of the live agent.
    """
    self.app_name = app_name
    get_instructions_tool = FunctionTool(func=get_instructions)
    root_agent = LlmAgent(
      name="root_agent",
      description="Agent that conducts live interviews by following tool-call instructions.",
      instruction=_instruction,
      tools=[get_instructions_tool],
    )
    self.runner = InMemoryRunner(
      app_name=self.app_name,
      agent=root_agent,
    )
    self.live_request_queue = LiveRequestQueue()

  def get_run_config(self, voice: str) -> RunConfig:
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

  async def start_session(
    self,
    session_id: str,
    interviewer_name: str,
    voice: str,
    background: str,
  ):
    self.session = await self.runner.session_service.create_session(
      app_name=self.app_name,
      user_id=session_id, 
      state={
        "interviewer_name": interviewer_name,
        "interviewer_background": background,
      }
    )
    self.live_events = self.runner.run_live(
      session=self.session,
      live_request_queue=self.live_request_queue,
      run_config=self.get_run_configs(voice)
    )
    
  async def close(self):
    """
    Close the runner and clean up resources.
    """
    await self.live_request_queue.close()
    await self.runner.close()

