from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time
from . import configs


##################### thought agent - question generator #####################################
def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  ### skip this if there is not enough content
  content = callback_context.state["phase_client_text"]
  if len(content) < 30:
    logging.info("Too early to generate follow-up question, waiting for more response.")
    return types.Content(
      role="model",
      parts=[types.Part(text="")],
    )

_instruction = """You are a question asker.
You are responsible for generating questions based on the user's behavioral response.

Here is the behavioral question: {question}
And previous follow-up question: {followup_question}

Here is the response from the interviewee: 
[start_interviewee]
{phase_client_text}
[end_interviewee]

Based on this response, what question can the interviewer ask as a followup?
Ask a question that is relevant to the response and encourages the interviewee to either:
- elaborate further, 
- clarify any points, 
- or provide specific examples.

Only write down the question you came up with. 
DO NOT repeat the previous follow-up question.
DO NOT include any additional discussion in your response.
"""

question_generator = LlmAgent(
  name="question_generator",
  description="Generate follow-up questions based on the interviewee's responses.",
  model=configs["model"],
  instruction=_instruction,
  before_agent_callback=[before_agent_callback],
  include_contents='none',
  output_key="followup_question",
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)