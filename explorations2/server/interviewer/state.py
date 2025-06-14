from google.adk.sessions import InMemorySessionService, BaseSessionService, Session
from google.adk.runners import Runner
from google.genai import types
import logging
import json

from .agent import root_agent

class InterviewSingleton:
  def __init__(self, configs: dict):
    """
    
    """
    self.session_service: BaseSessionService = InMemorySessionService()
    self.runner: Runner = Runner(
      agent=root_agent,
      app_name=configs["name"],
      session_service=self.session_service,
    )
    self.configs = configs

  def initialize_state(self) -> dict:
    """
    state schema
    {
      "bahavioral_question": "",  # str
      "user_response": "", # str
      "followup_question": "", # str
      "question_judgement": {
        "is_appropriate": False,
        "reason": ""  # Optional, str
      }, 
      "on_topic_judgement": {
        "on_topic": False,
        "reason": ""  # Optional, str
      },
    }
    """
    return {
      "behavioral_question": "Describe a situation where you had a conflict with a teammate. How did you handle it?",  
      "user_response": "",
      "followup_question": "",
      "question_judgement": {},
      "on_topic_judgement": {},
    }

  async def get_state(self, user_id: str, session_id: str) -> dict:
    session = await self.get_session(user_id, session_id)
    return session.state
  
  async def get_session(self, user_id: str, session_id: str) -> Session:
    session =  await self.session_service.get_session(
      app_name=self.configs["name"],
      user_id=user_id,
      session_id=session_id
    )
    return session
  
  async def create_session(self, user_id: str, session_id: str) -> Session:
    session = await self.session_service.create_session(
      app_name=self.configs["name"],
      user_id=user_id,
      session_id=session_id,
      state=self.initialize_state()
    )
    return session
  
  async def proceed(self, user_id: str, session_id: str, message: str) -> types.Content:
    # session = await self.get_session(user_id, session_id)
    # logging.info(
    #   "pre session state: %s", 
    #   json.dumps(session.state, indent=2)
    # )    
    try:
      async for event in self.runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(
          role="user",
          parts=[types.Part(text=message)]
        )
      ):
        session = await self.get_session(user_id, session_id)
        # if event.is_final_response():
        #   if event.content and event.content.parts:
        #     return event.content.parts[0].text
        ### retrieve user response from state
        is_appropriate = session.state.get("question_judgement", {}).get("is_appropriate", False)
        is_ontopic = session.state.get("on_topic_judgement", {}).get("on_topic", False)
        # logging.info(event)
        # logging.info(
        #   "mid session state: %s", 
        #   json.dumps(session.state, indent=2)
        # )
        if is_appropriate and is_ontopic:
          return types.Content(
            role="agent", 
            parts=[types.Part(text=session.state["followup_question"])]
          )

      return types.Content(role="system", parts=[types.Part(text="Moving on.")])

    except Exception as e:
      print(f"Error during interview process: {e}")
      return types.Content(role="system", parts=[types.Part(text="An error occurred during the interview process.")])