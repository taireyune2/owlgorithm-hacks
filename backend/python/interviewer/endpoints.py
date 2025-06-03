from fastapi import APIRouter, WebSocket, Depends


# from common import auth

router = APIRouter(
    prefix="/interview",
)



@router.post("/")
async def interview_session(response: str):
# async def interview_session(response: str, token: str = Depends(auth.validate_token)):
    """
    Text mock interview session.

    For agent debug.
    """
    pass


@router.post("/upload")
async def upload_material(placeholder: str):
# async def upload_material(placeholder: str, token: str = Depends(auth.validate_token)):
    """
    Allow user to upload relavent material about the interview such
    as resume, job description, and target company.
    """
    pass


@router.websocket("/{user_id}")
async def interview_session(websocket: WebSocket, user_id: int):
# async def interview_session(websocket: WebSocket, user_id: int, token: str = Depends(auth.validate_token)):
    """
    Audio Mock interview session
    """
    pass

