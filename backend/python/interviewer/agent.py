import logging
from typing_extensions import override
from typing import AsyncGenerator, Optional

from google.adk.agents import (
  BaseAgent, LlmAgent, SequentialAgent, ParallelAgent
)
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.events import Event
from google.genai import types

from .subagents import  behavioral_questioner, greeter, introducer, overviewer


class InterviewerAgent(BaseAgent):
  """
  Agent that deterministically directs flow to the defined agents
  based on state using state machine pattern.
  This agent does not call the LLM, but routes requests to other agents
  based on predefined rules.
  """
  introducer: LlmAgent
  greeter: LlmAgent
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
      sub_agents=[greeter, introducer, overviewer, behavioral_questioner  ],
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



root_agent = InterviewerAgent(
  greeter.agent,
  introducer.agent,
  overviewer.agent,
  behavioral_questioner.agent,
  name="root_agent"
)