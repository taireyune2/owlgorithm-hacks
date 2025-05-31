from google.adk.agents import LlmAgent

root_agent = LlmAgent(
    name="root_agent", 
    description="Say hello to the user.",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant that greets the user. Ask for user's name and greet them by name.",
    tools=[],
)