"""
Socket communication for the interviewer agent to communicate with the client.
Using various events and Queues
"""

import logging
import traceback
import json
import base64
import asyncio
from sqlite3 import Blob
from typing import Optional, AsyncGenerator, Callable, Awaitable

from fastapi import WebSocket, WebSocketDisconnect
from google.genai import types
from google.adk.events import Event
from google.adk.agents import LiveRequestQueue


async def handle_live_events(
  live_events: AsyncGenerator[Event, None],
  websocket: WebSocket, 
  collect_client_txt: Callable[[str], Awaitable[None]],
  collection_agent_txt: Callable[[str], Awaitable[None]],
) -> None:
  """
  Handle the live agent's output events.
  Parse the events and send them to the client and/or collect them for further processing.
  """
  # try:
  async for event in live_events:
    # If the turn complete or interrupted, send it
    if event.turn_complete or event.interrupted:
      message = {
        "turn_complete": event.turn_complete,
        "interrupted": event.interrupted,
      }
      await websocket.send_text(json.dumps(message))
      # logging.info(f"[AGENT TO CLIENT]: {message}")
      continue

    # Read the Content and its first Part
    part: types.Part = (
      event.content and event.content.parts and event.content.parts[0]
    )
    if not part:
      continue

    # If it's audio, send Base64 encoded audio data
    is_audio = part.inline_data and part.inline_data.mime_type.startswith("audio/pcm")
    if hasattr(part, "inline_data") and is_audio:
      audio_data = part.inline_data and part.inline_data.data
      if audio_data:
        message = {
          "mime_type": "audio/pcm",
          "data": base64.b64encode(audio_data).decode("ascii")
        }
        await websocket.send_text(json.dumps(message))
        # logging.info(f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes.")

    # If it's text and a parial text, send it
    if hasattr(part, "text") and part.text:
      if hasattr(event.content, "role") and event.content.role == "user":
        message = {
          "mime_type": "text/plain",
          "data": part.text
        }
        await websocket.send_text(json.dumps(message))
        await collect_client_txt(part.text)
        # logging.info(f"[AGENT TO CLIENT]: text/plain: {message}")
      if event.partial:
        message = {
          "mime_type": "text/plain",
          "data": part.text
        }
        await websocket.send_text(json.dumps(message))
        await collection_agent_txt(part.text)
        # logging.info(f"[AGENT TO CLIENT]: text/plain: {message}")

  # except WebSocketDisconnect as e:
  #   logging.info("WebSocket disconnected")
  #   raise e
  # except Exception as e:
  #   logging.error(traceback.format_exc())
  #   raise e


async def handle_inbound_messages(websocket: WebSocket, live_request_queue: LiveRequestQueue) -> None:
  """Client to agent communication"""
  # try:
  while True:
    message_json = await websocket.receive_text()
    message = json.loads(message_json)
    data = message.get("data")
    live_request_queue.send_realtime(
      types.Blob(data=base64.b64decode(data), mime_type="audio/pcm")
    )
  # except WebSocketDisconnect as e:
  #     logging.info("WebSocket disconnected")
  #     raise e
  # except Exception as e:
  #     logging.error(traceback.format_exc())
  #     raise e