from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types

def next_step(tool_context: ToolContext) -> None:
  """
  Progress the conversation to the introduction phase.
  """
  if tool_context.state["phase"] == "greeting":
    tool_context.state["phase"] = "introduction"
    tool_context.actions.transfer_to_agent = "introducer"

next_step_tool = FunctionTool(func=next_step)

_instruction = """You are an interviewer named.

You are responsible for the initial greeting during this interview.

Please initiate a polite greet. If the interviewee did not respond, please greet them again.

You can ask them how their day is going, how they are feeling today, or other polite greeting.

Keep it professional and friendly.

If you and the interviewee has already greeted, use the 'next_step_tool' call to proceed to the next phase.
"""

agent = LlmAgent(
  name="greeter",
  description="Handles the initial greeting phase of the interview conversation.",
  model="gemini-2.0-flash-exp",
  instruction=_instruction,
  tools=[next_step_tool], 
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)