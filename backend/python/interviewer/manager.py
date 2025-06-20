import logging
import asyncio
from typing import Optional, AsyncGenerator

from fastapi import WebSocket, WebSocketDisconnect
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.events import Event, EventActions

from .interview import InterviewRound

class InterviewManager:
  """
  Facilitate adding/removing interview rounds
  and managing their lifecycle.
  """
  def __init__(self, config: dict):
    self.interviews: dict[str, InterviewRound] = {}
    self.session_service = InMemorySessionService()
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
    
    interview = InterviewRound(
      configs=self.config,
      session_id=session_id,
    )
    await interview.start_thought_session(
      session_service=self.session_service, resume=resume, job_description=job_description
    )
    self.interviews[session_id] = interview

  async def connect(self, websocket: WebSocket, session_id: str, tries: int = 3):
    """
    Check if Interview Round is ready. Once ready, accept websocket connection.
    """
    interview_round = self.interviews.get(session_id, None)
    if interview_round:
      await interview_round.start_live_session()
      await interview_round.run(websocket)
    elif tries > 0:
      logging.info(f"Interview Round {session_id} is not ready. Retrying in 1 second with {tries} retries...")
      await asyncio.sleep(1)
      return await self.connect(websocket, session_id, tries - 1)
    else:
      logging.error(f"Interview Round {session_id} is not ready after retries. Disconnecting.")
      await self.disconnect(session_id)
      raise Exception(f"Interview Round {session_id} is not ready after retries.")

  async def disconnect(self, session_id: str):
    interview_round = self.interviews.get(session_id, None)
    if interview_round:
      await interview_round.close()
      del self.interviews[interview_round.session_id]
