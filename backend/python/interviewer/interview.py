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
    configs: dict,
    session_id: str, 
    
  ):
    self.interviewer = random.choice(configs["voices"])
    self.configs = configs
    self.session_id = session_id
  
    self.thought = None
    self.live = None
    self.idle_socket_duration = 0

  async def start_thought_session(
    self, *,
    session_service: InMemorySessionService,
    resume: str, job_description: str
  ) -> None:
    """
    Prepare the interview round by checking the inputs and creating the background info.
    """
    interviewer_background = await prepare_interview(
      app_name=self.configs["name"],
      session_id=self.session_id,
      interviewer_name=self.interviewer["name"],
      resume=resume,
      job_description=job_description,
      session_service=session_service,
    )
    self.thought = ThoughtAgentSystem()
    await self.thought.start_session(
      session_service=session_service,
      app_name=self.configs["name"],
      session_id=self.session_id,
      interviewer_name=self.interviewer["name"],
      resume=resume,
      job_description=job_description,
      interviewer_background=interviewer_background,
      interview_questions=random.sample(
        self.configs["interview_questions"], self.configs["num_questions"]
      ),
    )

  async def start_live_session(self):
    """
    Initialize the live agent system.
    """
    self.live = LiveAgentSystem()
    state = await self.thought.get_state()
    await self.live.start_session(
      app_name=self.configs["name"],
      session_id=self.session_id, 
      interviewer_name=self.interviewer["name"],
      voice=self.interviewer["voice"],
      background=[state["interviewer_background"]],
      model=self.configs["live"]["model"],
      get_instructions=self.thought.get_instructions,
    )

  async def close(self):
    """
    Close the interview round and clean up resources.
    """
    if self.thought:
      await self.thought.close()
    if self.live:
      await self.live.close()

  async def run(self, websocket: WebSocket) -> None:
    # try:
    await websocket.accept()

    async with asyncio.TaskGroup() as tg:
      handle_live_events_task = tg.create_task(
        socket.handle_live_events(
          self.live.live_events, 
          websocket, 
          self.thought.put_client_message, 
          self.thought.put_agent_message
        )
      )
      handle_inbound_messages_task = tg.create_task(
        socket.client_to_agent_messaging(
          websocket, 
          self.live.live_request_queue,
          None, 3,
        )
      )
      update_thought_task = tg.create_task(self._update_thought(websocket))
      
    # except WebSocketDisconnect as e:
    #   logging.info(f"⚠️ WebSocket disconnected before tasks started for session {self.session_id}")
    #   raise e
    # except Exception as e:
    #   logging.error(f"⚠️ Unhandled error in run: {e}")
    #   logging.error(traceback.format_exc())
    #   raise e

  async def _update_thought(self, websocket: WebSocket) -> None:
    """
    Update the thought agent with new messages.
    """
    REFRESH_INTERVAL = self.configs["refresh_interval"]
    while True:
      await asyncio.sleep(REFRESH_INTERVAL)
      await self.thought.update()
      await self.thought.run()
      await self.close_idle_socket(websocket, 90)
      # TODO: push system message into the request queue

  async def close_idle_socket(self, websocket: WebSocket, max_idle_duration_allowed: int) -> None:
    
    state = await self.thought.get_state()
    immediate_client_message = state.get("immediate_client_text", "")
    if immediate_client_message and immediate_client_message.strip():
      self.idle_socket_duration = 0
    else:
      self.idle_socket_duration += 10

    if self.idle_socket_duration > 0 and self.idle_socket_duration < max_idle_duration_allowed and self.idle_socket_duration % 30 == 0:
      remaining = max_idle_duration_allowed - self.idle_socket_duration
      print(f"Socket remaining time is: {remaining} ")
      await websocket.send_text(json.dumps({
        "status": "open",
        "role": "system",
        "mime_type": "text/plain",
        "data": f"Socket will be closed in {remaining} seconds"
      }))
    # Close connection if exceeded max idle duration
    elif self.idle_socket_duration > max_idle_duration_allowed:
      await websocket.send_text(json.dumps({
        "status": "closed",
        "signal": "close_socket",
        "mime_type": "text/plain",
        "data": ""
      }))
      raise WebSocketDisconnect()

    

