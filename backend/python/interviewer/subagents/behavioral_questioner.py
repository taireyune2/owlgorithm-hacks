from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time

from . import configs

from .common import question_generator_first, route_interview

##################################### live agent instructions #####################################
interviewer_instruction = """It is currently the main behavioral question phase of the interview.
In this phase, you are responsible for asking the interviewee a behavioral question.

Here is the question: {behavioral_question}

If the interviewee ask for clarification, please rephrase the question.
If the interviewee has starting answering the question, DO NOT interrupt them.
You are ONLY to respond with affirmations like "tell me more", "okay",  or "nice" when the interviewee is providing their response.
"""

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  logging.info("Entering behavioral question phase callback.")
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

##################### thought agent - state manager #####################################
def criteria_met(met: bool, reason: str, tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  if met:
    logging.info("Criteria met, proceeding to next phase.")
    return route_interview(tool_context)

  logging.info(f"timings: { time.time() - tool_context.state['phase_start']} and {configs['durations']['behavioral']}")
  if time.time() - tool_context.state["phase_start"] > configs["durations"]["behavioral"]:
    logging.info("Behavioral question phase timed out, proceeding to next phase.")
    return route_interview(tool_context)
    
  tool_context.actions.skip_summarization = True

criteria_met_tool = FunctionTool(func=criteria_met)

_instruction = """You are an answer judge.
You are responsible for determining whether the interviewee has provided a detailed response to the behavioral question.
Here is the question: {question}

Here is the response: 
[start_interviewee]
{phase_client_text}
[end_interviewee]

To meet the criteria, the response should at least 100 words and provide a detailed answer to the question.

Tool call 'criteria_met_tool': 
If the interviewee's response meets the criteria, call the 'criteria_met_tool' with input 'True' and an empty reason.
Otherwise, call the 'criteria_met_tool' with input 'False' to indicate that the response is insufficient and provide the reason.

Arguments for 'criteria_met_tool':
- met: A boolean indicating whether the criteria are met.
- reason: A string explaining why the criteria are not met, if applicable.
"""

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
    question_generator_first,
  ],
  before_agent_callback=[before_agent_callback],
)