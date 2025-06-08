# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import LlmAgent
from typing import AsyncGenerator, Optional
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest


def log_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
   if callback_context.user_content and callback_context.user_content.parts:
      print(f"Running before agent callback.\n{callback_context.user_content.parts[0].text}")
   else:
      print("Running before agent callback with no callback content.")


def log_model_callback(
   callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
   if llm_request.contents and llm_request.contents.parts:
      print(f"Running before model callback.\n{llm_request.contents.parts[0].text}")
   else:
      print("Running before model callback with no llm_request content.")


root_agent = LlmAgent(
   # A unique name for the agent.
   name="main_agent",
   # The Large Language Model (LLM) that agent will use.
   # model="gemini-2.0-flash-exp",
   model="gemini-2.0-flash-exp",
   # model="gemini-2.0-flash-live-001",  # New streaming model version as of Feb 2025
   # A short description of the agent's purpose.
   description="Agent to answer questions",
   # Instructions to set the agent's behavior.
   instruction="You are a helpful assistant that answers user's questions. Your name is root agent.",
   # before_agent_callback=log_agent_callback,
   # before_model_callback=log_model_callback,
)
