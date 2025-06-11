from google.adk.runners import InMemoryRunner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.events import Event

from .agent import root_agent

class LiveRun:
  def __init__(self):
    self.runner = InMemoryRunner(
      app_name="audio_assistant",
      agent=root_agent,
    )