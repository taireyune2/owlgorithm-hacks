from google.adk.agents import LlmAgent, BaseAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time
from . import configs

############################## live agent instructions ##############################
interviewer_instruction = """It is currently the introduction phase of the interview.
In this phase, you are responsible for providing your background to the interviewee and then asking them to provide a self-introduction.
Here is your background information:
{interviewer_background}
Keep it professional, humble, and concise. 
Followup with a question asking the interviewee to provide a brief self-introduction about themselves, including their background and experience.
DO NOT interrupt the interviewee while they are providing their self-introduction.
You are ONLY to respond with affirmations like "tell me more", "uh-huh", "hmm", or "nice" when the interviewee is providing their self-introduction.
"""

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  if callback_context.state["phase"] != "introduction":
    callback_context.state["phase_start"] = time.time()
    callback_context.state["phase"] = "introduction"
    callback_context.state["interview_instructions"] = interviewer_instruction.format(
      interviewer_background=callback_context.state["interviewer_background"]
    )

############################### thought agent ###############################
NEXT_STEP_AGENT = "overview_judge"  

def criteria_met(met: bool, reason: str, tool_context: ToolContext) -> None:
  """
  Progress the conversation to the next phase.
  """
  if met:
    logging.info("Criteria met, proceeding to next phase.")
    # tool_context.state["phase"] = "overview"
    tool_context.actions.transfer_to_agent = NEXT_STEP_AGENT
    return
  
  logging.info(f"Criteria not met: {reason}")
  logging.info(f"timings: { time.time() - tool_context.state["phase_start"]} and {configs["durations"]["introduction"]}")
  if time.time() - tool_context.state["phase_start"] > configs["durations"]["introduction"]:
    logging.info("Introduction phase timed out, proceeding to next phase.")
    tool_context.actions.transfer_to_agent = NEXT_STEP_AGENT
    return
  
  tool_context.actions.skip_summarization = True

criteria_met_tool = FunctionTool(func=criteria_met)

_instruction = """You are an introduction judge.

You are responsible for determining whether the interviewee has provided a detailed self-introduction.

Here is the self-introduction:
[start_interviewee]
{phase_client_text}
[end_interviewee]

The self-introduction should be at least 30 words long and include the interviewee's background and experience.

If the interviewee's self-introduction meets these criteria, call the 'criteria_met_tool' with input 'True' and an empty reason string.
Otherwise, input 'False' to indicate that the self-introduction is insufficient and provide the reason.
"""


agent = LlmAgent(
  name="introduction_judge",
  description="Determine whether the interviewee has provided a detailed self-introduction.",
  model=configs["model"],
  instruction=_instruction,
  tools=[criteria_met_tool], 
  before_agent_callback=[before_agent_callback],
  include_contents='none',
  generate_content_config=types.GenerateContentConfig(
    temperature=0.0
  ),
)
