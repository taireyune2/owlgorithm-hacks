
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.tools.agent_tool import AgentTool
from typing import AsyncGenerator
import asyncio
from google.adk.tools import google_search  # Import the tool

_instruction = """You are a converation agent.

Make sure to call 'record_response' with the user's response so program can record it.

Do not use the output from 'record_response'.
"""

# _instruction = """You are a question answering agent.
# Whenever you receive a question, always reply with the output from 'get_answer'.
# Call the 'get_answer' with the user's question.
# The 'get_answer' function will return the answer to the user's question.

# Please summarize the user's question and reply to the user.
# """


# async def get_answer(question: str, tool_context: ToolContext) -> AsyncGenerator[dict[str, str], None]:
async def record_response(response: str) -> None:
  """this function records the user's response"""
  print(f"Received user input: {response}")

# async def get_answer(question: str) -> AsyncGenerator[str, None]:
#   """this function returns an answer for the user"""
#   print(f"Received user input: {question}")
#   yield "This user's name is Tyler"


# answering_tool = FunctionTool(func=get_answer)


# root_agent = LlmAgent(
#   name="main_agent",
#   model="gemini-2.0-flash-exp",
#   description="Agent to answer questions using function call",
#   # Instructions to set the agent's behavior.
#   instruction=_instruction,
#   tools=[get_answer],
# )



root_agent = LlmAgent(
   name="google_search_agent",
   model="gemini-2.0-flash-exp", # if this model does not work, try below
   #model="gemini-2.0-flash-live-001",
   description="Agent to answer questions using Google Search.",
   instruction="Answer the question using the Google Search tool.",
   tools=[google_search],
)



# root_agent = LlmAgent(
#    name="conversation_agent",
#   #  model="gemini-2.0-flash-exp", # if this model does not work, try below
#    model="gemini-2.0-flash-live-001",
#    description="Agent that talks with the user",
#    instruction="You are responsible for conversing with the user. The user's name is {user_name}. Make sure to reply with the user's name if asked.",
#   #  instruction=_instruction,
#   #  tools=[record_response],
# )



# answering_machine_agent = LlmAgent(
#   name="answering_machine",
#   model="gemini-2.0-flash-exp",  # if this model does not work, try below
#   # model="gemini-2.0-flash-live-001",
#   description="Agent to answer special questions",
#   instruction="You are an answering machine agent. You will always answer 'Tyler has the answer'."
# )

# _instruction = """You are a greeting agent. 
# You are responsible for greeting the user.
# If the user asks any questions, call the 'answering_machine' tool to provide an answer.
# """

# root_agent = LlmAgent(
#   name="greeting_agent",
#   model="gemini-2.0-flash-exp", # if this model does not work, try below
#   #model="gemini-2.0-flash-live-001",
#   description="Greets the user and reply with the help of tools",
#   instruction=_instruction,
#   tools=[AgentTool(agent=answering_machine_agent)],
# )