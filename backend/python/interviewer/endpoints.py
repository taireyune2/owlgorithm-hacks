import os
import asyncio
import json
import logging
import traceback
from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Optional
from starlette.requests import Request

from .manager import InterviewManager
from common import configs
from service import limiter


manager = InterviewManager(config=configs.file["agent"])

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
@limiter.limit("3/minute")  # Allows only 3 requests per minute
async def upload_material(request: Request, user_info: UserInfo):
  """
  Endpoint to upload user resume and job description.
  If the materials are valid, the interview session will start.
  If the materials are invalid, the invalid reason will be returned in the error details.
  """
  try:
    await manager.initialize_interview(user_info.session_id, user_info.resume.rawText, user_info.job_description.rawText)
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


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
  """Client websocket endpoint"""
  try:
    await manager.connect(websocket, session_id)
  except WebSocketDisconnect:
    logging.info(f"WebSocket disconnected for {session_id}")
  except Exception as e:
    logging.error(f"Error in WebSocket connection for session {session_id}: {e}")
    logging.error(traceback.format_exc())
  finally:
    await manager.disconnect(session_id)
  logging.info(f"Interview {session_id} has been cleaned up.")

