from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types


def next_step(interviewee_response: str, tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  if tool_context.state["phase"] == "introduction_response":
    tool_context.state["self_introduction"] = interviewee_response
    tool_context.state["phase"] = "overview"
    tool_context.actions.transfer_to_agent = "overviewer"

next_step_tool = FunctionTool(func=next_step)


_instruction = """You are responsible for listening to the interviewee's self-introduction.

DO NOT INTERRUPT the interviewee while they are speaking.
ONLY REPLY with words of affirmation like "Uh-huh", "Hmm", "Okay", etc.

Once the interviewee has given a full self-introduction which is about 50 words, 
call the 'next_step_tool' with the content of the interviewee's self-introduction to continue.
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