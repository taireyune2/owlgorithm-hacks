from google.adk.agents import LlmAgent, BaseAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time
from . import configs

############################## live agent instructions ##############################
interviewer_instruction = """It is the end of the interview.
In this phase, you are responsible for providing a self-introduction to the interviewee and then asking them to provide a self-introduction.
You are responsible for closing the interview and providing a warm, professional farewell.
Thank the interviewee for their time and interest.
Let them know that you will reach out to them for the next steps in the hiring process.
"""

def closing(ctx: ToolContext) -> Optional[types.Content]:
  ctx.state["phase"] = "closing"
  ctx.state["interview_instructions"] = interviewer_instruction
