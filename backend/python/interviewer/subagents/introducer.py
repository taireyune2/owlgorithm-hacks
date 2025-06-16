from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types


def next_step(interviewee_response: str,tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  if tool_context.state["phase"] == "introduction":
    tool_context.state["self_introduction"] = interviewee_response
    tool_context.state["phase"] = "overview"
    tool_context.actions.transfer_to_agent = "overviewer"

next_step_tool = FunctionTool(func=next_step)

_instruction = """You are an interviewer named {interviewer_name}.

Here is your background:

{interviewer_background}

You are responsible for giving interviewee a brief self-introduction of who you are and what you do. Keep it professional and humble. 

Do not greet or say hi again, as the greeting phase has already been completed.

Ask the interviewee to also provide a brief self-introduction about themselves, including their background and experience.

If the interviewee provided a satisfactory self-introduction, you can proceed to the next phase by calling the 'next_step_tool' using the 'interviewee_response'.
"""

agent = LlmAgent(
  name="introducer",
  description="Provide a self-introduction and elicit the interviewee's self-introduction.",
  model="gemini-2.0-flash",
  instruction=_instruction,
  tools=[next_step_tool], 
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)