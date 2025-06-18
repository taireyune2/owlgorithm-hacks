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
  introduction_listener, 
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
  introduction_listener: LlmAgent
  overviewer: LlmAgent
  behavioral_questioner: LlmAgent
  closer: LlmAgent

  def __init__(
    self, 
    greeter: LlmAgent,
    introducer: LlmAgent,
    introduction_listener: LlmAgent,
    overviewer: LlmAgent,
    behavioral_questioner: LlmAgent,
    closer: LlmAgent,
    name: str = "interviewer",
  ):
    super().__init__(
      greeter=greeter,
      introducer=introducer,
      introduction_listener=introduction_listener,
      overviewer=overviewer,
      behavioral_questioner=behavioral_questioner,
      closer=closer,
      name=name,
      sub_agents=[greeter, introducer, introduction_listener, overviewer, behavioral_questioner, closer],
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
    if ctx.session.state["phase"] == "introduction_response":
      async for event in self.introduction_listener.run_async(ctx):
        yield event
    if ctx.session.state["phase"] == "overview":
      async for event in self.overviewer.run_async(ctx):
        yield event
    if ctx.session.state["phase"] == "behavioral_question":
      async for event in self.behavioral_questioner.run_async(ctx):
        yield event
    if ctx.session.state["phase"] == "closing":
      async for event in self.closer.run_async(ctx):
        yield event

        
  @override
  async def _run_live_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
    """
    Deterministic control flow for other interview agents
    """
    if ctx.session.state["phase"] == "greeting":
      async for event in self.greeter.run_live(ctx):
        yield event
    if ctx.session.state["phase"] == "introduction":
      async for event in self.introducer.run_live(ctx):
        yield event
    if ctx.session.state["phase"] == "introduction_response":
      async for event in self.introduction_listener.run_live(ctx):
        yield event
    if ctx.session.state["phase"] == "overview":
      async for event in self.overviewer.run_live(ctx):
        yield event
    if ctx.session.state["phase"] == "behavioral_question":
      async for event in self.behavioral_questioner.run_live(ctx):
        yield event
    if ctx.session.state["phase"] == "closing":
      async for event in self.closer.run_async(ctx):
        yield event
    if ctx.end_invocation:
      return

root_agent = InterviewerAgent(
  greeter.agent,
  introducer.agent,
  introduction_listener.agent,
  overviewer.agent,
  behavioral_questioner.agent,
  closing_agent.agent,
  name="root_agent"
)
