from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.genai import types
from typing import AsyncGenerator, Optional

import logging
import time
import json

from . import configs


class OnTopicJudgement(BaseModel):
  on_topic: bool = Field(default=False, description="Indicates whether the user's response is on-topic based on the provided context.")
  explanation: str = Field(default="", description="Brief explanation if the response is off-topic.")


_instruction = """You are a interviewer auditor/admin.
You are responsible for detecting whether the user's response is related to the background or not.

Here are the relevant background:

Interviewee's resume: 
{resume}

Interview job description:
{job_description}

Interview question:
{question}

Here is the interviewee's response:
[start_interviewee]
{phase_client_text}
[end_interviewee]

Your task is to determine if the user's response is relevant to the provided context.

Please answer with "True" or "False".
If "False", provide a brief explanation of why the response is off-topic.
Respond ONLY in valid JSON format following this schema:

```json
{
  "on_topic": bool,
  "explanation": "brief explanation if response is off-topic"
}
```

Do NOT include any explanations, context, or text outside of this JSON object.
"""

def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
  """
  Callback to handle the response from the agent.
  """
  # logging.info(llm_response.model_dump_json(indent=2))
  
  result = json.loads(llm_response.content.parts[0].text)
  logging.info(f"Handle on-topic detection response. {result}")
  if result.get("on_topic", False):
    callback_context.state["off_topic"] = 0
  else:
    callback_context.state["off_topic"] += 1
    logging.info(f"Off-topic count increased with reason: {result.get('explanation', 'No explanation provided')}")

def init_ontopic_agent(name: str) -> LlmAgent:
  """
  Initialize an on-topic detection agent with the given name.
  """
  return LlmAgent(
    name=name,
    description="Detect whether the user response is on-topic.",
    model=configs["model"],
    instruction=_instruction,
    after_model_callback=after_model_callback,
    output_schema=OnTopicJudgement,  
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    include_contents='none',
  )
