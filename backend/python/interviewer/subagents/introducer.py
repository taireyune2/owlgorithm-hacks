from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time
from . import configs


################################### live agent ###################################
_instruction = """You are an interviewer. Your name is {interviewer_name}.

You are currently in the introduction phase of the interview.
Start off by giving the interviewee a self-introduction about yourself.
Your background information below:
{interviewer_background}
Keep it professional, humble, and concise.

Followup by asking the interviewee to provide a brief self-introduction about themselves, including their background and experience.
Once the interviewee has started their self-introduction, DO NOT interrupt the interviewee.
You are ONLY to respond with affirmations like "tell me more", "uh-huh", "okay", "hmm", or "nice" when the interviewee is providing their self-introduction.
"""

live_agent = LlmAgent(
  name="introducer",
  description="Provide and ask for a self-introduction.",
  model=configs["live"]["model"],
  instruction=_instruction,
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)

##################################### thought agent #####################################
def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  """
  Called before introducer agent runs.
  - update phase
  - obtain and check timestamp
  """
  logging.info(f"accessing introduction judge")
  if callback_context.state["phase"] != "introduction":
    callback_context.state["phase_start"] = time.time()
    callback_context.state["phase"] = "introduction"
    return

  if time.time() - callback_context.state["phase_start"] > configs["durations"]["introduction"]:
    logging.info("Introduction phase timed out, proceeding to next phase.")
    callback_context.actions.transfer_to_agent = "overview_judge"
    return
  

def criteria_met(tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  logging.info("Criteria met, proceeding to next phase.")
  # tool_context.state["phase"] = "overview"
  tool_context.actions.transfer_to_agent = "overview_judge"

criteria_met_tool = FunctionTool(func=criteria_met)


_instruction = """You are an introduction judge.

You are responsible for determining whether the interviewee has provided a detailed self-introduction.

Here is the self-introduction:
[start_interviewee]
{phase_client_text}
[end_interviewee]

The self-introduction should be at least 30 words long and include the interviewee's background and experience.

If the interviewee's self-introduction meets these criteria, call the 'criteria_met_tool' to proceed.
"""

thought_agent = LlmAgent(
  name="introduction_judge",
  description="Determine whether the interviewee has provided a detailed self-introduction.",
  model=configs["thought"]["model"],
  instruction=_instruction,
  tools=[criteria_met_tool], 
  include_contents='none',
  before_agent_callback=[before_agent_callback],
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)