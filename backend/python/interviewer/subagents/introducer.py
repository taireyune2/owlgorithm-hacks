from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types


def next_step(tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  if tool_context.state["phase"] == "introduction":
    tool_context.state["phase"] = "introduction_response"
    tool_context.actions.transfer_to_agent = "introduction_listener"

next_step_tool = FunctionTool(func=next_step)


_instruction = """You are an interviewer named {interviewer_name}.

You are responsible for giving interviewee a brief self-introduction of who you are and what you do. Keep it professional and humble. 
Here is your background: {interviewer_background}

Do not greet or say hi again, as the greeting phase has already been completed.
Ask the interviewee to also provide a brief self-introduction about themselves, including their background and experience.

If the interviewee is providing or has provided their self-introduction, you can proceed to the next phase by calling the 'next_step_tool'.
"""

agent = LlmAgent(
  name="introducer",
  description="Provide a self-introduction and elicit the interviewee's self-introduction.",
  model="gemini-2.0-flash-exp",
  instruction=_instruction,
  tools=[next_step_tool], 
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)