import asyncio
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts
from dotenv import load_dotenv

from .interviewer.agent import root_agent
from .interviewer.agent import router_agent





async def demo():
    load_dotenv()

    APP_NAME = "text_demo"
    USER_ID = "user_123"
    SESSION_ID = "session_123"

    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state = {
            "default": "default",
            "content": "empty",
        }
    )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    message = types.Content(
        role="user", parts=[types.Part(text="Hello, who are you?")]
    )

    for event in runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                print("Final response:", event.content.parts[0].text)

    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    for key, value in session.state.items():
        print(f"{key}: {value}")


asyncio.run(demo())