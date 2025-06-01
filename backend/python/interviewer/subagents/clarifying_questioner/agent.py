from google.adk.agents import LlmAgent

instruction = """
You are a helpful assistant that greets the user. Ask for user's name and greet them by name.
"""

star_parser = LlmAgent(
    name="star_parser", 
    description="Summarizes the response from user.",
    model="gemini-2.0-flash",
    instruction=instruction,
    tools=[

    ],
    output_key="star_method",  
)