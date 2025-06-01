from google.adk.agents import BaseAgent, LlmAgent, SequentialAgent
from google.adk.session import InvocationContext
from typing import AsyncGenerator

class MyCustomRouterAgent(BaseAgent):
    def __init__(self, llm_agent: LlmAgent, sequential_agent: SequentialAgent, **kwargs):
        super().__init__(name="custom_router", sub_agents=[llm_agent, sequential_agent], **kwargs)
        self.llm_agent = llm_agent
        self.sequential_agent = sequential_agent

    async def _run_async_impl(self, context: InvocationContext) -> AsyncGenerator:
        user_input = context.get_input().text  # Get the user's input

        if "calculate" in user_input.lower():
            # Deterministically route to the sequential agent for calculation
            async for event in self.sequential_agent.run_async(context):
                yield event
        elif "hello" in user_input.lower():
            # Deterministically route to the LLM agent for a greeting
            async for event in self.llm_agent.run_async(context):
                yield event
        else:
            # Default to the LLM agent for general responses
            async for event in self.llm_agent.run_async(context):
                yield event

        # You can also use context.session.state to pass data between agents
        # For example: context.session.state["processed_data"] = "..."