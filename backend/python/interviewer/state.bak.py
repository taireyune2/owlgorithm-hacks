from google.adk.sessions import InMemorySessionService, BaseSessionService, Session
from google.adk.runners import Runner
from google.genai import types
import logging
import json
from fastapi import WebSocket, WebSocketDisconnect
import time

from .agent import root_agent


class InterviewRound:
    """
    Represents a single round of the interview.    
    """
    user_id: str
    session_id: str
    resume: str
    job_description: str
    socket: WebSocket
    latest_signal: float


class InterviewManager:
  """
  Facilitate adding/removing interview rounds
  and managing their lifecycle.
  """
  def __init__(self):
    self.interviews: dict[str, InterviewRound] = {}
    self.session_service: BaseSessionService = InMemorySessionService()
    self.runner: Runner = Runner(
      agent=root_agent,
      session_service=self.session_service,
    )
