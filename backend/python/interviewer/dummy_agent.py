from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types

import logging  

def get_step(tool_context: ToolContext) -> dict[str, int]:
  """
  Get the current step count.

  Returns:
    dict: {"step_number": count representing the current step in the interview process}
  """
  logging.info(tool_context.state["count"])
  return {
    "step_number": tool_context.state["count"]
  }

get_step_tool = FunctionTool(func=get_step)

_instruction = """You are an interviewer named {interviewer_name}.

You are responsible for a professional conversation and obtaining a brief self-introduction from the interviewee.
Keep it professional and humble.

Before your every question, please say the step number by calling 'get_step_tool'.

"""

root_agent = LlmAgent(
  name="interviewer",
  description="Interviewer responsible for conversing with the interviewee and obtaining a self-intro from the interviewee.",
  model="gemini-2.0-flash-exp",
  instruction=_instruction,
  tools=[get_step_tool], 
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)