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
  behavioral_questioner, 
  greeter, 
  introducer,
  overviewer, 
  closing_agent,
)

class InterviewerAgent(BaseAgent):
  """
  Agent that deterministically directs flow to the defined agents
  based on state using state machine pattern.
  This agent does not call the LLM, but routes requests to other agents
  based on predefined rules.
  """
  greeter: LlmAgent
  introducer: LlmAgent
  overviewer: LlmAgent
  behavioral_questioner: LlmAgent

  def __init__(
    self, 
    greeter: LlmAgent,
    introducer: LlmAgent,
    overviewer: LlmAgent,
    behavioral_questioner: LlmAgent,
    name: str = "interviewer",
  ):
    super().__init__(
      greeter=greeter,
      introducer=introducer,
      overviewer=overviewer,
      behavioral_questioner=behavioral_questioner,
      name=name,
      sub_agents=[
        greeter, 
        introducer, overviewer, behavioral_questioner,
      ],
      description="Route agents based on the interview phase.",
    )

  @override
  async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
    """
    Deterministic control flow for other interview agents
    """
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
        
  @override
  async def _run_live_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
    """
    Deterministic control flow for other interview agents
    """
    logging.info(f"Running live agent {self.name} with phase {ctx.session.state['phase']}")
    if ctx.session.state["phase"] == "greeting":
      async for event in self.greeter.run_live(ctx):
        yield event
    if ctx.session.state["phase"] == "introduction":
      async for event in self.introducer.run_live(ctx):
        yield event
    if ctx.session.state["phase"] == "overview":
      async for event in self.overviewer.run_live(ctx):
        yield event
    if ctx.session.state["phase"] == "behavioral_question":
      async for event in self.behavioral_questioner.run_live(ctx):
        yield event
    if ctx.end_invocation:
      return


thought_agent = InterviewerAgent(
  greeter.thought_agent,
  introducer.thought_agent,
  overviewer.thought_agent,
  behavioral_questioner.thought_agent,
  name="thought_agent"
)


live_agent = InterviewerAgent(
  greeter.live_agent,
  introducer.live_agent,
  overviewer.live_agent,
  behavioral_questioner.live_agent,
  name="live_agent"
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