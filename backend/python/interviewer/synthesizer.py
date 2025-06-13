from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types
from pydantic import BaseModel, Field
import random

from common.configs import file as config


def get_default_background() -> dict[str, str]:
  """
  Returns the name and background.

  Example structure:
  {
    "name": "Alex",
    "background": "I am a software engineer."
  }

  """
  return random.choice(config["agent"]["default_backgrounds"])

get_resume_tool = FunctionTool(func=get_default_background)

class BackgroundInfo(BaseModel):
  name: str = Field(description="A unisex name that correspond to what is in the resume.")
  background: str = Field(description="Resume in markdown format.")


_instruction = """You are a synthesizer of resumes.

You will generate a resume based on the relevant description of what the team does.

If what we have below is not a work related description, use the 'get_resume_tool' to obtain the resume.

[relevant_description_start]
{job_description}
[relevant_description_end]

Otherwise, generate a resume based on the relevant description provided.

Format your response as below:
{
  "name": str ("Alex"),
  "background": str (.md format of a resume)
}
"""

synthesizer_agent = LlmAgent(
  name="synthesizer_agent", 
  description="Synthesize resumes from job descriptions.",
  model="gemini-2.0-flash-exp",
  instruction=_instruction,
  tools=[get_resume_tool],
  output_key="background_info", 
  output_schema=BackgroundInfo,
  # before_agent_callback=[utils.log_agent_context],
  # before_model_callback=[utils.log_before_model_context],
  # after_model_callback=[utils.log_after_model_context],
  # after_agent_callback=[utils.log_agent_context],
  include_contents='none'
)