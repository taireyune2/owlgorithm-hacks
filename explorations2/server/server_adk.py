import asyncio
import json
import base64

# Import Google ADK components
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner, InMemoryRunner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Import common components
from common import (
  BaseWebSocketServer,
  logger,
  VOICE_NAME,
  SEND_SAMPLE_RATE,
  root_agent,
)


class ADKWebSocketServer(BaseWebSocketServer):
  """WebSocket server implementation using Google ADK."""

  def __init__(self, host="0.0.0.0", port=8765):
    super().__init__(host, port)

    # Initialize ADK components
    self.agent = root_agent

    # Create session service
    self.session_service = InMemorySessionService()

  async def process_audio(self, websocket, client_id):
    # Store reference to client
    self.active_clients[client_id] = websocket

    # # Create session for this client
    # session = self.session_service.create_session(
    #   app_name="audio_assistant",
    #   user_id=f"user_{client_id}",
    #   session_id=f"session_{client_id}",
    # )

    # # Create runner
    # runner = Runner(
    #   app_name="audio_assistant",
    #   agent=self.agent,
    #   session_service=self.session_service,
    # )

    runner = InMemoryRunner(
      app_name="audio_assistant",
      agent=self.agent,
    )

    session = await runner.session_service.create_session(
      app_name="audio_assistant",
      user_id=f"user_{client_id}",
      session_id=f"session_{client_id}",
      state={
        "interviewer_name": "Alex",
        "interviewer_background": "Alex Lee is an Engineering Manager leading the Gemini API platform team at Google, responsible for designing, building, and scaling developer-facing interfaces that allow seamless integration with Google\u2019s next-generation multi-modal LLMs. With over 12 years of experience in distributed systems and developer platforms, Alex combines deep technical expertise with a strong focus on user empathy and product vision.\n\nBefore joining the Gemini team, she managed the API Gateway and Identity Services group within Google Cloud, where she led efforts to improve service reliability and security for internal and external APIs. Her leadership played a key role in unifying authentication strategies across various AI services.\n\nIn her current role, Alex\u2019s team owns the full lifecycle of the Gemini APIs \u2014 from model invocation and token management to content safety, observability, and developer tooling. She partners closely with product managers, researchers, and cloud infra teams to ensure Gemini\u2019s capabilities are accessible, secure, and performant for developers across diverse domains, including search, education, healthcare, and creative tools.\n\nAlex holds a B.S. in Computer Science from Carnegie Mellon University and is passionate about mentoring women in engineering and scaling high-performing, mission-driven teams.\n\nSpecialties:\n\t\u2022\tAPI design & management for ML platforms\n\t\u2022\tScalable service architecture\n\t\u2022\tDeveloper experience (DX)\n\t\u2022\tCross-functional leadership\n\t\u2022\tPrivacy & safety for AI interfaces\n\t\u2022\tHybrid inference pipeline optimization",
        "interviewee_name": "Mike",
        "resume": "# Micheal Li\n\n**Email:** micheal.li@example.com  \n**Phone:** (123) 456-7890  \n**Location:** San Francisco, CA  \n**GitHub:** [github.com/michaelli](https://github.com/michaelli)  \n**LinkedIn:** [linkedin.com/in/michaelli](https://linkedin.com/in/michaelli)\n\n---\n\n## \ud83e\uddd1\u200d\ud83d\udcbb Summary\n\nMotivated junior software engineer with hands-on experience building scalable backend services using Java and AWS. Strong understanding of REST APIs, microservices architecture, and CI/CD pipelines. Eager to contribute to impactful projects and grow within a collaborative engineering team.\n\n---\n\n## \ud83d\udee0\ufe0f Technical Skills\n\n- **Languages:** Java, Python, SQL  \n- **Backend:** Spring Boot, REST APIs, JUnit  \n- **Cloud:** AWS (EC2, S3, Lambda, RDS)  \n- **DevOps:** Git, Docker, Jenkins, GitHub Actions  \n- **Databases:** MySQL, PostgreSQL, DynamoDB  \n- **Tools:** IntelliJ, Postman, Maven, VS Code\n\n---\n\n## \ud83d\udcbc Experience\n\n### Backend Engineering Intern  \n**Acme Tech Solutions \u2013 San Jose, CA**  \n*Jan 2024 \u2013 May 2024*\n\n- Developed and deployed RESTful APIs using Spring Boot and Java to support customer account management features.\n- Integrated AWS services (S3, RDS, Lambda) for secure file storage and backend processing.\n- Wrote unit and integration tests using JUnit, increasing backend code coverage by 35%.\n- Collaborated with senior engineers in Agile sprints and contributed to code reviews and design discussions.\n\n---\n\n## \ud83e\uddea Projects\n\n### Cloud File Upload Service  \nA secure and scalable file upload platform using AWS.\n\n- Implemented backend service in Java with Spring Boot.\n- Used **AWS S3** for file storage and **AWS Lambda** for asynchronous processing.\n- Managed deployments with **GitHub Actions** and **Docker** containers.\n\n### Student Course Registration API  \nA RESTful API for managing course registrations in a mock university system.\n\n- Built using Spring Boot, Java, and MySQL.\n- Supported CRUD operations for students and courses with validation and error handling.\n- Wrote automated tests to ensure API reliability and performance.\n\n---\n\n## \ud83c\udf93 Education\n\n**B.S. in Computer Science**  \nUniversity of California, Davis  \n*Graduated: Dec 2023*\n\n- Relevant Coursework: Data Structures, Algorithms, Cloud Computing, Software Engineering\n- Member of the ACM Student Chapter\n\n---\n\n## \ud83d\udcdc Certifications\n\n- AWS Certified Cloud Practitioner (2024)\n- Java Programming Nanodegree \u2013 Udacity (2023)\n\n---\n\n## \ud83c\udf31 Interests\n\nOpen source contributions, backend architecture, cloud infrastructure, hiking",
        "job_description": "About the Role\n\nWe are looking for a skilled and motivated Backend Engineer to join our AI Platform team to build and scale production-ready APIs powered by Gemini, Google\u2019s state-of-the-art multimodal models. In this role, you will design, develop, and optimize API services that make AI capabilities accessible, secure, and performant for downstream applications.\n\nYou\u2019ll work alongside machine learning engineers, frontend developers, and product managers to bring intelligent features to life, with a strong emphasis on reliability, observability, and scalability.\n\n\u2e3b\n\nResponsibilities\n\t\u2022\tDesign and implement scalable REST and/or gRPC APIs for Gemini-powered features.\n\t\u2022\tWork closely with ML teams to productionize Gemini model calls (e.g., prompt templating, streaming output, retries).\n\t\u2022\tBuild and manage asynchronous job pipelines and caching layers to handle long-running or expensive model inference tasks.\n\t\u2022\tSecure APIs with proper authentication/authorization (OAuth2, JWT, API keys).\n\t\u2022\tWrite integration and unit tests to ensure reliability and correctness.\n\t\u2022\tMonitor and improve performance using observability tools (e.g., OpenTelemetry, Prometheus, Grafana).\n\t\u2022\tCollaborate cross-functionally to define API interfaces and service SLAs.\n\t\u2022\tEnsure the APIs are documented, versioned, and easy to consume.\n\n\u2e3b\n\nMinimum Qualifications\n\t\u2022\t3+ years of experience building backend services in Python, Go, Java, or similar.\n\t\u2022\tProficiency in designing and maintaining RESTful APIs and/or gRPC services.\n\t\u2022\tExperience with containerized environments (Docker, Kubernetes, ECS).\n\t\u2022\tFamiliarity with cloud infrastructure (GCP, AWS, or Azure).\n\t\u2022\tStrong understanding of API security best practices and performance tuning.\n\t\u2022\tComfort working with large-scale data or model outputs (e.g., token streaming, pagination, rate limits).\n\n\u2e3b\n\nPreferred Qualifications\n\t\u2022\tExperience integrating with large language models (LLMs) or generative AI APIs (Gemini, OpenAI, Claude).\n\t\u2022\tExposure to vector stores, embedding pipelines, or RAG systems.\n\t\u2022\tFamiliarity with API gateways (e.g., Kong, Apigee) and traffic management.\n\t\u2022\tKnowledge of FastAPI, Flask, or equivalent modern Python frameworks.\n\t\u2022\tContributions to open-source AI or API tooling.",
        "phase": "greeting"
      },
    )

    # Create live request queue
    live_request_queue = LiveRequestQueue()

    # Create run config with audio settings
    run_config = RunConfig(
      streaming_mode=StreamingMode.BIDI,
      speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
          prebuilt_voice_config=types.PrebuiltVoiceConfig(
            voice_name=VOICE_NAME
          )
        )
      ),
      response_modalities=["AUDIO"],
      output_audio_transcription=types.AudioTranscriptionConfig(),
      input_audio_transcription=types.AudioTranscriptionConfig(),
    )

    # Queue for audio data from the client
    audio_queue = asyncio.Queue()

    async with asyncio.TaskGroup() as tg:
      # Task to process incoming WebSocket messages
      async def handle_websocket_messages():
        async for message in websocket:
          try:
            data = json.loads(message)
            if data.get("type") == "audio":
              # Decode base64 audio data
              audio_bytes = base64.b64decode(data.get("data", ""))
              # Put audio in queue for processing
              await audio_queue.put(audio_bytes)
            elif data.get("type") == "end":
              # Client is done sending audio for this turn
              logger.info("Received end signal from client")
            elif data.get("type") == "text":
              # Handle text messages (not implemented in this simple version)
              logger.info(f"Received text: {data.get('data')}")
          except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
          except Exception as e:
            logger.error(f"Error processing message: {e}")

      # Task to process and send audio to Gemini
      async def process_and_send_audio():
        while True:
          data = await audio_queue.get()

          # Send the audio data to Gemini through ADK's LiveRequestQueue
          live_request_queue.send_realtime(
            types.Blob(
              data=data,
              mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}",
            )
          )

          audio_queue.task_done()

      # Task to receive and process responses
      async def receive_and_process_responses():
        # Track user and model outputs between turn completion events
        input_texts = []
        output_texts = []

        # Flag to track if we've seen an interruption in the current turn
        interrupted = False

        # Process responses from the agent
        async for event in runner.run_live(
          # user_id=f"user_{client_id}",
          # session_id=f"session_{client_id}",
          session=session,
          live_request_queue=live_request_queue,
          run_config=run_config,
        ):

          # Check for turn completion or interruption using string matching
          # This is a fallback approach until a proper API exists
          event_str = str(event)
          #print()

          # Handle audio content
          if event.content and event.content.parts:
            for part in event.content.parts:
              # Process audio content
              if hasattr(part, "inline_data") and part.inline_data:
                b64_audio = base64.b64encode(part.inline_data.data).decode("utf-8")
                await websocket.send(json.dumps({"type": "audio", "data": b64_audio}))

              # Process text content
              if hasattr(part, "text") and part.text:
                # Check if this is user or model text based on content role
                if hasattr(event.content, "role") and event.content.role == "user":
                  # User text shouldn't be sent to the client
                  input_texts.append(part.text)
                  # logger.info(f"User input: {part.text}")
                else:
                  # From the logs, we can see the duplicated text issue happens because
                  # we get streaming chunks with "partial=True" followed by a final consolidated
                  # response with "partial=None" containing the complete text

                  # Check in the event string for the partial flag
                  # Only process messages with "partial=True"
                  if "partial=True" in event_str:
                    await websocket.send(json.dumps({"type": "text", "data": part.text}))
                    output_texts.append(part.text)
                    # logger.info(f"User output: {part.text}")
                  # Skip messages with "partial=None" to avoid duplication

          # Check for interruption
          if event.interrupted  and not interrupted:
            logger.info("🤐 INTERRUPTION DETECTED")
            await websocket.send(json.dumps({
              "type": "interrupted",
              "data": "Response interrupted by user input"
            }))
            interrupted = True

          # Check for turn completion
          if event.turn_complete:
            # Only send turn_complete if there was no interruption
            if not interrupted:
              logger.info("✅ Gemini done talking")
              await websocket.send(json.dumps({"type": "turn_complete"}))

            # Log collected transcriptions for debugging
            if input_texts:
              # Get unique texts to prevent duplication
              unique_texts = list(dict.fromkeys(input_texts))
              logger.info(f"Input transcription: {' '.join(unique_texts)}")

            if output_texts:
              # Get unique texts to prevent duplication
              unique_texts = list(dict.fromkeys(output_texts))
              logger.info(f"Output transcription: {' '.join(unique_texts)}")

            # Reset for next turn
            input_texts = []
            output_texts = []
            interrupted = False

      # Start all tasks
      tg.create_task(handle_websocket_messages())
      tg.create_task(process_and_send_audio())
      tg.create_task(receive_and_process_responses())


async def main():
  """Main function to start the server"""
  server = ADKWebSocketServer()
  await server.start()


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    logger.info("Exiting application via KeyboardInterrupt...")
  except Exception as e:
    logger.error(f"Unhandled exception in main: {e}")
    import traceback
    traceback.print_exc()
