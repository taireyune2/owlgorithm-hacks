from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
from . import configs

################################### live agent ###################################
_instruction = """You are an interviewer. Your name is {interviewer_name}.

You are in the initial phase of the interview.
You are responsible for the opening conversation, the greeting exchange during this interview.

Start with a simple "hi" or "hello". 
If the interviewee responds, continue the greeting exchange. Make small talk conversation with the interviewee to make them feel comfortable.
You can ask them about their day, week, or any other small talk topic that is appropriate.
DO NOT ask any questions related to the resume, interview, or the interview process at this stage.
Make sure to keep the conversation light and friendly, but sufficiently professional.
If the interviewee does not respond, continue to greet them until they respond.
"""

live_agent = LlmAgent(
  name="greeter",
  description="Greet the interviewee and make small talk to make them feel comfortable.",
  model=configs["live"]["model"],
  instruction=_instruction,
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)

##################################### thought agent #####################################
def step_complete(tool_context: ToolContext) -> None:
  """
  Progress the conversation to the introduction phase.
  """
  logging.info("Greeting exchange complete, proceeding to introduction phase.")
  # tool_context.state["phase"] = "introduction"
  tool_context.actions.transfer_to_agent = "introduction_judge"

step_complete_tool = FunctionTool(func=step_complete)

_instruction = """You are a content judge.
You are responsible for determining whether the interviewer and interviewee have both greeted each other.
Here is the conversation:

interviewer:
{phase_agent_text}

interviewee:
{phase_client_text}

Tool use 'step_complete_tool': call the 'step_complete_tool' if the interviewer and interviewee have both greeted each other
"""

thought_agent = LlmAgent(
  name="greeting_judge",
  description="Determine whether the interviewee has greeted",
  model=configs["thought"]["model"],
  instruction=_instruction,
  tools=[step_complete_tool,], 
  include_contents='none',
  # before_agent_callback=[before_agent_callback,],
  generate_content_config=types.GenerateContentConfig(
    temperature=0.0
  ),
)