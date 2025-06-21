from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time
from . import configs
from .introducer import interviewer_instruction as next_instruction

############################# live agent instruction #########################
interviewer_instruction = """It is currently the initial phase of the interview.
You are responsible for the opening conversation, the greeting exchange during this interview.

Start with a simple hi or hello. 
If the interviewee responds, continue the greeting exchange.
Do not ask any questions related to the interview or the job at this stage.
Make sure to keep the conversation light and friendly, but also professional.
Do not ask any questions related to the interview or the job at this stage.
"""
  

######################### thought agent ###############################
def step_complete(done: bool, tool_context: ToolContext) -> None:
  """
  Progress the conversation to the introduction phase.
  """
  logging.info(f"Step complete called with done={done}. {time.time()} - {tool_context.state['phase_start']} seconds since phase start.")
  if done:
    tool_context.actions.transfer_to_agent = "introduction_judge"
    return

  if time.time() - tool_context.state["phase_start"] > configs["durations"]["greeting"]:
    logging.info("Greeting phase timed out, proceeding to next phase.")
    tool_context.actions.transfer_to_agent = "introduction_judge"
    return

step_complete_tool = FunctionTool(func=step_complete)

_instruction = """You are a content judge.
You are responsible for determining whether the interviewer and interviewee have both greeted each other.
Here is the conversation:

interviewer:
{phase_agent_text}

interviewee:
{phase_client_text}

Tool call 'step_complete_tool': 
If both the interviewer and interviewee have greeted each other, call the 'step_complete_tool' with input 'True' to proceed.
Otherwise, call the 'step_complete_tool' with input 'False'.
"""

agent = LlmAgent(
  name="greeting_judge",
  description="Determine whether the interviewee has greeted",
  model=configs["model"],
  instruction=_instruction,
  tools=[step_complete_tool,], 
  include_contents='none',
  generate_content_config=types.GenerateContentConfig(
    temperature=0.0
  ),
)