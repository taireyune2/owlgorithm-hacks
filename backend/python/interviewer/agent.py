import logging
from typing_extensions import override
from typing import AsyncGenerator, Optional
import asyncio

from google.adk.agents import (
  BaseAgent, LlmAgent, 
)

from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.events import Event
from google.genai import types

from .subagents import (
  greeter, 
  introducer,
  overviewer,
  behavioral_questioner, 
  followup_questioner,
  closing_responder,
)

class InterviewerAgent(BaseAgent):
  """
  Agent that deterministically directs flow to the defined agents
  based on state using state machine pattern.
  This agent does not call the LLM, but routes requests to other agents
  based on predefined rules.
  """
  greeter: BaseAgent
  introducer: BaseAgent
  overviewer: BaseAgent
  behavioral_questioner: BaseAgent
  followup_questioner: BaseAgent
  closing_responder: BaseAgent

  def __init__(
    self, 
    greeter: BaseAgent,
    introducer: BaseAgent,
    overviewer: BaseAgent,
    behavioral_questioner: BaseAgent,
    followup_questioner: BaseAgent,
    closing_responder: BaseAgent,
    name: str = "interviewer",
  ):
    super().__init__(
      greeter=greeter,
      introducer=introducer,
      overviewer=overviewer,
      behavioral_questioner=behavioral_questioner,
      followup_questioner=followup_questioner,
      closing_responder=closing_responder,
      name=name,
      sub_agents=[
        greeter, introducer, overviewer,
        behavioral_questioner, followup_questioner,
        closing_responder
      ],
      description="Route agents based on the interview phase.",
    )

  @override
  async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
    """
    Deterministic control flow for other interview agents
    """
    # while True:
    if ctx.session.state["phase"] == "greeting":
      async for event in self.greeter.run_async(ctx):
        yield event
    if ctx.session.state["phase"] == "introduction":
      async for event in self.introducer.run_async(ctx):
        yield event
    if ctx.session.state["phase"] == "overview":
      async for event in self.overviewer.run_async(ctx):
        yield event
    if ctx.session.state["phase"] == "behavioral_question":
      async for event in self.behavioral_questioner.run_async(ctx):
        yield event
    if ctx.session.state["phase"] == "followup_question":
      async for event in self.followup_questioner.run_async(ctx):
        yield event
    if ctx.session.state["phase"] == "closing_response":
      async for event in self.closing_responder.run_async(ctx):
        yield event


root_agent = InterviewerAgent(
  greeter.agent,
  introducer.agent,
  overviewer.agent,
  behavioral_questioner.agent,
  followup_questioner.agent,
  closing_responder.agent,
  name="thought_agent"
)


# ############################## dummy agent for instructions ##############################
# _instruction = """
# You are the head of the talent team.

# You are responsible for writing the instructions for the interview process.

# Please only respond with the instruction.

# Tell the interviewer to {}
# """
# root_agent = LlmAgent(
#   name="Instruction Writer",
#   description="Writes instructions for the interview process.",
#   model="gemini-2.0-flash-exp",
#   instruction=_instruction,
#   output_key="interview_instructions",
# )
