from google.adk.agents import BaseAgent, LlmAgent, ParallelAgent, SequentialAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext

from google.genai import types
from typing import AsyncGenerator, Optional, override

from pydantic import BaseModel, Field

import logging
import time

from . import configs

from .common import (
  init_question_generator, RoutingAgent, JudgeResult
)
from .ontopic_detector import init_ontopic_agent

##################################### live agent instructions #####################################
interviewer_instruction = """It is currently the main behavioral question phase of the interview.
In this phase, you are responsible for asking the interviewee a behavioral question.

Here is the question: {behavioral_question}

If the interviewee ask for clarification, please rephrase the question.
If the interviewee has starting answering the question, DO NOT interrupt them.
You are ONLY to respond with affirmations like "tell me more", OR "okay", OR "nice" when the interviewee pause during their response.
"""

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  logging.info("Entering behavioral question phase callback.")
  callback_context.state["judge_result"] = {}
  callback_context.state["interview_instructions"] = interviewer_instruction.format(
    behavioral_question=callback_context.state["question"]
  )
  return None


########################## thought agent - answer judge #####################################
_instruction = """You are an answer judge.
You are responsible for determining whether the interviewee has provided a detailed response to the behavioral question.
Here is the question: {question}

Here is the response: 
[start_interviewee]
{phase_client_text}
[end_interviewee]

To meet the criteria, the response should at least 50 words and provide a detailed answer to the question.
 
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

answer_judge = LlmAgent(
  name="answer_judge",
  description="Judge the interviewee's answers to behavioral questions.",
  model=configs["model"],
  # before_agent_callback=[before_agent_callback],
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

##################### thought agent - workflow #####################################
parallel_agent = ParallelAgent(
  name="behavioral_parallel_agent", #"behavioral_questioner",
  description="Agent that manages the tasks during the behavioral question phase of the interview.",
  sub_agents=[
    answer_judge,
    init_question_generator("behavioral_question_generator"),
    # init_ontopic_agent("behavioral_ontopic_agent"),
  ],
)

routing_agent = RoutingAgent(
  name="behavioral_routing_agent",
  interviewer_instruction=interviewer_instruction
)

agent = SequentialAgent(
  name="behavioral_questioner",
  description="Agent that manages the behavioral question phase of the interview.",
  sub_agents=[
    parallel_agent,
    routing_agent,
  ],
)