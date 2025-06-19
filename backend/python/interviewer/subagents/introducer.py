from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging

from . import configs

interviewer_instruction = """It is currently the introduction phase of the interview.
In this phase, you are responsible for providing a self-introduction to the interviewee and then asking them to provide a self-introduction.
Here is your background information:
{interviewer_background}
Keep it professional, humble, and concise. 
Followup with a question asking the interviewee to provide a brief self-introduction about themselves, including their background and experience.
DO NOT interrupt the interviewee while they are providing their self-introduction. At most respond with affirmations like "Uh-huh", "hmm", "okay", "nice".
"""


def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  logging.info(f"Before agent callback for {callback_context.agent_name}.")
  callback_context.state["interview_instructions"] = interviewer_instruction.format(
    interviewer_background=callback_context.state["interviewer_background"]
  )


def criteria_met(tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  logging.info("Criteria met, proceeding to next phase.")
    # tool_context.actions.transfer_to_agent = "introduction_listener"

criteria_met_tool = FunctionTool(func=criteria_met)


_instruction = """You are an introduction judge.

You are responsible for determining whether the interviewee has provided a detailed self-introduction.

Here is the self-introduction:
[start_interviewee]
{phase_client_text}
[end_interviewee]

The self-introduction should be at least 30 words long and include the interviewee's background and experience.

If the interviewee's self-introduction meets these criteria, call the 'criteria_met_tool' to proceed.
"""

agent = LlmAgent(
  name="introduction_judge",
  description="Determine whether the interviewee has provided a detailed self-introduction.",
  model=configs["model"],
  instruction=_instruction,
  tools=[criteria_met_tool], 
  include_contents='none',
  # before_agent_callback=[before_agent_callback,],
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)