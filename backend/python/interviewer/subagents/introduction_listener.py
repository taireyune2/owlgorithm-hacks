from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types


def next_step(interviewee_response: str,tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  if tool_context.state["phase"] == "introduction_response":
    tool_context.state["self_introduction"] = interviewee_response
    tool_context.state["phase"] = "overview"
    tool_context.actions.transfer_to_agent = "overviewer"

next_step_tool = FunctionTool(func=next_step)


_instruction = """You are an interviewer named {interviewer_name}.

You are responsible for listening to the interviewee's self-introduction.

Please encourage the interviewee to provide their self-introduction.

Respond with "Uh-huh", "Hmm", "Okay", etc.

If the interviewee has finished giving a full self-introduction, please call the 'next_step_tool' to proceed to the next step.
"""

agent = LlmAgent(
  name="introduction_listener",
  description="Listens to the interviewee's self-introduction and encourages them to speak.",
  model="gemini-2.0-flash-exp",
  instruction=_instruction,
  tools=[next_step_tool], 
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)