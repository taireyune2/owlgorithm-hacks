from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field


class OnTopicJudgement(BaseModel):
    on_topic: bool = Field(default=False, description="Indicates whether the user's response is on-topic based on the interview question and topic.")
    explanation: str = Field(default="", description="Brief explanation if the response is off-topic.")


instruction = """
You are a interviewer auditor/admin.
You are responsible for detecting whether the user's response is on-topic or not.

Here is a summary of the interview topic:

Behavioral interview.

Here is the interview question:

{behavioral_question}

Here is the user's response:

[start_user_response]
{user_response}
[end_user_response]

Is the user's response on-topic based on the interview question and topic?
Please answer with "yes" or "no".
If "no", provide a brief explanation of why the response is off-topic.
Respond ONLY in valid JSON format following this schema:

```json
{
    "on_topic": bool,
    "explanation": "brief explanation if response is off-topic"
}
```

Do NOT include any explanations, context, or text outside of this JSON object.
"""

agent = LlmAgent(
    name="ontopic_detector", 
    description="Detect whether the user response is on-topic.",
    model="gemini-2.0-flash",
    instruction=instruction,
    # tools=[],
    output_key="on_topic_judgement",
    output_schema=OnTopicJudgement,  
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)