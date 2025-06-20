import pytest 
import logging
import json
import os
from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from . import agent
from common import logger

TEST_FOLDER = "../tests/"

def setup():
  load_dotenv() 
  with open(os.path.join(TEST_FOLDER, "configs/agent-testing.json"), "r") as f:
    _configs = json.load(f)
    configs = _configs["agent"]
    logger.setup(_configs["logging"])

  session_service = InMemorySessionService()
  runner = Runner(
    agent=agent.thought_agent,
    app_name=configs["name"],
    session_service=session_service,
  )
  return configs, session_service, runner


async def test_introduction():
  configs, session_service, runner = setup()
  with open(os.path.join(TEST_FOLDER, "inputs/intro/expected.json"), "r") as f:
    data = json.load(f)

  user_id = "123"
  session_id = user_id

  session = await session_service.create_session(
    app_name=configs["name"],
    user_id=user_id,
    session_id=session_id,
    state=data["initial_state"],
  )

  results = []
  messages = ["", *data["inputs"]]
  for message in messages:
    async for event in runner.run_async(
      user_id=user_id,
      session_id=session_id,
      new_message=types.Content(
        role="user",
        parts=[types.Part(text=message)]
      )
    ):
      if event.is_final_response():
        results.append(event.content.parts[0].text)

  for user, agent in zip(messages, results):
    logging.info(f"User: {user}")
    logging.info(f"Agent: {agent}")

async def test_closing():
  configs, session_service, runner = setup()
  with open(os.path.join(TEST_FOLDER, "inputs/closing/expected.json"), "r") as f:
    data = json.load(f)
  
  user_id = "123"
  session_id = user_id  
  session = await session_service.create_session(
    app_name=configs["name"],
    user_id=user_id,
    session_id=session_id,
    state=data["initial_state"],
  )
  
  results = []
  messages = ["", *data["inputs"]]
  for message in messages:
    async for event in runner.run_async(
      user_id=user_id,
      session_id=session_id,
      new_message=types.Content(
        role="user",
        parts=[types.Part(text=message)]
      )
    ):
      if event.is_final_response():
        results.append(event.content.parts[0].text)
  
  for user, agent in zip(messages, results):
    logging.info(f"User: {user}")
    logging.info(f"Agent: {agent}")

async def test_core():
  configs, session_service, runner = setup()
  with open(os.path.join(TEST_FOLDER, "inputs/core/expected.json"), "r") as f:
    data = json.load(f)

  user_id = "123"
  session_id = user_id

  session = await session_service.create_session(
    app_name=configs["name"],
    user_id=user_id,
    session_id=session_id,
    state=data["initial_state"],
  )

  results = []
  messages = ["", *data["inputs"]]
  for message in messages:
    async for event in runner.run_async(
      user_id=user_id,
      session_id=session_id,
      new_message=types.Content(
        role="user",
        parts=[types.Part(text=message)]
      )
    ):
      if event.is_final_response():
        results.append(event.content.parts[0].text)

  for user, agent in zip(messages, results):
    logging.info(f"User: {user}")
    logging.info(f"Agent: {agent}")

