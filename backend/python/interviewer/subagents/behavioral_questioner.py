from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time
from . import configs

from .followup_generator import question_generator

##################################### live agent instructions #####################################
interviewer_instruction = """It is currently the main behavioral question phase of the interview.
In this phase, you are responsible for asking the interviewee a behavioral question.

Here is the question: {behavioral_question}

If the interviewee ask for clarification, please rephrase the question.
If the interviewee has starting answering the question, DO NOT interrupt them.
You are ONLY to respond with affirmations like "tell me more", "uh-huh", "hmm", or "nice" when the interviewee is providing their response.
"""

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  if callback_context.state["phase"] != "behavioral_question":
    ### setup states
    callback_context.state["phase_start"] = time.time()
    callback_context.state["phase"] = "behavioral_question"
    question = callback_context.state["interview_questions"][callback_context.state["question_index"]]
    callback_context.state["question"] = question
    callback_context.state["interview_instructions"] = interviewer_instruction.format(
      behavioral_question=question
    )

    ### clear previous phase context
    callback_context.state["phase_client_text"] = ""
    callback_context.state["phase_agent_text"] = ""
    return

  if time.time() - callback_context.state["phase_start"] > configs["durations"]["behavioral"]:
    logging.info("Behavioral question phase timed out, proceeding to next phase.")
    callback_context.actions.transfer_to_agent = "followup_questioner"
    return
  
##################### thought agent - state manager #####################################
def criteria_met(tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  logging.info("Criteria met, proceeding to next phase.")
  tool_context.actions.transfer_to_agent = "followup_questioner"

criteria_met_tool = FunctionTool(func=criteria_met)

_instruction = """You are an answer judge.
You are responsible for determining whether the interviewee has provided a detailed response to the behavioral question.
Here is the question: {question}

Here is the response: 
[start_interviewee]
{phase_client_text}
[end_interviewee]

The response should at least 100 words and provide a detailed answer to the question.
If the response meets the criteria, call the 'criteria_met_tool' to proceed to the next phase.
"""#TODO adjust word count

answer_judge = LlmAgent(
  name="answer_judge",
  description="Judge the interviewee's answers to behavioral questions.",
  model=configs["model"],
  instruction=_instruction,
  tools=[criteria_met_tool], 
  include_contents='none',
  generate_content_config=types.GenerateContentConfig(
    temperature=0.0
  ),
)


##################### thought agent - workflow #####################################
agent = ParallelAgent(
  name="behavioral_questioner",
  description="Agent that manages the behavioral question phase of the interview.",
  sub_agents=[
    answer_judge,
    question_generator,
  ],
  before_agent_callback=[before_agent_callback],
)