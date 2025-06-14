import os
import asyncio
import json
import logging
import traceback
from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect, HTTPException
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
  If the materials are valid, the interview session will start.
  If the materials are invalid, the invalid reason will be returned in the error details.
  """
  try:
    await manager.prep_background(request.session_id, request.resume.rawText, request.job_description.rawText)
    return {"status": "success", "message": "Materials uploaded successfully."}
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    logging.error(f"Error uploading materials: {e}")
    raise HTTPException(status_code=500, detail="Internal server error while uploading materials.")


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
    await interview.start_session()
  except WebSocketDisconnect:
    pass
  except Exception as e:
    logging.error(f"Error in WebSocket connection for session {session_id}: {e}")
    logging.error(traceback.format_exc())
  finally:
    manager.disconnect(websocket)
    logging.info(f"WebSocket connection closed for session {session_id}")


  