from google.adk.agents import LlmAgent, BaseAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time
from . import configs
from .closing import closing

############################## live agent instructions ##############################
interviewer_instruction = """It is currently the closing phase of the interview.
You are responsible for providing a short summary of the interview and giving the interviewee the opportunity to ask questions.

Make sure the summary is short and concise, under 100 words.
Then giving the interviewee the opportunity to ask any questions.
"""

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  if callback_context.state["phase"] != "closing_question":
    callback_context.state["phase_start"] = time.time()
    callback_context.state["phase"] = "closing_question"
    callback_context.state["interview_instructions"] = interviewer_instruction

############################### thought agent ###############################

def criteria_met(met: bool, reason: str, tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  if met:
    logging.info("Criteria met, proceeding to next phase.")
    # tool_context.state["phase"] = "overview"
    closing(tool_context)
    return
  
  logging.info(f"Criteria not met: {reason}")
  logging.info(f"timings: { time.time() - tool_context.state["phase_start"]} and {configs["durations"]["closing"]}")
  if time.time() - tool_context.state["phase_start"] > configs["durations"]["closing"]:
    logging.info("Closing phase timed out, proceeding to next phase.")
    closing(tool_context)
    return
  
  tool_context.actions.skip_summarization = True

criteria_met_tool = FunctionTool(func=criteria_met)

_instruction = """You are a conversation judge.

You are responsible for determining whether the interviewer has provided a brief summary and answered all of the interviewee's questions.

Here is what the interviewer has said:
{phase_agent_text}

Here is what the interviewee has said:
{phase_client_text}

Criteria is met if the interviewer has provided a brief summary of the interview and answered all of the interviewee's questions.

If criteria is met, call the 'criteria_met_tool' with input 'True' and an empty reason string.
Otherwise, input 'False' to indicate that the criteria is not met and provide the reason.
"""


agent = LlmAgent(
  name="closing_responder",
  description="Determine whether the interviewee has provided a detailed self-introduction.",
  model=configs["model"],
  instruction=_instruction,
  tools=[criteria_met_tool], 
  before_agent_callback=[before_agent_callback],
  include_contents='none',
  generate_content_config=types.GenerateContentConfig(
    temperature=0.0
  ),
)
