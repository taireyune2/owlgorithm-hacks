from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time
from . import configs

from .common import question_generator_second, route_interview
from .ontopic_detector import ontopic_detector_second

############################# live agent instructions ##############################
interviewer_instruction = """It is currently the followup question part of the interview.
The interviewee has already provided a response to a behavioral question.
You are responsible for asking the follow-up questions based on the behavioral question and the interviewee's response:

Behavioral question: {behavioral_question}

Interviewee's response:
{interviewee_response}

If the interviewee asks for clarification, please rephrase the question.
If the interviewee has started answering the question, DO NOT interrupt them.
You are ONLY to respond with affirmations like "tell me more", OR "okay", OR "nice" when the interviewee pause during their response.
"""

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  if callback_context.state["phase"] != "followup_question":
    ### setup state and instructions
    callback_context.state["phase"] = "followup_question"

    questions = callback_context.state["followup_questions"]
    if len(questions) > 0:
      response = callback_context.state["phase_client_text"].split(" [turn complete] ")
      callback_context.state["interview_instructions"] = interviewer_instruction.format(
        behavioral_question=questions[-1], interviewee_response="\n".join(response)
      )
    else:
      raise ValueError("No follow-up questions available in the state.")


################################ thought agent - state manager #####################################
def criteria_met(met: str, reason: str, tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  if met:
    logging.info("Criteria met, proceeding to next phase.")
    return route_interview(tool_context)

  logging.info(f"timings: { time.time() - tool_context.state['phase_start']} and {configs['durations']['followup']}")
  if time.time() - tool_context.state["phase_start"] > configs["durations"]["followup"]:
    logging.info("Follow-up question phase timed out, proceeding to next phase.")
    return route_interview(tool_context)

  tool_context.actions.skip_summarization = True

criteria_met_tool = FunctionTool(func=criteria_met)

_instruction = """You are an answer judge.
You are responsible for determining whether the interviewee has provided a detailed response to the follow-up question.
Here is the question: {question}
Here are the follow-up questions: {followup_questions}

Here is the response: 
[start_interviewee]
{phase_client_text}
[end_interviewee]

To meet the criteria, the interviewee's response should appropriately answer the follow-up question.

Tool call 'criteria_met_tool': 
If the interviewee's response meets the criteria, call the 'criteria_met_tool' with input 'True' and an empty reason string.
Otherwise, call the 'criteria_met_tool' with input 'False' and a reason string explaining why the criteria are not met.

Arguments for 'criteria_met_tool':
- met: boolean indicating whether the criteria are met
- reason: string explaining why the criteria are not met, if applicable.
"""

agent = LlmAgent(
  name="followup_questioner", 
  # name="followup_judge", 
  description="Questioner that asks a follow-up question based on the user's response.",
  model=configs["model"],
  instruction=_instruction,
  tools=[criteria_met_tool], 
  before_agent_callback=[before_agent_callback],
  include_contents='none',
  generate_content_config=types.GenerateContentConfig(
    temperature=0.0
  ),
)


# ######################## thought agent - workflow ##########################
# agent = ParallelAgent(
#   name="followup_questioner",
#   description="Agent that manages the follow-up question phase of the interview.",
#   sub_agents=[
#     followup_judge,
#     question_generator_second, 
#     ontopic_detector_second,
#   ],
#   before_agent_callback=[before_agent_callback],
# )