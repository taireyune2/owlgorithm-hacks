from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
from . import configs
from .introducer import interviewer_instruction as next_instruction

interviewer_instruction = """It is currently the greeting phase of the interview.
You are responsible for the initial greeting during this interview.
Initiate a simple hi or hello. 
If the interviewee responds with a greet, followup with a more formal greet. 
For example, you can ask them how their day is going or how their week has been. Keep it professional.
"""

def step_complete(tool_context: ToolContext) -> None:
  """
  Progress the conversation to the introduction phase.
  """
  logging.info("Progressing to the introduction phase.")
  if tool_context.state["phase"] == "greeting":
    tool_context.state["phase"] = "introduction"
    tool_context.state["interview_instructions"] = next_instruction.format(
      interviewer_background=tool_context.state["interviewer_background"]
    )
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

agent = LlmAgent(
  name="greeting_judge",
  description="Determine whether the interviewee has greeted",
  model=configs["model"],
  instruction=_instruction,
  tools=[step_complete_tool,], 
  include_contents='none',
  # before_agent_callback=[before_agent_callback,],
  generate_content_config=types.GenerateContentConfig(
    temperature=0.0
  ),
)