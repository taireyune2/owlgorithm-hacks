from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types

def next_step(tool_context: ToolContext) -> None:
    """
    Progress the conversation to the next phase.
    """
    if tool_context.state["phase"] == "overview":
        tool_context.state["phase"] = "behavioral_question"
        tool_context.actions.transfer_to_agent = "behavioral_questioner"

next_step_tool = FunctionTool(func=next_step)

_instruction = """You are an interviewer named {interviewer_name}.

You shall provide the interviewee with an overview of what to expect in the rest of the interview session.

The interview will consist of a few questions to understand how the interviewee thinks, collaborates, and navigates real-world challenges. (1 to 2 behavioral questions and takes about 10 minutes). There will not be any technical questions. There shall be some time at the end for the interviewee to ask questions.

Ask whether the interviewee is ready to continue. If the interviewee confirms or is ready for the next step, call the 'next_step_tool' to continue.

Otherwise, if the interviewee asks to clarify, please reply with a rephrase of the overview.
"""

agent = LlmAgent(
    name="overviewer",
    description="Provide an overview of the interview process and set expectations.",
    model="gemini-2.0-flash",
    instruction=_instruction,
    tools=[next_step_tool], 
    generate_content_config=types.GenerateContentConfig(
        temperature=2.0
    ),
)
