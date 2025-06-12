import os
import asyncio
import json
import logging
import traceback
from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional

from . import state, socket
from common import configs

async def process_audio(websocket: socket.AudioWebSocket):
  pass

manager = state.InterviewManager(config=configs.file["agent"])

##################### FastAPI endpoints ######################
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


router = APIRouter(
  prefix="",
)


@router.post("/upload")
async def upload_material(request: UserInfo):
  """
  Endpoint to upload user resume and job description.
  """
  # Here you can process the uploaded data, e.g., save it to a database or file system
  print(f"Received session_id: {request.session_id}")
  print(f"Received email: {request.resume.email}")
  print(f"Received phone: {request.resume.phone}")
  print(f"Received rawText: {request.resume.rawText}")
  print(f"Received job description link: {request.job_description.link}")
  print(f"Received job description rawText: {request.job_description.rawText}")

  return {"status": "success", "message": "Materials uploaded successfully."}


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

  session_id = str(user_id)
  try:
    interview = await manager.connect(websocket, session_id)
    await interview.run()
  except WebSocketDisconnect:
    pass
  except Exception as e:
    logging.error(f"Error in WebSocket connection for session {session_id}: {e}")
    logging.error(traceback.format_exc())
  finally:
    manager.disconnect(websocket)
    logging.info(f"WebSocket connection closed for session {session_id}")


  