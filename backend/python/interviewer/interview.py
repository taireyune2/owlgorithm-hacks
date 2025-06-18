import logging
import traceback
import json
import time
import random
import asyncio
import base64
from typing import Optional, AsyncGenerator
from pydantic import BaseModel

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
from .thought import ThoughtAgentSystem
from .live import LiveAgentSystem
from . import socket


class InterviewRound:
  """
  Represents a single round of the interview.    
  """
  def __init__(
    self, 
    app_name: str,
    session_id: str, 
    interviewer_name: str,
    voice: str,
    session_service: InMemorySessionService
  ):
    self.app_name = app_name
    self.session_id = session_id
    self.interviewer_name = interviewer_name
    self.voice = voice

    self.thought = ThoughtAgentSystem(session_service=session_service)
    self.live = None

  async def start_session(self, resume: str, job_description: str) -> str:
    """
    Prepare the interview round by checking the inputs and creating the background info.
    """
    interviewer_background = await prepare_interview(
      app_name=self.app_name,
      session_id=self.session_id,
      interviewer_name=self.interviewer_name,
      resume=resume,
      job_description=job_description,
      session_service=self.thought.session_service,
    )

    await self.thought.start_session(
      app_name=self.app_name,
      session_id=self.session_id,
      interviewer_name=self.interviewer_name,
      resume=resume,
      job_description=job_description,
      interviewer_background=interviewer_background,
    )

  async def connect(self):
    """
    Initialize the live agent system.
    """
    self.live = LiveAgentSystem(
      app_name=self.app_name,
      session_id=self.session_id,
      get_instructions=self.thought.get_instructions,
    )
    await self.live.start_session(
      session_id=self.session_id, 
      interviewer_name=self.interviewer_name,
      voice=self.voice,
      background=self.thought.get_state()["interviewer_background"],
    )

  def close(self):
    """
    Close the interview round and clean up resources.
    """
    if self.thought:
      self.thought.close()
    if self.live:
      self.live.close()

  # async def process_live_response


  async def run(self, websocket: WebSocket) -> None:
    await websocket.accept()

    # Start tasks
    receive_and_process_responses_task = asyncio.create_task(
      socket.receive_and_process_responses(websocket, self.live.live_events)
    )
    client_to_agent_task = asyncio.create_task(socket.client_to_agent_messaging(
      websocket, 
      self.live.live_request_queue, 
      self.live.audio_queue
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



