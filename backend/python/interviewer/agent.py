import logging
from typing_extensions import override
from typing import AsyncGenerator, Optional
import asyncio

from google.adk.agents import (
  BaseAgent, LlmAgent, SequentialAgent, ParallelAgent
)
from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner
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

############################ Run ######################################
class TextAgentSystem:
  """
  Handles the lifecycle of the text agent.
  """
  def __init__(self, app_name: str, session_service: InMemorySessionService):
    self.app_name = app_name
    self.session_service = session_service
    self.root_agent = root_agent
    self.runner = Runner(
      app_name=self.app_name,
      agent=self.root_agent,
      session_service=self.session_service
    )

  async def start_session(
    self, 
    session_id: str, 
    interviewer_name: str,   
    resume: str,
    job_description: str,
    interviewer_background: str,
  ) -> Session:
    """
    Prepare session.
    """
    self.session = await self.session_service.create_session(
      app_name=self.app_name,
      user_id=session_id,
      session_id=session_id,
      state={
        "interviewer_name": interviewer_name,
        "resume": resume,
        "job_description": job_description,
        "interviewer_background": interviewer_background,
        "interview_instructions": "",
      }
    )
    return self.session
  
  async def close(self) -> None:
    """
    Close the session.
    """
    await self.session_service.delete_session(self.session.id)
    await self.runner.close()

  async def run(self, role, message):
    """
    Run the agent with the given message.
    """
    async for event in self.runner.run_async(
      user_id=self.session.id,
      session_id=self.session.id,
      new_message=types.Content(
        role=role,
        parts=[types.Part(text=message)]
      )
    ):
      continue