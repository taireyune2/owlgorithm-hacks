from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import json

import os
import json
import asyncio
import base64
import warnings

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
from google.adk.agents.run_config import RunConfig

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Request
from pydantic import BaseModel
from typing import Optional

from dummy_agent.agent import root_agent


APP_NAME = "ADK Streaming example"


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


async def agent_to_client_messaging(websocket, live_events):
    """Agent to client communication"""

    # Track user and model outputs between turn completion events
    input_texts = []
    output_texts = []

    while True:
        async for event in live_events:

            # If the turn complete or interrupted, send it
            if event.turn_complete or event.interrupted:
                message = {
                    "turn_complete": event.turn_complete,
                    "interrupted": event.interrupted,
                }
                await websocket.send_text(json.dumps(message))
                print(f"[AGENT TO CLIENT]: {message}")
                continue

            # Read the Content and its first Part
            part: Part = (
                event.content and event.content.parts and event.content.parts[0]
            )
            if not part:
                continue

            # If it's audio, send Base64 encoded audio data
            is_audio = part.inline_data and part.inline_data.mime_type.startswith("audio/pcm")
            if is_audio:
                audio_data = part.inline_data and part.inline_data.data
                if audio_data:
                    message = {
                        "mime_type": "audio/pcm",
                        "data": base64.b64encode(audio_data).decode("ascii")
                    }
                    await websocket.send_text(json.dumps(message))
                    print(f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes.")
                    continue

            # If it's text and a parial text, send it
            if part.text and event.partial:
                message = {
                    "mime_type": "text/plain",
                    "data": part.text
                }
                await websocket.send_text(json.dumps(message))
                print(f"[AGENT TO CLIENT]: text/plain: {message}")

async def client_to_agent_messaging(websocket, live_request_queue):
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
            live_request_queue.send_content(content=content)
            print(f"[CLIENT TO AGENT]: {data}")
        elif mime_type == "audio/pcm":
            # Send an audio data
            decoded_data = base64.b64decode(data)
            live_request_queue.send_realtime(Blob(data=decoded_data, mime_type=mime_type))
        else:
            raise ValueError(f"Mime type not supported: {mime_type}")





# from common import auth

router = APIRouter(
    prefix="",
)

########################## POJO #################################
# Upload resume endpoint
class Resume(BaseModel):
    email: str
    phone: Optional[str]
    rawText: str

class JobDescription(BaseModel):
    link: Optional[str]
    rawText: str

class UserInfo(BaseModel):
    session_id: int
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
async def upload_material(user_info: UserInfo):

    print(f"Session ID: {user_info.session_id}")
    print(f"Email: {user_info.resume.email}")
    print(f"Phone: {user_info.resume.phone}")
    print(f"Raw Text: {user_info.resume.rawText[:100]}...")  # Print first 100 characters
    print(f"Job Link: {user_info.job_description.link}")  # Print first 100 characters
    print(f"Description: {user_info.job_description.rawText[:100]}...")  # Print first 100 characters

    # Placeholder logic to handle the uploaded data
    return {"status": "success", "session_id": user_info.session_id}


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

        # Start tasks
        agent_to_client_task = asyncio.create_task(
            agent_to_client_messaging(websocket, live_events)
        )
        client_to_agent_task = asyncio.create_task(
            client_to_agent_messaging(websocket, live_request_queue)
        )

        # Wait until the websocket is disconnected or an error occurs
        tasks = [agent_to_client_task, client_to_agent_task]
        await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

        # Close LiveRequestQueue
        live_request_queue.close()

        # Disconnected
        print(f"Client #{user_id} disconnected")

    except WebSocketDisconnect:
        manager.disconnect(websocket)

