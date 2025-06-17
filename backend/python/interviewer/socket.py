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
from typing import Optional, AsyncGenerator


async def receive_and_process_responses(websocket, live_events):
  """Agent to client communication"""

  # Track user and model outputs between turn completion events
  input_texts = []
  output_texts = []

  # Flag to track if we've seen an interruption in the current turn
  interrupted = False

  while True:
    async for event in live_events:

      # Check for interruption
      if event.interrupted:
        logging.info("🤐 INTERRUPTION DETECTED")
        await websocket.send_text(json.dumps({
          "status": "open",
          "signal": "interrupted",
          "mime_type": "text/plain",
          "data": "Response interrupted by user input"
        }))
        interrupted =  True

      # Check for turn completion
      if event.turn_complete:
        if not interrupted:
          logging.info("✅ Gemini done talking")
          await websocket.send_text(json.dumps({
            "status": "open",
            "signal": "turn_complete",
            "mime_type": "text/plain",
            "data": "Response completed by Gemini"
          }))

        if input_texts:
          # Get unique texts to prevent duplication
          unique_texts = list(dict.fromkeys(input_texts))
          logging.info(f"Input transcription: {' '.join(unique_texts)}")

        if output_texts:
          # Get unique texts to prevent duplication
          unique_texts = list(dict.fromkeys(output_texts))
          logging.info(f"Output transcription: {' '.join(unique_texts)}")

        input_texts = []
        output_texts = []
        interrupted = False

      # Read the types.Content and its first Part
      part: types.Part = (
        event.content and event.content.parts and event.content.parts[0]
      )

      if not part:
        continue

      # If it's audio, send Base64 encoded audio data. Handle audio content
      is_audio = part.inline_data and part.inline_data.mime_type.startswith("audio/pcm")
      if hasattr(part, "inline_data") and is_audio:
        audio_data = part.inline_data and part.inline_data.data
        if audio_data:
          message = {
            "status": "open",
            "signal":  None,
            "mime_type": "audio/pcm",
            "data": base64.b64encode(audio_data).decode("ascii")
          }
          await websocket.send_text(json.dumps(message))
          # print(f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes.")

      # Process text content
      if part.text:
        # Check if this is user or model text based on content role
        if hasattr(event.content, "role") and event.content.role == "user":
          # User text shouldn't be sent to the client
          input_texts.append(part.text)
          message = {
            "status": "open",
            "signal": None,
            "mime_type": "text/plain",
            "data": part.text
          }
          await websocket.send_text(json.dumps(message))
          # print(f"[CLIENT TO AGENT]: text/plain: {part.text}")
        else:
          # From the logs, we can see the duplicated text issue happens because
          # we get streaming chunks with "partial=True" followed by a final consolidated
          # response with "partial=None" containing the complete text

          # Check in the event string for the partial flag
          # Only process messages with "partial=True"
          if event.partial:
            output_texts.append(part.text)
            message = {
              "status": "open",
              "signal": None,
              "mime_type": "text/plain",
              "data": part.text
            }
            await websocket.send_text(json.dumps(message))
            # print(f"[AGENT TO CLIENT]: text/plain: {message}")


async def client_to_agent_messaging(websocket, live_request_queue, audio_queue):
  """Client to agent communication"""
  try:
    while True:
      # Decode JSON message
      idle_time = 0
      IDLE_TIMEOUT_SECONDS = 30
      PING_INTERVAL = 10
      try:
        # Wait up to PING_INTERVAL for client message
        message_json = await asyncio.wait_for(websocket.receive_text(), timeout=PING_INTERVAL)
        message = json.loads(message_json)
        mime_type = message["mime_type"]
        data = message["data"]
        
        # Send the message to the agent
        if mime_type == "text/plain":
          # Send a text message
          content = types.Content(role="user", parts=[types.Part.from_text(text=data)])
          await audio_queue.put(content)
          # print(f"[CLIENT TO AGENT]: {data}")
        elif mime_type == "audio/pcm":
          # Send an audio data
          decoded_data = base64.b64decode(data)
          await audio_queue.put(decoded_data)
        else:
          raise ValueError(f"Mime type not supported: {mime_type}")
        
        idle_time = 0  # Reset idle time if message received
      except asyncio.TimeoutError:
        idle_time += PING_INTERVAL
        if idle_time >= IDLE_TIMEOUT_SECONDS:
          raise asyncio.TimeoutError 
        else:
          await websocket.send_text(json.dumps({
            "signal": "waiting",
            "mime_type": "text/plain",
            "data": "Agent is waiting for you to respond"
          }))
  except WebSocketDisconnect as webSocketDisconnect:
    raise webSocketDisconnect
  except Exception as e:
    raise e

async def process_and_send_audio(live_request_queue, audio_queue):
  while True:
    SEND_SAMPLE_RATE = 16000
    decoded_data = await audio_queue.get()

    # Send the audio data to Gemini through ADK's LiveRequestQueue
    live_request_queue.send_realtime(
        types.Blob(
            data=decoded_data,
            mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}",
        )
    )
    audio_queue.task_done()
