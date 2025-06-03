from google.adk.agents import (
    BaseAgent, LlmAgent, SequentialAgent, ParallelAgent
) 
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.events import Event
from google.genai import types
from typing import AsyncGenerator, Optional
from typing_extensions import override
import logging  

from .subagents import ontopic_detector, followup_questioner, question_judge


sequential_question_formulator = SequentialAgent(
    name="sequential_question_formulator",
    sub_agents=[followup_questioner.agent, question_judge.agent],
    description="Sequential agent that handles follow-up questions and judges responses.",
)


def populate_state(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Store user input into session state before running the agent.
    """
    if not callback_context.user_content or not callback_context.user_content.parts:
        return types.Content(role="system", parts=[types.Part(text="User input is required.")])
    
    callback_context.state["user_response"] = callback_context.user_content.parts[0].text
    return None
    # logging.info("Running before agent callback...")


root_agent = ParallelAgent(
    name="root_agent",
    sub_agents=[ontopic_detector.agent, sequential_question_formulator],
    description="Parallel agent that detects topics and manages follow-up questions.",
    before_agent_callback=populate_state
)

# instructions = """
# You are an interviewer.

# You are tasked with asking follow-up questions
# """
# root_agent = LlmAgent(
#     name="root_agent", 
#     description="Interviewer agent that asks follow-up questions after user response.",
#     model="gemini-2.0-flash",
#     instruction=instructions,
#     tools=[],
# )

# ### agent that runs a deterministic responses, do not call llm
# class InterviewerAgent(BaseAgent):
#     """
#     Agent that deterministically directs flow to the defined agents
#     based on state using state machine pattern.
#     This agent does not call the LLM, but routes requests to other agents
#     based on predefined rules.
#     """
#     ontopic_detector: LlmAgent
#     followup_questioner: LlmAgent
#     question_judge: LlmAgent
#     sequential_agent: SequentialAgent
#     parallel_agent: ParallelAgent
    
#     def __init__(
#         self, 
#         ontopic_detector: LlmAgent,
#         followup_questioner: LlmAgent,
#         question_judge: LlmAgent,
#         name: str = "router_agent",
#     ):
#         logging.info("Initializing RouterAgent...")
#         """Initialize the RouterAgent."""
#         sequential_agent = SequentialAgent(
#             name="sequential_agent",
#             sub_agents=[followup_questioner, question_judge],
#             description="Sequential agent that handles follow-up questions and judges responses.",
#         )
#         parallel_agent = ParallelAgent(
#             name="parallel_agent",
#             sub_agents=[ontopic_detector, sequential_agent],
#             description="Parallel agent that detects topics and manages follow-up questions.",
#         )
#         super().__init__(
#             ontopic_detector=ontopic_detector,
#             followup_questioner=followup_questioner,
#             question_judge=question_judge,
#             sequential_agent=sequential_agent,
#             parallel_agent=parallel_agent,
#             name=name,
#             sub_agents=[parallel_agent],
#         )

#     @override
#     async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
#         """
#         Deterministic control flow for other interview agents
#         """
#         logging.info("Router agent started#############")
#         async for event in self.parallel_agent.run_async(ctx):
#             yield event

      


# root_agent = InterviewerAgent(
#     name="root_agent",
#     ontopic_detector=ontopic_detector,
#     followup_questioner=followup_questioner,
#     question_judge=question_judge,
# )
