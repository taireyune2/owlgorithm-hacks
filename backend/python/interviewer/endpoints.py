from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import json

import os
import json
import asyncio
import base64
import warnings
import logging
from pathlib import Path
from dotenv import load_dotenv
from google.genai import types
from google.genai.types import (
  Part,
  Content,
  Blob,
)

from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Request
from pydantic import BaseModel
from typing import Optional

from dummy_agent.agent import root_agent
# from .agent import root_agent

APP_NAME = "ADK Streaming example"
VOICE_NAME = "Puck"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def start_agent_session(user_id, is_audio=False):
  """Starts an agent session"""

  # Create a Runner
  runner = InMemoryRunner(
    app_name=APP_NAME,
    agent=root_agent,
  )

  # Create a Session
  session = await runner.session_service.create_session(
    app_name=APP_NAME,
    user_id=user_id,  # Replace with actual user ID
  )

  # Set response modality
  modality = "AUDIO" if is_audio else "TEXT"
  run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=VOICE_NAME
            )
        )
    ),
    response_modalities=[modality],
    output_audio_transcription=types.AudioTranscriptionConfig(),
    input_audio_transcription=types.AudioTranscriptionConfig())

  # Create a LiveRequestQueue for this session
  live_request_queue = LiveRequestQueue()

  # Start agent session
  live_events = runner.run_live(
    session=session,
    live_request_queue=live_request_queue,
    run_config=run_config,
  )
  return live_events, live_request_queue


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
        logger.info("🤐 INTERRUPTION DETECTED")
        await websocket.send_text(json.dumps({
          "mime_type": "text/plain",
          "data": "Response interrupted by user input"
        }))
        interrupted =  True

      # Check for turn completion
      if event.turn_complete:
        if not interrupted:
          logger.info("✅ Gemini done talking")
          message = {
            "mime_type": "text/plain",
            "data": "Response done (turn complete) by Gemini"
          }
          await websocket.send_text(json.dumps(message))

        if input_texts:
          # Get unique texts to prevent duplication
          unique_texts = list(dict.fromkeys(input_texts))
          logger.info(f"Input transcription: {' '.join(unique_texts)}")

        if output_texts:
          # Get unique texts to prevent duplication
          unique_texts = list(dict.fromkeys(output_texts))
          logger.info(f"Output transcription: {' '.join(unique_texts)}")

        input_texts = []
        output_texts = []
        interrupted = False

      # Read the Content and its first Part
      part: Part = (
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
            "mime_type": "audio/pcm",
            "data": base64.b64encode(audio_data).decode("ascii")
          }
          await websocket.send_text(json.dumps(message))
          print(f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes.")

      # Process text content
      if part.text:
        # Check if this is user or model text based on content role
        if hasattr(event.content, "role") and event.content.role == "user":
          # User text shouldn't be sent to the client
          input_texts.append(part.text)
          message = {
            "mime_type": "text/plain",
            "data": part.text
          }
          await websocket.send_text(json.dumps(message))
          print(f"[CLIENT TO AGENT]: text/plain: {part.text}")
        else:
          # From the logs, we can see the duplicated text issue happens because
          # we get streaming chunks with "partial=True" followed by a final consolidated
          # response with "partial=None" containing the complete text

          # Check in the event string for the partial flag
          # Only process messages with "partial=True"
          if event.partial:
            output_texts.append(part.text)
            message = {
              "mime_type": "text/plain",
              "data": part.text
            }
            await websocket.send_text(json.dumps(message))
            print(f"[AGENT TO CLIENT]: text/plain: {message}")

async def client_to_agent_messaging(websocket, live_request_queue, audio_queue):
  """Client to agent communication"""
  while True:
    # Decode JSON message
    message_json = await websocket.receive_text()
    message = json.loads(message_json)
    mime_type = message["mime_type"]
    data = message["data"]

    # Send the message to the agent
    if mime_type == "text/plain":
      # Send a text message
      content = Content(role="user", parts=[Part.from_text(text=data)])
      await audio_queue.put(content)
      print(f"[CLIENT TO AGENT]: {data}")
    elif mime_type == "audio/pcm":
      # Send an audio data
      decoded_data = base64.b64decode(data)
      await audio_queue.put(decoded_data)
      #live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
    else:
      raise ValueError(f"Mime type not supported: {mime_type}")

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


router = APIRouter(
  prefix="",
)

########################## POJO #################################
# Upload resume endpoint
class Resume(BaseModel):
    email: Optional[str]
    phone: Optional[str]
    rawText: str

class JobDescription(BaseModel):
  link: Optional[str]
  rawText: str

class UserInfo(BaseModel):
    session_id: str
    resume: Resume
    job_description: JobDescription


class ConnectionManager:
  def __init__(self):
    self.active_connections: list[WebSocket] = []

  async def connect(self, websocket: WebSocket):
    await websocket.accept()
    self.active_connections.append(websocket)

  def disconnect(self, websocket: WebSocket):
    self.active_connections.remove(websocket)

  async def send_personal_message(self, message: str, websocket: WebSocket):
    await websocket.send_text(message)

  async def broadcast(self, message: str):
    for connection in self.active_connections:
      await connection.send_text(message)


manager = ConnectionManager()


@router.post("/upload")
async def upload_material(request: UserInfo):
    session_id = request.session_id
    resume = request.resume,
    jobDescription = request.job_description
    print(f"Session ID: {session_id}")
    print(f"Email: {request.resume.email}")
    print(f"Phone: {request.resume.phone}")
    print(f"Raw Text: {request.resume.rawText[:100]}...")  # Print first 100 characters
    print(f"Job Link: {request.job_description.link}")  # Print first 100 characters
    print(f"Description: {request.job_description.rawText[:100]}...")  # Print first 100 characters

    # Placeholder logic to handle the uploaded data
    return {"status": "success", "session_id": request.session_id}


@router.post("/")
async def interview_session(response: str):
# async def interview_session(response: str, token: str = Depends(auth.validate_token)):
  """
  Text mock interview session.

  For agent debug.
  """
  pass


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, is_audio: str):
  """Client websocket endpoint"""
  
  # Wait for client connection
  await manager.connect(websocket)
  print(f"Client #{user_id} connected, audio mode: {is_audio}")

  try:
    # Start agent session
    user_id_str = str(user_id)
    live_events, live_request_queue = await start_agent_session(user_id_str, is_audio == "true")

    audio_queue = asyncio.Queue()

    # Start tasks
    receive_and_process_responses_task = asyncio.create_task(
      receive_and_process_responses(websocket, live_events)
    )
    client_to_agent_task = asyncio.create_task(
      client_to_agent_messaging(websocket, live_request_queue, audio_queue)
    )
    process_and_send_audio_task = asyncio.create_task(
      process_and_send_audio(live_request_queue, audio_queue)
    )

    # Wait until the websocket is disconnected or an error occurs
    tasks = [client_to_agent_task, process_and_send_audio_task, receive_and_process_responses_task]
    await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    # Close LiveRequestQueue
    live_request_queue.close()

    # Disconnected
    print(f"Client #{user_id} disconnected")

  except WebSocketDisconnect:
    manager.disconnect(websocket)

