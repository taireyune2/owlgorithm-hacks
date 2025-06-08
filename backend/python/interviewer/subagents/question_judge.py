from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field

from .. import utils

class QuestionJudgement(BaseModel):
    is_appropriate: bool = Field(default=False, description="Indicates whether the follow-up question is appropriate based on the user's response.")
    explanation: str = Field(default="", description="Brief explanation if the follow-up question is not appropriate.")


instruction = """
You are a interview auditor/admin. 
You are responsible for determining whether a follow-up question asked by the interviewer is appropriate based on the user's response.

Here is the response from the user:

[start_user_response]
{user_response}
[end_user_response]

Here is the follow-up question asked by the interviewer:

[start_followup_question]
{followup_question}
[end_followup_question]

Is this follow-up question appropriate based on the user's response?
Please answer with "yes" or "no". 
If "no", provide a brief explanation of why the follow-up question is not appropriate.
Respond ONLY in valid JSON format following this schema:

```json
{
    "is_appropriate": bool,
    "explanation": "brief explanation if not appropriate"
}
```

Do NOT include any explanations, context, or text outside of this JSON object.
"""

agent = LlmAgent(
    name="question_judge", 
    description="Summarizes the response from user.",
    model="gemini-2.0-flash",
    instruction=instruction,
    # tools=[],
    output_key="question_judgement", 
    output_schema=QuestionJudgement,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    before_agent_callback=[utils.log_agent_context],
    before_model_callback=[utils.log_before_model_context],
    after_model_callback=[utils.log_after_model_context],
    after_agent_callback=[utils.log_agent_context],
    include_contents='none'
)