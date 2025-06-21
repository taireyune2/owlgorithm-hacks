from pydantic import BaseModel, Field
from typing import Optional
import random
import logging
import asyncio

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext

from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner
from google.genai import types

from common.configs import file

configs = file["agent"]["preparer"]

###################### Resume ###############################
class ResumeJudgement(BaseModel):
  is_resume: bool = Field(default=False, description="Indicates whether the user's input is a resume or not.")
  explanation: str = Field(default="", description="Brief explanation if the input is not a resume.")


_instruction = """You are a resume judge. 

Determine if the input text is a resume or not. 
If it is a resume, return true, otherwise return false with explanation.
Here is the input text:

[start_input]
{resume}
[end_input]

Respond ONLY in valid JSON format following this schema:
```json
{
  "is_resume": bool,
  "explanation": str (If false, brief explanation of why it is not a resume)"
}
```
"""

resume_judge = LlmAgent(
  name="resume_judge",
  model=configs["model"],
  description="Agent to judge whether the input text is a resume or not.",
  instruction=_instruction,
  output_key="resume_judgement",
  output_schema=ResumeJudgement,
  include_contents='none',
  disallow_transfer_to_parent=True,
  disallow_transfer_to_peers=True,
  generate_content_config=types.GenerateContentConfig(
    temperature=0.0
  ),
)

######################### Job Description ###############################

class JobDescriptionJudgement(BaseModel):
  is_job_description: bool = Field(default=False, description="Indicates whether the user's input is a job description or not.")
  explanation: str = Field(default="", description="Brief explanation if the input is not a job description.")

_instruction = """You are a job description judge.

Determine if the input text is a job description or not.
If it is a job description, return true, otherwise return false with explanation.
Here is the input text:

[start_input]
{job_description}
[end_input]

Respond ONLY in valid JSON format following this schema:
```json
{
  "is_job_description": bool,
  "explanation": str (If false, brief explanation of why it is not a job description)"
}
```
"""

job_description_judge = LlmAgent(
  name="job_description_judge",
  model=configs["model"],
  description="Agent to judge whether the input text is a job description or not.",
  instruction=_instruction,
  output_key="job_description_judgement",
  output_schema=JobDescriptionJudgement,
  include_contents='none',
  disallow_transfer_to_parent=True,
  disallow_transfer_to_peers=True,
  generate_content_config=types.GenerateContentConfig(
    temperature=0.0
  ),
)


######################### Interviewer Self Introduction ###############################
def check_inputs_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  """
  Callback to check if the inputs are valid resumes and job descriptions.
  """
  logging.info("callback called")
  resume_judgement = callback_context.state.get("resume_judgement")
  job_description_judgement = callback_context.state.get("job_description_judgement")
  # print(f"Resume judgement: {resume_judgement}")
  # print(f"Job description judgement: {job_description_judgement}")
  if resume_judgement.get("is_resume", False) and job_description_judgement.get("is_job_description", False):
    return None
  
  error_message = "Invalid inputs: "
  if not resume_judgement.get("is_resume", False):
    error_message += f"Resume check failed: {resume_judgement.get("explanation", "")}. "
  if not job_description_judgement.get("is_job_description", False):
    error_message += f"Job description check failed: {job_description_judgement.get("explanation", "")}."
  logging.info(f"User uploaded invalid background info: {error_message}")
  return types.Content(role="agent", parts=[types.Part(text=error_message)])


_instruction = """You are a person who is hiring.

You need to give a background about yourself to the candidate.
This is the job description you wrote:

{job_description}

Please write a brief background of yourself. 
This description should be clear and concise, befitting the PERSON WHO IS HIRING.
The description should be no more than 50 words. Please use fictional information where ever needed.
Respond only with your background. No need to greet or say your name.
"""

interviewer_agent = LlmAgent(
  name="self_introduction_agent",
  model=configs["model"],
  description="Agent to provide background information about the interviewer.",
  instruction=_instruction,
  include_contents='none',
  disallow_transfer_to_parent=True,
  disallow_transfer_to_peers=True,
  before_agent_callback=[check_inputs_callback],
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0,
  ),
)


################################# Control Flow ####################################

content_checker = ParallelAgent(
  name="content_checker",
  description="Parallel agent to check if the user's input is a resume and job description.",
  sub_agents=[
    resume_judge,
    job_description_judge,
  ],
)

preparation_agent = SequentialAgent(
  name="preparation_agent",
  description="Sequential agent to prepare the interview round by checking the inputs and creating the background info.",
  sub_agents=[
    content_checker,
    interviewer_agent
  ],
)


############################## Run ######################################
async def prepare_interview(
  app_name: str,
  session_id: str,
  interviewer_name: str,
  resume: str,
  job_description: str,
  session_service: InMemorySessionService,
) -> str:
  """
  Prepare the interview round by checking the inputs and creating the background info.
  """
  runner: Runner = Runner(
    app_name=app_name,
    agent=preparation_agent,
    session_service=session_service
  )
  session = await session_service.create_session(
    app_name=app_name,
    user_id=session_id,
    session_id=session_id,
    state={
      "interviewer_name": interviewer_name,
      "resume": resume,
      "job_description": job_description,
    }
  )

  results = []
  async for event in runner.run_async(
    user_id=session_id,
    session_id=session_id,
    new_message=types.Content(
      role="user",
      parts=[types.Part(text="")]
    )
  ):
    if event.is_final_response():
      results.append(event.content.parts[0].text)

  if not results:
    raise Exception("Agents failed to generate a proper response.")
  if results[-1].startswith("Invalid inputs: "):
    raise ValueError(results[-1])
  
  await runner.close()
  await session_service.delete_session(
    app_name=app_name, user_id=session_id, session_id=session_id
  )
  return results[-1]
