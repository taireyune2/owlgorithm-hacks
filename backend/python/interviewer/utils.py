from google.adk.agents.callback_context import CallbackContext
from google.adk.events import Event
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types
from typing import AsyncGenerator, Optional
import logging
import json


def log_agent_context(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Log the callback context for debugging purposes.
    """
    if callback_context.user_content and callback_context.user_content.parts:
        logging.info(f"Agent callback user content for {callback_context.agent_name}:\n{callback_context.user_content.parts[0].text}")

    logging.info(f"Agent callback state for {callback_context.agent_name}:\n{json.dumps(callback_context.state.to_dict(), indent=2)}")
    return None


def log_before_model_context(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """
    Log the model context for debugging purposes.
    """
    logging.info(f"Model request for {callback_context.agent_name}:\n{llm_request.contents}")
    return None


def log_after_model_context(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    """
    Log the model context for debugging purposes.
    """
    logging.info(f"Model response for {callback_context.agent_name}:\n{llm_response.content}")
    return None