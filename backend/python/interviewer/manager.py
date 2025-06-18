import logging
import traceback
import json
import time
import random
import asyncio
import base64
from typing import Optional, AsyncGenerator

from fastapi import WebSocket, WebSocketDisconnect
from google.adk.sessions import InMemorySessionService,
from google.adk.runners import InMemoryRunner, Runner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types
from google.adk.events import Event, EventActions
from google.adk.tools import ToolContext, FunctionTool


# from .agent import root_agent
from ....archive.agents.func_call_agent import get_step, root_agent
from .preparer import preparation_agent
from . import socket
from google.adk.agents import LlmAgent


class InterviewManager:
  """
  Facilitate adding/removing interview rounds
  and managing their lifecycle.
  """
  def __init__(self, config: dict):
    self.interviews: dict[str, InterviewRound] = {}
    self.session_service = InMemorySessionService()

    self.text_runner: Runner = Runner(
      app_name=config["name"] + "-text",
      agent=root_agent,
      session_service=self.session_service,
    )
    self.config = config
    






  async def initialize_interview(self, session_id: str, resume: str, job_description: str):
    """
    Prepare the interview round.
    Setup interviewer with background.
    Initialize agent.
    """
    if session_id in self.interviews:
      logging.warning(f"Session {session_id} already exists. Overwriting existing interview round.")
      self.disconnect(session_id)
    
    choice = random.choice(self.config["voices"]) 
    interviewer = Interviewer(
      self.config["name"], 
      choice["name"], 
      choice["voice"], 
      self.session_service
    )
    await interviewer.prep_background(session_id, resume, job_description)

    interview_round = InterviewRound(
      app_name=self.config["name"],
      session_id=session_id,
      interviewer=interviewer
    )
    self.interviews[session_id] = interview_round
    await interview_round.initialize_agent(resume, job_description)

  async def connect(self, websocket: WebSocket, session_id: str, tries: int = 3):
    """
    Check if Interview Round is ready. Once ready, accept websocket connection.
    """
    interview_round = self.interviews.get(session_id, None)
    if not interview_round or not interview_round.is_ready():
      if tries > 0:
        logging.info(f"Interview Round {session_id} is not ready. Retrying in 1 second with {tries} retries...")
        await asyncio.sleep(1)
        return await self.connect(websocket, session_id, tries - 1)
      else:
        logging.error(f"Interview Round {session_id} is not ready after retries. Disconnecting.")
        self.disconnect(session_id)
        raise WebSocketDisconnect(f"Interview Round {session_id} is not ready after retries.")
    
    return await interview_round.run(websocket)

  def disconnect(self, session_id: str):
    interview_round = self.interviews.get(session_id, None)
    if interview_round:
      interview_round.close()
      del self.interviews[interview_round.session_id]
