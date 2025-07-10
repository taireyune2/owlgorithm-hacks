from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time

from . import configs


############################### live agent instructions ##############################
interviewer_instruction = """It is currently the overview phase of the interview.
In this phase, you are responsible for providing an overview of the interview process and setting expectations.
The interview will consist of a few questions to understand how the interviewee thinks, collaborates, and navigates real-world challenges. 
There will be one behavioral question and takes about 5 minutes. There will not be any technical questions. There shall be some time at the end for the interviewee to ask questions.
Ask whether the interviewee is ready to continue.
If the interviewee asks for clarification, please reply with a rephrase of the overview.
DO NOT ask the actual interview question.
"""


def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  logging.info("Entering overview phase callback.")
  if callback_context.state["phase"] != "overview":
    callback_context.state["phase_start"] = time.time()
    callback_context.state["phase"] = "overview"
    callback_context.state["interview_instructions"] = interviewer_instruction

    ### clear previous phase context
    callback_context.state["phase_client_text"] = ""
    callback_context.state["phase_agent_text"] = ""


############################### thought agent ###############################
NEXT_STEP_AGENT = "behavioral_questioner"

def next_step(met: bool, tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  if met:
    logging.info("Criteria met, proceeding to next phase.")
    tool_context.actions.transfer_to_agent = NEXT_STEP_AGENT
    return

  if time.time() - tool_context.state["phase_start"] > configs["durations"]["overview"]:
    logging.info("Overview phase timed out, proceeding to next phase.")
    tool_context.actions.transfer_to_agent = NEXT_STEP_AGENT
    return
  
  tool_context.actions.skip_summarization = True

next_step_tool = FunctionTool(func=next_step)

_instruction = """You are responsible for deciding if the interview can proceed.

Here is what the interviewer has said so far:
{phase_agent_text}

Here is the interviewee's response:
[start_interviewee]
{phase_client_text}
[end_interviewee]

Criteria for proceeding to the next step:
1. the interviewer has provided an overview/expectation for the interview process,
2. and the interviewee has acknowledged the overview and is ready to continue with the interview.

Tool call 'next_step_tool':
If the criteria are met, call the 'next_step_tool' with input 'True'.
Otherwise, call the 'next_step_tool' with input 'False'.
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
    temperature=0.0
  ),
)
