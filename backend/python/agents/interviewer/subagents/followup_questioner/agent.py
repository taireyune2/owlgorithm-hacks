from google.adk.agents import LlmAgent

instruction = """
You are an interviewer.

Here is a response from a user:

[start_user_response]
{user_response}
[end_user_response]

Please ask an appropriate follow-up question.
"""

followup_questioner = LlmAgent(
    name="followup_questioner", 
    description="Questioner that asks a follow-up question based on the user's response.",
    model="gemini-2.0-flash",
    instruction=instruction,
    # tools=[],
    output_key="followup_question",  
)