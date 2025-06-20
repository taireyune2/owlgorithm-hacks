from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
from . import configs
from .introducer import interviewer_instruction as next_instruction

############################# live agent instruction #########################
interviewer_instruction = """It is currently the initial phase of the interview.
You are responsible for the opening conversation, the greeting exchange during this interview.

Start with a simple hi or hello. 
If the interviewee responds, continue the greeting exchange. Make small talk to make the interviewee feel comfortable and relaxed.
You can ask them about their day, week, or any other light topic to break the ice.
Do not ask any questions related to the interview or the job at this stage.
Make sure to keep the conversation light and friendly, but also professional.
Do not ask any questions related to the interview or the job at this stage.
"""

######################### thought agent ###############################
def step_complete(tool_context: ToolContext) -> None:
  """
  Progress the conversation to the introduction phase.
  """
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

Tool use 'step_complete_tool': call the 'step_complete_tool' if the interviewer and interviewee have both greeted each other or have started a small talk.
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