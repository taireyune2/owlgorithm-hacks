from google.adk.agents import LlmAgent, BaseAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types
from typing import AsyncGenerator, Optional
from google.adk.events import Event, EventActions
from pydantic import BaseModel, Field
from typing import AsyncGenerator, Optional, override
import logging
import time
from . import configs


##################### thought agent - question generator #####################################
def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
  ### skip this if there is not enough content
  content = callback_context.state["phase_client_text"]
  if len(content) < 50:
    logging.info("Too early to generate follow-up question, waiting for more response.")
    return types.Content(
      role="model",
      parts=[types.Part(text="")],
    )


_instruction = """You are a question asker.
You are responsible for generating questions based on the user's behavioral response.

Here is the behavioral question: {question}
And previous follow-up questions: {followup_questions}

Here is the response from the interviewee: 
[start_interviewee]
{phase_client_text}
[end_interviewee]

Based on this response, ask the interviewee a followup question.
Ask a question that is relevant to the interviewee's response and encourages the interviewee to either:
- elaborate further, 
- clarify any points, 
- or provide specific examples.

Only write down the new followup question. Do not include any additional text or explanations. 
DO NOT repeat the previous follow-up question.
DO NOT include any additional discussion in your response.
"""

def init_question_generator(name: str) -> LlmAgent:
  """
  Initialize a question generator agent with the given name.
  """
  return LlmAgent(
    name=name,
    description="Generate follow-up questions based on the interviewee's responses.",
    model=configs["model"],
    instruction=_instruction,
    # before_agent_callback=[before_agent_callback],
    include_contents='none',
    output_key="working_followup_question",
    generate_content_config=types.GenerateContentConfig(
      temperature=2.0
    ),
  )

####################### answer judge ##############################
class JudgeResult(BaseModel):
  met: bool = Field(description="Whether the criteria for a detailed response are met.")
  reason: str = Field(default="", description="Reason for not meeting the criteria, if applicable.")


###################################### routing agent #####################################

class RoutingAgent(BaseAgent):
  """
  Agent that routes the interview to the next phase based on the current state.
  """
  interviewer_instruction: str

  def __init__(self, name: str, interviewer_instruction: str):
    super().__init__(name=name, interviewer_instruction=interviewer_instruction)
    
  @override
  async def _run_async_impl(
    self, ctx: InvocationContext
  ) -> AsyncGenerator[Event, None]:
    state = ctx.session.state.copy()
    logging.info(f"Entering routing agent run async.")
    ### check route condition
    if not state["judge_result"]["met"]:
      logging.info("Criteria not met. No action taken.")
      return

    ### direct to follow up question phase
    if time.time() - state["phase_start"] > configs["durations"]["followup"]:
      logging.info("Criteria met, proceeding to next follow-up question.")
      state_delta = {
        "followup_questions": state["followup_questions"] + [state["working_followup_question"]],
        "phase": "followup_question",
      }
      yield Event(
        author=self.name,
        invocation_id="route_agent_event",
        actions=EventActions(
          state_delta=state_delta, 
          transfer_to_agent="followup_questioner"
        ) 
      )
    
    ### direct to next behavioral question
    elif state["question_index"] + 1 < len(state["interview_questions"]):
      logging.info("Criteria met, proceeding to next behavioral question.")
      state_delta = {
        "followup_questions": [],
        "phase_start": time.time(),
        "phase": "behavioral_question",
        "question_index": state["question_index"] + 1,
        "question": state["interview_questions"][state["question_index"]+1],
        "phase_client_text": "",
        "phase_agent_text": "",
        "judge_result": {},
        "interview_instructions": self.interviewer_instruction.format(
          behavioral_question=state["interview_questions"][state["question_index"]+1]
        ),
      }  
      yield Event(
        author=self.name,
        invocation_id="route_agent_event",
        actions=EventActions(
          state_delta=state_delta, 
          transfer_to_agent="behavioral_questioner"
        ) 
      )

    ### direct to closing phase
    else:
      logging.info("Criteria met, proceeding to closing phase.")
      yield Event(
        author=self.name,
        invocation_id="route_agent_event",
        actions=EventActions(
          transfer_to_agent="closing_responder"
        ) 
      )
