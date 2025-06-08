from google.adk.agents import LlmAgent

from .. import utils

instruction = """
You are an interviewer.

You are tasked with asking a follow-up question based on the user's behavioral response.

Here is the original behavioral question that was asked:

{behavioral_question}

Here is a response from a user:

[start_user_response]
{user_response}
[end_user_response]

Please ask an appropriate follow-up question based on the response.
"""

agent = LlmAgent(
  name="followup_questioner", 
  description="Questioner that asks a follow-up question based on the user's response.",
  model="gemini-2.0-flash",
  instruction=instruction,
  # tools=[],
  output_key="followup_question",  
  before_agent_callback=[utils.log_agent_context],
  before_model_callback=[utils.log_before_model_context],
  after_model_callback=[utils.log_after_model_context],
  after_agent_callback=[utils.log_agent_context],
  include_contents='none'
)