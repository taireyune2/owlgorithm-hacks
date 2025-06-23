from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time
from . import configs

from .common import (
  init_question_generator, JudgeResult, RoutingAgent
)
from .ontopic_detector import init_ontopic_agent

############################# live agent instructions ##############################
interviewer_instruction = """It is currently the followup question part of the interview.
The interviewee has already provided a response to a behavioral question.
You are responsible for asking the follow-up question.

Here is the follow-up question: {followup_question}

If the interviewee asks for clarification, please rephrase the question.
If the interviewee has started answering the question, DO NOT interrupt them.
You are ONLY to respond with affirmations like "tell me more", OR "okay", OR "nice" when the interviewee pause during their response.
"""

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  logging.info("Entering followup question phase callback.")
  callback_context.state["judge_result"] = {}
  questions = callback_context.state["followup_questions"]
  if len(questions) > 0:
    callback_context.state["interview_instructions"] = interviewer_instruction.format(
      followup_question=questions[-1]
    )
  else:
    raise ValueError("No follow-up questions available in the state.")


################################ thought agent - state manager #####################################
_instruction = """You are an answer judge.
You are responsible for determining whether the interviewee has provided a detailed response to the follow-up question.
Here is the question: {question}
Here are the follow-up questions: {followup_questions}

Here is the response: 
[start_interviewee]
{phase_client_text}
[end_interviewee]

To meet the criteria, the interviewee's response should appropriately answer the follow-up question.

If the interviewee's response meets the criteria, return true with an empty reason string.
Otherwise, return false with a reason string explaining why the criteria are not met.

Respond ONLY in valid JSON format following this schema:
```json
{
  "met": bool,
  "explanation": str (If false, brief explanation of why the criteria are not met)"
}
```
"""

followup_judge = LlmAgent(
  name="followup_judge", 
  description="Questioner that asks a follow-up question based on the user's response.",
  model=configs["model"],
  instruction=_instruction, 
  output_schema=JudgeResult,
  output_key="judge_result",
  disallow_transfer_to_parent=True,
  disallow_transfer_to_peers=True,
  include_contents='none',
  generate_content_config=types.GenerateContentConfig(
    temperature=0.0
  ),
)


######################## thought agent - workflow ##########################
parallel_agent = ParallelAgent(
  name="followup_questioner",
  description="Agent that manages the follow-up question phase of the interview.",
  sub_agents=[
    followup_judge,
    init_question_generator("followup_question_generator"),
    # init_ontopic_agent("followup_ontopic_agent"),
  ],
  # before_agent_callback=[before_agent_callback],
)

routing_agent = RoutingAgent(
  name="followup_routing_agent", 
  interviewer_instruction=interviewer_instruction
)

agent = SequentialAgent(
  name="followup_questioner",
  description="Agent that manages the follow-up question phase of the interview.",
  sub_agents=[
    parallel_agent,
    routing_agent,
  ],
  # before_agent_callback=[before_agent_callback],
)
