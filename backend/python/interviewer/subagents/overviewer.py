from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time

from . import configs

interviewer_instruction = """It is currently the overview phase of the interview.
In this phase, you are responsible for providing an overview of the interview process and setting expectations.
The interview will consist of a few questions to understand how the interviewee thinks, collaborates, and navigates real-world challenges. (1 to 2 behavioral questions and takes about 10 minutes). There will not be any technical questions. There shall be some time at the end for the interviewee to ask questions.
Ask whether the interviewee is ready to continue.
If the interviewee asks to clarify, please reply with a rephrase of the overview.
"""

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  logging.info(f"Interview instructions:\n{callback_context.state['interview_instructions']}")
  if callback_context.state["phase"] != "overview":
    callback_context.state["phase_start"] = time.time()
    callback_context.state["phase"] = "overview"
    callback_context.state["interview_instructions"] = interviewer_instruction
    return
  
  if time.time() - callback_context.state["phase_start"] > configs["durations"]["overview"]:
    logging.info("Overview phase timed out, proceeding to next phase.")
    callback_context.actions.transfer_to_agent = "behavioral_questioner"
    return


def next_step(tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  logging.info("Proceeding to next phase.")
  tool_context.state["phase"] = "behavioral_question"
  tool_context.actions.transfer_to_agent = "behavioral_questioner"

next_step_tool = FunctionTool(func=next_step)

_instruction = """You are here to decide if the interview can proceed.

Here is the interviewee's response:
[start_interviewee]
{immediate_client_text}
[end_interviewee]

If the interviewee confirms or is ready for the next step, call the 'next_step_tool' to continue.
"""


agent = LlmAgent(
  name="overview_judge",
  description="Determine if the interviewee is ready to continue to the next step of the interview.",
  model=configs["model"],
  instruction=_instruction,
  tools=[next_step_tool],
  before_agent_callback=[before_agent_callback],
  include_contents='none',
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)
