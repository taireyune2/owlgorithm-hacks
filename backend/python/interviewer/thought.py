import logging
from typing_extensions import override
from typing import AsyncGenerator, Optional
import asyncio
import json
import time

from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner
from google.adk.events import Event, EventActions
from google.genai import types

from .agent import root_agent
# from .subagents.overviewer import interviewer_instruction
from .subagents.greeter import interviewer_instruction

############################ Run ######################################
class ThoughtQueue:
  """
  A simple queue to hold thought messages.
  """
  def __init__(self):
    self.agent_queue: list[str] = []
    self.client_queue: list[str] = []
    self._lock = asyncio.Lock()

  async def put_client_message(self, message: str) -> None:
    async with self._lock:
      self.client_queue.append(message)

  async def put_agent_message(self, message: str) -> None:
    async with self._lock:
      self.agent_queue.append(message)

  async def read(self) -> tuple[str, str]:
    """
    Read and return the concatenated messages.
    Clear the queues after reading.

    Returns:
      tuple[str, str]: A tuple containing the client message and agent message.
    """
    async with self._lock:
      agent_message = "".join(self.agent_queue)
      client_message = "".join(self.client_queue)
      self.agent_queue.clear()
      self.client_queue.clear()
    return client_message, agent_message


class ThoughtAgentSystem:
  """
  Handles the lifecycle of the thought agent.
  """
  def __init__(self):
    self.session_service: InMemorySessionService = None
    self.runner: Optional[Runner] = None
    self.session_id: Optional[str] = None
    self.session: Optional[Session] = None
    self.thought_queue = ThoughtQueue()

  async def start_session(
    self, *,
    session_service: InMemorySessionService,
    app_name: str,
    session_id: str, 
    interviewer_name: str,   
    resume: str,
    job_description: str,
    interviewer_background: str,
    interview_questions: list[str],
  ) -> Session:
    """
    Prepare session.
    """
    self.session_service = session_service
    self.session_id = session_id
    self.runner = Runner(
      app_name=app_name,
      agent=root_agent,
      session_service=self.session_service
    )
    self.session = await self.session_service.create_session(
      app_name=app_name,
      user_id=session_id,
      session_id=session_id,
      state={
        "interviewer_name": interviewer_name,
        "resume": resume,
        "job_description": job_description,
        "interviewer_background": interviewer_background,
        "phase": "greeting",
        # "phase": "overview",
        "interview_instructions": interviewer_instruction,
        "immediate_agent_text": "",
        "immediate_client_text": "",
        "phase_agent_text": "",
        "phase_client_text": "",
        "phase_start": time.time(),
        "interview_questions": interview_questions,
        "question_index": 0,
        "question": "",
        "followup_questions": [],
        "working_followup_question": "",
        "off_topic": 0,
      }
    )
    return self.session
  
  async def close(self) -> None:
    """
    Close the session.
    """
    await self.session_service.delete_session(
      app_name=self.session.app_name,
      user_id=self.session.id,
      session_id=self.session.id
    )
    await self.runner.close()

  async def run(self):
    """
    Run the agent with the given message.
    """
    async for event in self.runner.run_async(
      user_id=self.session_id,
      session_id=self.session_id,
      new_message=types.Content(
        role="user",
        parts=[types.Part(text="")]
      )
    ):
      # logging.info(event.model_dump_json(indent=2))
      if event.is_final_response():
        return
  
  async def update(self) -> None:
    """
    Update the agent internal state with new conversation data.
    """
    client_message, agent_message = await self.thought_queue.read()
    state = await self.get_state()
    printable = {k: state[k] for k in state if k not in [
      "interviewer_name", "interviewer_background", "resume", "interview_instructions", "job_description"
    ]}
    logging.info(f"current state:\n{json.dumps(printable, indent=2)}")
    state_delta = {
      "immediate_agent_text": agent_message,
      "immediate_client_text": client_message,
      "phase_agent_text": state["phase_agent_text"] + agent_message,
      "phase_client_text": state["phase_client_text"] + client_message,
    }
    system_event = Event(
      invocation_id="conversation_update",
      author="thought_agent",
      actions=EventActions(state_delta=state_delta),
    )
    await self.runner.session_service.append_event(self.session, system_event)
  
  async def get_instructions(self) -> str:
    """
    Get the instructions for the interviewer from session state.

    Returns:
      str: Instructions for the interviewer.
    """
    session = await self.session_service.get_session(
      app_name=self.session.app_name,
      user_id=self.session_id,
      session_id=self.session_id
    )
    logging.info(f"Interview_instructions: {session.state['interview_instructions']}")
    return session.state["interview_instructions"]

  async def get_state(self) -> dict:
    """
    Obtain the current phase of the interview from session state.

    Returns:
      dict: Current state of the interview.
    """
    session = await self.session_service.get_session(
      app_name=self.session.app_name,
      user_id=self.session_id,
      session_id=self.session_id
    )
    return session.state.copy()
  
  async def put_client_message(self, message: str) -> None:
    """
    Put a message from the client into the queue.
    
    Args:
      message (str): Message from the client.
    """
    await self.thought_queue.put_client_message(message)

  async def put_agent_message(self, message: str) -> None:
    """
    Put a message from the agent into the queue.

    Args:
      message (str): Message from the agent.
    """
    await self.thought_queue.put_agent_message(message)