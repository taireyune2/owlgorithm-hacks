from typing import Callable

from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService, Session
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.events import Event, EventActions
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types


_entrypoint_instruction = """You are responsible for the opening conversation, the greeting exchange during this interview.
Start with a simple "hi" or "hello". 
If the interviewee responds, transfer to 'interviewer'.
"""

_interviewer_instruction = """Use the instructions from 'get_instructions_tool' to conduct the interview. 

Follow the instructions provided by the 'get_instructions_tool'.
DO NOT say anything about following instructions or tools or moving too the next step.
"""


class LiveAgentSystem:
  def __init__(self):
    self.runner: InMemoryRunner = None
    self.live_request_queue: LiveRequestQueue = None
    self.session: Session = None
    self.app_name = None
    self.live_events = None

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
    get_instructions_tool = FunctionTool(func=get_instructions)
    interviewer_agent = LlmAgent(
      name="interviewer",
      description="Agent that conducts live interviews by following the tool-call instructions.",
      model=model,
      instruction=_interviewer_instruction,
      tools=[get_instructions_tool],
    )
    root_agent = LlmAgent(
      name="call_initiator",
      description="Start the opening conversation and transfer to the interviewer agent.",
      model=model,
      instruction=_entrypoint_instruction,
      sub_agents=[interviewer_agent],
    )
    self.runner = InMemoryRunner(
      app_name=self.app_name,
      agent=root_agent,
    )
    self.live_request_queue = LiveRequestQueue()
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

    ### agent need to initiate the conversation
    self.live_request_queue.send_content(
      types.Content(
        role="user", 
        parts=[types.Part(text="Hi")],
        # parts=[types.Part(text="[SYSTEM] Start by saying 'hi' or 'hello'.")],
      )
    )

  async def close(self):
    """
    Close the runner and clean up resources.
    """
    if isinstance(self.live_request_queue, LiveRequestQueue):
      self.live_request_queue.close()
    if isinstance(self.runner, InMemoryRunner):
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