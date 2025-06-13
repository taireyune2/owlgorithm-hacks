from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional
import random
import logging

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
  model="gemini-2.0-flash-exp",
  description="Agent to judge whether the input text is a resume or not.",
  instruction=_instruction,
  output_key="resume_judgement",
  output_schema=ResumeJudgement,
  include_contents='none',
  disallow_transfer_to_parent=True,
  disallow_transfer_to_peers=True
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
  model="gemini-2.0-flash-exp",
  description="Agent to judge whether the input text is a job description or not.",
  instruction=_instruction,
  output_key="job_description_judgement",
  output_schema=JobDescriptionJudgement,
  include_contents='none',
  disallow_transfer_to_parent=True,
  disallow_transfer_to_peers=True
)


######################### Interviewer Self Introduction ###############################

def check_inputs_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  """
  Callback to check if the inputs are valid resumes and job descriptions.
  """
  resume_judgement = callback_context.state.get("resume_judgement")
  job_description_judgement = callback_context.state.get("job_description_judgement")
  print(f"Resume judgement: {resume_judgement}")
  print(f"Job description judgement: {job_description_judgement}")
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

Please give a brief background of yourself. 
This description should be clear and concise, befitting the PERSON WHO IS HIRING.
The description should be no more than 200 words. Please use fictional information where ever needed.
"""

interviewer_agent = LlmAgent(
  name="self_introduction_agent",
  model="gemini-2.0-flash-exp",
  description="Agent to provide background information about the interviewer.",
  instruction=_instruction,
  include_contents='none',
  disallow_transfer_to_parent=True,
  disallow_transfer_to_peers=True,
  before_agent_callback=[check_inputs_callback],
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
