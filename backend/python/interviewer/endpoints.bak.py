from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import json

import os
import json
import asyncio
import base64

from google.genai import types
from google.genai.types import (
  Part,
  Content,
  Blob,
)

from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.events import Event

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Request
from pydantic import BaseModel
from typing import Optional

# from dummy_agent.agent import root_agent
from .agent import root_agent

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
    state={
      "interviewer_name": "Alex",
      "interviewer_background": "Alex Lee is an Engineering Manager leading the Gemini API platform team at Google, responsible for designing, building, and scaling developer-facing interfaces that allow seamless integration with Google\u2019s next-generation multi-modal LLMs. With over 12 years of experience in distributed systems and developer platforms, Alex combines deep technical expertise with a strong focus on user empathy and product vision.\n\nBefore joining the Gemini team, she managed the API Gateway and Identity Services group within Google Cloud, where she led efforts to improve service reliability and security for internal and external APIs. Her leadership played a key role in unifying authentication strategies across various AI services.\n\nIn her current role, Alex\u2019s team owns the full lifecycle of the Gemini APIs \u2014 from model invocation and token management to content safety, observability, and developer tooling. She partners closely with product managers, researchers, and cloud infra teams to ensure Gemini\u2019s capabilities are accessible, secure, and performant for developers across diverse domains, including search, education, healthcare, and creative tools.\n\nAlex holds a B.S. in Computer Science from Carnegie Mellon University and is passionate about mentoring women in engineering and scaling high-performing, mission-driven teams.\n\nSpecialties:\n\t\u2022\tAPI design & management for ML platforms\n\t\u2022\tScalable service architecture\n\t\u2022\tDeveloper experience (DX)\n\t\u2022\tCross-functional leadership\n\t\u2022\tPrivacy & safety for AI interfaces\n\t\u2022\tHybrid inference pipeline optimization",
      "interviewee_name": "Mike",
      "resume": "# Micheal Li\n\n**Email:** micheal.li@example.com  \n**Phone:** (123) 456-7890  \n**Location:** San Francisco, CA  \n**GitHub:** [github.com/michaelli](https://github.com/michaelli)  \n**LinkedIn:** [linkedin.com/in/michaelli](https://linkedin.com/in/michaelli)\n\n---\n\n## \ud83e\uddd1\u200d\ud83d\udcbb Summary\n\nMotivated junior software engineer with hands-on experience building scalable backend services using Java and AWS. Strong understanding of REST APIs, microservices architecture, and CI/CD pipelines. Eager to contribute to impactful projects and grow within a collaborative engineering team.\n\n---\n\n## \ud83d\udee0\ufe0f Technical Skills\n\n- **Languages:** Java, Python, SQL  \n- **Backend:** Spring Boot, REST APIs, JUnit  \n- **Cloud:** AWS (EC2, S3, Lambda, RDS)  \n- **DevOps:** Git, Docker, Jenkins, GitHub Actions  \n- **Databases:** MySQL, PostgreSQL, DynamoDB  \n- **Tools:** IntelliJ, Postman, Maven, VS Code\n\n---\n\n## \ud83d\udcbc Experience\n\n### Backend Engineering Intern  \n**Acme Tech Solutions \u2013 San Jose, CA**  \n*Jan 2024 \u2013 May 2024*\n\n- Developed and deployed RESTful APIs using Spring Boot and Java to support customer account management features.\n- Integrated AWS services (S3, RDS, Lambda) for secure file storage and backend processing.\n- Wrote unit and integration tests using JUnit, increasing backend code coverage by 35%.\n- Collaborated with senior engineers in Agile sprints and contributed to code reviews and design discussions.\n\n---\n\n## \ud83e\uddea Projects\n\n### Cloud File Upload Service  \nA secure and scalable file upload platform using AWS.\n\n- Implemented backend service in Java with Spring Boot.\n- Used **AWS S3** for file storage and **AWS Lambda** for asynchronous processing.\n- Managed deployments with **GitHub Actions** and **Docker** containers.\n\n### Student Course Registration API  \nA RESTful API for managing course registrations in a mock university system.\n\n- Built using Spring Boot, Java, and MySQL.\n- Supported CRUD operations for students and courses with validation and error handling.\n- Wrote automated tests to ensure API reliability and performance.\n\n---\n\n## \ud83c\udf93 Education\n\n**B.S. in Computer Science**  \nUniversity of California, Davis  \n*Graduated: Dec 2023*\n\n- Relevant Coursework: Data Structures, Algorithms, Cloud Computing, Software Engineering\n- Member of the ACM Student Chapter\n\n---\n\n## \ud83d\udcdc Certifications\n\n- AWS Certified Cloud Practitioner (2024)\n- Java Programming Nanodegree \u2013 Udacity (2023)\n\n---\n\n## \ud83c\udf31 Interests\n\nOpen source contributions, backend architecture, cloud infrastructure, hiking",
      "job_description": "About the Role\n\nWe are looking for a skilled and motivated Backend Engineer to join our AI Platform team to build and scale production-ready APIs powered by Gemini, Google\u2019s state-of-the-art multimodal models. In this role, you will design, develop, and optimize API services that make AI capabilities accessible, secure, and performant for downstream applications.\n\nYou\u2019ll work alongside machine learning engineers, frontend developers, and product managers to bring intelligent features to life, with a strong emphasis on reliability, observability, and scalability.\n\n\u2e3b\n\nResponsibilities\n\t\u2022\tDesign and implement scalable REST and/or gRPC APIs for Gemini-powered features.\n\t\u2022\tWork closely with ML teams to productionize Gemini model calls (e.g., prompt templating, streaming output, retries).\n\t\u2022\tBuild and manage asynchronous job pipelines and caching layers to handle long-running or expensive model inference tasks.\n\t\u2022\tSecure APIs with proper authentication/authorization (OAuth2, JWT, API keys).\n\t\u2022\tWrite integration and unit tests to ensure reliability and correctness.\n\t\u2022\tMonitor and improve performance using observability tools (e.g., OpenTelemetry, Prometheus, Grafana).\n\t\u2022\tCollaborate cross-functionally to define API interfaces and service SLAs.\n\t\u2022\tEnsure the APIs are documented, versioned, and easy to consume.\n\n\u2e3b\n\nMinimum Qualifications\n\t\u2022\t3+ years of experience building backend services in Python, Go, Java, or similar.\n\t\u2022\tProficiency in designing and maintaining RESTful APIs and/or gRPC services.\n\t\u2022\tExperience with containerized environments (Docker, Kubernetes, ECS).\n\t\u2022\tFamiliarity with cloud infrastructure (GCP, AWS, or Azure).\n\t\u2022\tStrong understanding of API security best practices and performance tuning.\n\t\u2022\tComfort working with large-scale data or model outputs (e.g., token streaming, pagination, rate limits).\n\n\u2e3b\n\nPreferred Qualifications\n\t\u2022\tExperience integrating with large language models (LLMs) or generative AI APIs (Gemini, OpenAI, Claude).\n\t\u2022\tExposure to vector stores, embedding pipelines, or RAG systems.\n\t\u2022\tFamiliarity with API gateways (e.g., Kong, Apigee) and traffic management.\n\t\u2022\tKnowledge of FastAPI, Flask, or equivalent modern Python frameworks.\n\t\u2022\tContributions to open-source AI or API tooling.",
      "phase": "greeting"
    }
  )

  # Set response modality
  modality = "AUDIO" if is_audio else "TEXT"
  run_config = RunConfig(
    # response_modalities=["AUDIO", "TEXT"],
    response_modalities=[modality],
    output_audio_transcription=types.AudioTranscriptionConfig(),
    input_audio_transcription=types.AudioTranscriptionConfig()
  )

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

      if event.content and event.content.parts:
        for part in event.content.parts:
          # Process audio content
          if hasattr(part, "inline_data") and part.inline_data:
            # Process text content
            if hasattr(part, "text") and part.text:
              # Check if this is user or model text based on content role
              if hasattr(event.content, "role") and event.content.role == "user":
                # User text shouldn't be sent to the client
                print(f"[AGENT TO CLIENT]: User text part: {part.text}")
                input_texts.append(part.text)

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

