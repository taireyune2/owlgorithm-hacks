import logging
import traceback
import json
import time
import random
import asyncio
import base64
from typing import Optional, AsyncGenerator

from fastapi import WebSocket, WebSocketDisconnect
from google.adk.sessions import InMemorySessionService, BaseSessionService, Session
from google.adk.runners import InMemoryRunner, Runner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
from google.adk.events import Event, EventActions
from google.adk.tools import ToolContext, FunctionTool


# from .agent import root_agent

from .preparer import prepare_interview
from .agent import TextAgentSystem
from .live import LiveAgentSystem
from . import socket

  # session_id: str
  # socket: WebSocket
  # latest_signal: float
  # session: Session
  # live_events: AsyncGenerator[Event, None]
  # live_request_queue: LiveRequestQueue
  # audio_queue: asyncio.Queue
  # self.audio_queue = asyncio.Queue()

class InterviewRound:
  
  """
  Represents a single round of the interview.    
  """
  def __init__(
    self, 
    app_name: str,
    session_id: str, 
    session_service: InMemorySessionService
  ):
    self.app_name = app_name
    self.session_id = session_id

    self.client_text_queue = asyncio.Queue()
    self.agent_text_queue = asyncio.Queue()

    self.text_agent_system = TextAgentSystem(
      app_name=app_name,
      session_service=session_service,
    )

  async def start_session(self, interviewer_name: str, resume: str, job_description: str) -> str:
    """
    Prepare the interview round by checking the inputs and creating the background info.
    """
    interviewer_background = await prepare_interview(
      app_name=self.app_name,
      session_id=self.session_id,
      interviewer_name=interviewer_name,
      resume=resume,
      job_description=job_description,
      session_service=self.text_agent_system.session_service,
    )

    await self.text_agent_system.start_session(
      session_id=self.session_id,
      interviewer_name=interviewer_name,
      resume=resume,
      job_description=job_description,
      interviewer_background=interviewer_background,
    )














  def _get_dynamic_instruction(self) -> str:
    """
    Generate dynamic instruction for the agent.

    Returns:
      str: Instruction for the agent.
    """
    instructions = [
      "Say you studied mathematics",
      "Say you graduated 2014",
      "Say you work at Google",
    ]
    current = instructions[self._index]
    logging.info(f"Dynamic instruction: {current}")
    return current

  def get_root_agent(self):
    instruction = """You are an interviewer named {interviewer_name}.

Please ALWAYS follow the instructions from 'get_instruction_tool'.

"""
    get_instruction_tool = FunctionTool(func=self._get_dynamic_instruction)
    return LlmAgent(
      name="interviewer",
      description="Converse with the user by following the instructions from 'get_instruction_tool'.",
      model="gemini-2.0-flash-exp",
      instruction=instruction,
      tools=[get_instruction_tool], 
      generate_content_config=types.GenerateContentConfig(
        temperature=2.0
      ),
      include_contents='none',
    )

  async def initialize_agent(self, resume: str, job_description: str) -> tuple[AsyncGenerator[Event, None], LiveRequestQueue]:
    """
    Start the interview round.
    """
    try:
      self.root_agent = self.get_root_agent()
      self.runner = InMemoryRunner(
        app_name=self.app_name,
        agent=self.root_agent,
      )

      # Create a Session
      self.session = await self.runner.session_service.create_session(
        app_name=self.app_name,
        user_id=self.session_id,  # Replace with actual user ID
        state={
          "interviewer_name": self.interviewer.name,
          "interviewer_background": self.interviewer.background,
          # "interviewee_name": "Mike",
          "resume": resume,
          "job_description": job_description,
          "phase": "greeting",
          "count": 0,
        }
      )
      self.live_request_queue = LiveRequestQueue()
      self.live_events = self.runner.run_live(
        session=self.session,
        live_request_queue=self.live_request_queue,
        run_config=self.interviewer.get_run_configs()
      )
      logging.info(f"Interview round {self.session_id} initialized with interviewer {self.interviewer.name}.")
    except Exception as e:
      logging.error(f"Unhandled error in initialize_agent: {e}")
      logging.error(traceback.format_exc())
      raise e

  def is_ready(self) -> bool:
    """
    Check if the interview round is ready to accept connections.
    """
    return self.live_events is not None
  
  async def broadcast_state(self, websocket: WebSocket) -> None:
    while True:
      actions_with_update = EventActions(
        state_delta={"count": (self.session.state["count"] + 1) % 3}
      )
      self._index = (self._index + 1) % 3
      system_event = Event(
        invocation_id="update_count",
        author="system", # Or 'agent', 'tool' etc.
        actions=actions_with_update,
        # content might be None or represent the action taken
      )
      await self.runner.session_service.append_event(self.session, system_event)
      logging.info(f"Broadcasting state: index={self._index} phase={self.session.state['phase']}, count={self.session.state['count']}")
      
      # await websocket.send_text(json.dumps(message))
      await asyncio.sleep(5)

  async def run(self, websocket: WebSocket) -> None:
    """
    Run the interview round with the given WebSocket connection.
    """
    await websocket.accept()

    # Start tasks
    receive_and_process_responses_task = asyncio.create_task(
      socket.receive_and_process_responses(websocket, self.live_events)
    )
    client_to_agent_task = asyncio.create_task(socket.client_to_agent_messaging(
      websocket, 
      self.live_request_queue, 
      self.audio_queue
    ))
    process_and_send_audio_task = asyncio.create_task(
      socket.process_and_send_audio(self.live_request_queue, self.audio_queue)
    )

    broadcast_state_task = asyncio.create_task(
      self.broadcast_state(websocket)
    )
    # Wait until the websocket is disconnected or an error occurs
    tasks = [
      client_to_agent_task, 
      process_and_send_audio_task, 
      receive_and_process_responses_task,
      broadcast_state_task,
    ]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    # Cancel any pending tasks immediately
    for task in pending:
      task.cancel()
      try:
        await task
      except asyncio.CancelledError:
        logging.info(f"✅ Cancelled task: {task.get_coro().__name__}")

    # Handle exceptions and cancellations for completed tasks
    for task in done:
      if task.cancelled():
        logging.info(f"⚠️ Task {task.get_coro().__name__} was cancelled")
      elif task.exception():
        exc = task.exception()
        errorCode = exc.code
        if errorCode == 1000:
          logging.info(f"✅ Session ended by user: {task.get_coro().__name__}")
        else:
          logging.error(f"❌ Unhandled exception in task {task.get_coro().__name__}: {exc}")
          tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
          logging.error(tb)
          raise exc

  def close(self):
    """
    Close the interview round and clean up resources.
    """
    if self.live_request_queue:
      self.live_request_queue.close()
    logging.info(f"Interview round {self.session_id} closed.")



