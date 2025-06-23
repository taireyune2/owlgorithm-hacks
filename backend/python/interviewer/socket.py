"""
Socket communication for the interviewer agent to communicate with the client.
Using various events and Queues
"""

import logging
import json
import base64
import asyncio

from fastapi import WebSocket, WebSocketDisconnect
from google.genai import types
from google.adk.events import Event
from typing import Optional, AsyncGenerator, Callable, Awaitable

from fastapi import WebSocket, WebSocketDisconnect
from google.genai import types
from google.adk.events import Event
from google.adk.agents import LiveRequestQueue

SEND_SAMPLE_RATE = 16000

async def handle_live_events(
  live_events: AsyncGenerator[Event, None],
  websocket: WebSocket, 
  collect_client_txt: Callable[[str], Awaitable[None]],
  collect_agent_txt: Callable[[str], Awaitable[None]],
) -> None:
  """
  Handle the live agent's output events.
  Parse the events and send them to the client and/or collect them for further processing.
  """

  # Track agent's outputs between turn completion events
  agent_output_audio = asyncio.Queue()
  agent_output_text = asyncio.Queue()

  # Flag to track if we've seen an interruption in the current turn
  interrupted = False

  # We shouldn't make a new line if it's the beginning of our conversation
  beginning = True
  
  while True:
    async for event in live_events:

      # Check for interruption
      if event.interrupted and not interrupted:
        logging.info("🤐 INTERRUPTION DETECTED")
        interrupted =  True

      # Check for turn completion
      if event.turn_complete:
        if not interrupted:

          if not beginning:
            # Make a new line because the user has done speaking. It's the agent's speech
            await websocket.send_text(json.dumps({
              "status": "open",
              "signal": "turn_complete",
              "mime_type": "text/plain",
              "data": ""
            }))
          beginning = False
          
          # Send agent's text data
          while True:
            try:
              item = agent_output_text.get_nowait()
              agent_output_text.task_done() 
              message = {
                "status": "open",
                "role": "agent",
                "mime_type": "text/plain",
                "data": item
              }
              await websocket.send_text(json.dumps(message))
            except asyncio.QueueEmpty:
              break
          # Send agent's audio data
          while True:
            try:
              item = agent_output_audio.get_nowait()
              agent_output_audio.task_done()
              message = {
                "status": "open",
                "mime_type": "audio/pcm",
                "data": item
              }
              await websocket.send_text(json.dumps(message))
            except asyncio.QueueEmpty:
              break

          logging.info("✅ Gemini done talking")

          # Make a new line because the agent has done speaking. It will be the user's speech turn
          await websocket.send_text(json.dumps({
            "status": "open",
            "signal": "turn_complete",
            "mime_type": "text/plain",
            "data": ""
          }))
          # flag = " [turn complete] " if event.turn_complete else " [interrupted] "
          # await collect_client_txt(flag)
          # await collect_agent_txt(flag)
        interrupted = False
        continue

      # Read the types.Content and its first Part
      part: types.Part = (
        event.content and event.content.parts and event.content.parts[0]
      )

      if not part:
        continue

      # If it's audio, send Base64 encoded audio data. Handle audio content
      is_audio = part.inline_data and part.inline_data.mime_type.startswith("audio/pcm")
      if is_audio:
        audio_data = part.inline_data and part.inline_data.data
        if audio_data:
          await agent_output_audio.put(base64.b64encode(audio_data).decode("ascii"))

      # Process text content
      if part.text:
        # Check if this is user or model text based on content role
        if hasattr(event.content, "role") and event.content.role == "user":
          # We send user's text immediately because the user should see his text as the user speaks
          message = {
            "status": "open",
            "role": "user",
            "mime_type": "text/plain",
            "data": part.text
          }
          await websocket.send_text(json.dumps(message))
          await collect_client_txt(part.text)
          logging.info(f"[CLIENT TO AGENT]: text/plain: {part.text}")

        # We get streaming chunks with "partial=True" followed by a final consolidated
        # response with "partial=None" containing the complete text so we only process messages with "partial=True"
        if event.partial:
          await agent_output_text.put(part.text)
          await collect_agent_txt(part.text)
          # logging.info(f"[AGENT TO CLIENT]: text/plain: {message}")

async def client_to_agent_messaging(websocket, live_request_queue, audio_queue, consecutiveIdleCountAllowed):
  """Client to agent communication"""
  while True:
    # Wait up to PING_INTERVAL for client message
    message_json = await websocket.receive_text()
    message = json.loads(message_json)
    mime_type = message["mime_type"]
    data = message["data"]
    
    # Send the message to the agent
    if mime_type == "audio/pcm":
      decoded_data = base64.b64decode(data)
      # Send the audio data to Gemini through ADK's LiveRequestQueue
      live_request_queue.send_realtime(
          types.Blob(
              data=decoded_data,
              mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}",
          )
      )