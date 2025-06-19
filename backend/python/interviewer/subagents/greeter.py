from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types
from typing import AsyncGenerator, Optional

from . import configs

interviewer_instruction = """It is currently the greeting phase of the interview.

You are responsible for the initial greeting during this interview.

Please initiate a polite greet. If the interviewee did not respond, please greet them again.

For example, you can ask them how their day is going or how their week has been. Keep it professional.
"""

# # If you and the interviewee has already greeted, use the 'next_step_tool' call to proceed to the next phase.
# def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
#   """
  
#   """
#   callback_context.state["interview_instructions"] = interviewer_instruction.format(
#     interviewer_name=callback_context.state["interviewer_name"]
#   )


def next_step(tool_context: ToolContext) -> None:
  """
  Progress the conversation to the introduction phase.
  """
  if tool_context.state["phase"] == "greeting":
    tool_context.state["phase"] = "introduction"
    tool_context.actions.transfer_to_agent = "introducer"

next_step_tool = FunctionTool(func=next_step)

_instruction = """You are a content judge.

You are responsible for determining whether the interviewer and interviewee have both greeted each other.

Here is the conversation:

[start_interviewer]
{phase_agent_text}
[end_interviewer]

[start_interviewee]
{phase_client_text}
[end_interviewee]

If they have both greeted each other, you will call the 'next_step_tool' to progress the conversation.
"""

agent = LlmAgent(
  name="greeter",
  description="Handles the initial greeting phase of the interview conversation.",
  model=configs.get("model", "gemini-2.0-flash"),
  instruction=_instruction,
  tools=[next_step_tool,], 
  # before_agent_callback=[before_agent_callback,],
  generate_content_config=types.GenerateContentConfig(
    temperature=0.0
  ),
)