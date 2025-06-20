from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time
from . import configs


################################### live agent ###################################
_instruction = """You are an interviewer. Your name is {interviewer_name}.

You are currently in the behavioral question phase of the interview.
In this phase, you are responsible for asking the interviewee a behavioral question.
If the interviewee need a clarification, please provide a rephrase of the question.
If the interviewee has started answering the question, DO NOT interrupt them.
While they are answering the question, you are ONLY to respond with affirmations like "tell me more", "uh-huh", "okay", "hmm", "nice", etc.
"""

live_agent = LlmAgent(
  name="behavioral_questioner",
  description="Ask the interviewee behavioral questions.",
  model=configs["live"]["model"],
  instruction=_instruction,
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)

# def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
#   logging.info(f"Interview instructions:\n{callback_context.state['interview_instructions']}")

#   if callback_context.state["phase"] != "behavioral_question":
#     callback_context.state["phase_start"] = time.time()
#     callback_context.state["phase"] = "behavioral_question"
#     callback_context.state["interview_instructions"] = interviewer_instruction.format(
#       interviewer_background=callback_context.state["interviewer_background"]
#     )
#     return

#   if time.time() - callback_context.state["phase_start"] > configs["durations"]["introduction"]:
#     logging.info("Introduction phase timed out, proceeding to next phase.")
#     callback_context.actions.transfer_to_agent = "overview_judge"
#     return
  


# def get_next_question(tool_context: ToolContext) -> dict[str, str]:
#   """
#   If question count is greater than zero and there is enough time,
#   return the next question.
#   Else, direct to the closing phase.
#   """
#   ### store previous states # TODO: add to end of questioning
#   # if tool_context.state.get("previous_states", ""):
#   #   previous_states = tool_context.state["previous_states"].copy() 
#   #   previous_states.append({
#   #     "behavioral_question": tool_context.state["behavioral_question"]
#   #   })
#   #   tool_context.state["previous_states"] = previous_states

#   if not _interview_questions: 
#     raise ValueError("No more questions available.")
  
#   ### get question
#   question = _interview_questions[-1]
#   tool_context.state["behavioral_question"] = question
#   return {
#     "behavioral_question": question
#   }

# get_next_question_tool = FunctionTool(func=get_next_question)

_instruction = """You are an interviewer responsible for asking the interviewee behavioral questions.

Call the 'get_next_question_tool' to get the next question to ask the interviewee.
"""

thought_agent = LlmAgent(
  name="answer_completeness_checker",
  description="Determine whether the interviewee has answered the behavioral question.",
  model=configs["thought"]["model"],
  instruction="You are here to listen to the interviewee's answer and determine if they have answered the question sufficiently.",
  # tools=[criteria_met_tool], 
  include_contents='none',
  # before_agent_callback=[before_agent_callback],
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)