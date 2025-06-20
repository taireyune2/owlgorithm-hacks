from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time
from . import configs

from .followup_generator import question_generator

############################# live agent instructions ##############################
interviewer_instruction = """It is currently the followup question part of the interview.
The interviewee has already provided a response to a behavioral question.
You are responsible for asking the follow-up question.

Here is the follow-up question: {followup_question}

If the interviewee asks for clarification, please rephrase the question.
If the interviewee has started answering the question, DO NOT interrupt them.
You are ONLY to respond with affirmations like "tell me more", "uh-huh", "hmm", or "nice" when the interviewee is providing their response.
"""

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  if callback_context.state["phase"] != "followup_question":
    ### setup state and instructions
    callback_context.state["phase_start"] = time.time()
    callback_context.state["phase"] = "followup_question"
    callback_context.state["interview_instructions"] = interviewer_instruction.format(
      followup_question=callback_context.state["followup_question"]
    )
    return

  if time.time() - callback_context.state["phase_start"] > configs["durations"]["followup"]:
    logging.info("Follow-up question phase timed out, proceeding to next phase.")
    # callback_context.actions.transfer_to_agent = "overview_judge"
    return

################################ thought agent - state manager #####################################
def criteria_met(tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  logging.info("Criteria met in followup questioner, proceeding to next phase.")
  # tool_context.actions.transfer_to_agent = "overview_judge"

criteria_met_tool = FunctionTool(func=criteria_met)

_instruction = """You are an answer judge.
You are responsible for determining whether the interviewee has provided a detailed response to the follow-up question.
Here is the question: {question}
Here is the follow-up question: {followup_question}

Here is the response: 
[start_interviewee]
{phase_client_text}
[end_interviewee]

If the interviewee's response sufficiently answers the follow-up question, call the 'criteria_met_tool' to proceed to the next phase.
"""

followup_judge = LlmAgent(
  name="followup_judge", 
  description="Questioner that asks a follow-up question based on the user's response.",
  model=configs["model"],
  instruction=_instruction,
  tools=[criteria_met_tool], 
  include_contents='none',
  generate_content_config=types.GenerateContentConfig(
    temperature=0.0
  ),
)


######################## thought agent - workflow ##########################
agent = ParallelAgent(
  name="followup_questioner",
  description="Agent that manages the follow-up question phase of the interview.",
  sub_agents=[
    followup_judge,
    question_generator,
  ],
  before_agent_callback=[before_agent_callback],
)