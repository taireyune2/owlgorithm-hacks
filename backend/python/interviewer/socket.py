"""
Manage interview socket connections for a single fastAPI instance
"""

import time
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import logging


class AudioWebSocket(WebSocket):
  session_id: str
  latest_signal: float

  def assign_session(self, session_id: str):
    self.session_id = session_id
    self.latest_signal = time.time()

  async def receive_text(self) -> str:
    result = await super().receive_text()
    self.latest_signal = time.time()
    return result
  
  async def send_text(self, data: str) -> None:
    await super().send_text(data)
    self.latest_signal = time.time()


class AudioConnectionManager:
  """
  Facilitate adding/removing WebSocket connections
  and managing their lifecycle.
  """
  def __init__(self):
    self.connections: list[AudioWebSocket] = []

  async def connect(self, websocket: WebSocket, session_id: str):
    await websocket.accept()
    websocket.__class__ = AudioWebSocket
    websocket.assign_session(session_id)
    self.connections.append(websocket)
    logging.info(f"New connection established for session {session_id}")

  def disconnect(self, websocket: AudioWebSocket):
    self.connections.remove(websocket)
    try:
      websocket.close()
    except WebSocketDisconnect:
      pass

  def cleanup(self, timeout: int = 30):
    current_time = time.time()
    connections: list[AudioWebSocket] = []

    for conn in self.connections:
      if current_time - conn.latest_signal > timeout:
        logging.info(f"Removing inactive connection for session {conn.session_id}")
        self.disconnect(conn)
      else:
        connections.append(conn)
    self.connections = connections
