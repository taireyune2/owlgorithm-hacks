from google.adk.agents import (
    BaseAgent, LlmAgent, SequentialAgent, ParallelAgent
) 
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from typing import AsyncGenerator
from typing_extensions import override
import logging

from .subagents.ontopic_detector.agent import ontopic_detector
from .subagents.followup_questioner.agent import followup_questioner
from .subagents.question_judge.agent import question_judge

### agent that runs a deterministic responses, do not call llm
class InterviewerAgent(BaseAgent):
    """
    Agent that deterministically directs flow to the defined agents
    based on state using state machine pattern.
    This agent does not call the LLM, but routes requests to other agents
    based on predefined rules.
    """
    ontopic_detector: LlmAgent
    followup_questioner: LlmAgent
    question_judge: LlmAgent
    sequential_agent: SequentialAgent
    parallel_agent: ParallelAgent
    
    def __init__(
        self, 
        ontopic_detector: LlmAgent,
        followup_questioner: LlmAgent,
        question_judge: LlmAgent,
        name: str = "router_agent",
    ):
        logging.info("Initializing RouterAgent...")
        """Initialize the RouterAgent."""
        sequential_agent = SequentialAgent(
            name="sequential_agent",
            sub_agents=[followup_questioner, question_judge],
            description="Sequential agent that handles follow-up questions and judges responses.",
        )
        parallel_agent = ParallelAgent(
            name="parallel_agent",
            sub_agents=[ontopic_detector, sequential_agent],
            description="Parallel agent that detects topics and manages follow-up questions.",
        )
        super().__init__(
            ontopic_detector=ontopic_detector,
            followup_questioner=followup_questioner,
            question_judge=question_judge,
            sequential_agent=sequential_agent,
            parallel_agent=parallel_agent,
            name=name,
            sub_agents=[parallel_agent],
        )

    @override
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Deterministic control flow for other interview agents
        """
        logging.info("Router agent started#############")
        async for event in self.parallel_agent.run_async(ctx):
            yield event

      


root_agent = InterviewerAgent(
    name="root_agent",
    ontopic_detector=ontopic_detector,
    followup_questioner=followup_questioner,
    question_judge=question_judge,
)
# root_agent = LlmAgent(
#     name="root_agent", 
#     description="Say hello to the user.",
#     model="gemini-2.0-flash",
#     instruction="You are a helpful assistant that greets the user. Ask for user's name and greet them by name.",
#     tools=[],
# )