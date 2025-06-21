from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types

def close_interview(tool_context: ToolContext) -> None:
    """
    Progress the conversation to the closing phase.
    """
    if tool_context.state["phase"] == "closing":
        tool_context.state["phase"] = "closed"
        # No need to transfer to another agent since we're already in the closing phase

close_interview_tool = FunctionTool(func=close_interview)  
_instruction = """You are an interviewer named.
    You are responsible for closing the interview and providing a warm, professional farewell.
    Thank the interviewee for their time and interest.
    Let them know that you will reach out to them for the next steps in the hiring process.
    If the interviewee has already said farewell, proceed to the closing phase.
    Do not announce that you are closing the interview; just do it naturally.
    If the interviewee has already said farewell, use the 'close_interview_tool' call to proceed to the closing phase.
"""

agent = LlmAgent(
    name="closer",
    description="Handles the closing phase of the interview conversation.",
    model="gemini-2.0-flash",
    instruction=_instruction,
    tools=[close_interview_tool],
    generate_content_config=types.GenerateContentConfig(
        temperature=2.0
    ),  
)
    