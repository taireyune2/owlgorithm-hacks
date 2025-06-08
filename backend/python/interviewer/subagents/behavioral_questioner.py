from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.genai import types


_interview_questions = [
  "Describe a situation where you disagreed with a team member. How did you handle it?",
  "Describe a time you got feedback that was hard to hear. How did you handle it?",
  "Give an example of a time you took initiative outside your job scope.",
  "Tell me about a time you had to make a difficult decision with limited data.",
]


def get_next_question(tool_context: ToolContext) -> dict[str, str]:
  """
  If question count is greater than zero and there is enough time,
  return the next question.
  Else, direct to the closing phase.
  """
  ### store previous states # TODO: add to end of questioning
  # if tool_context.state.get("previous_states", ""):
  #   previous_states = tool_context.state["previous_states"].copy() 
  #   previous_states.append({
  #     "behavioral_question": tool_context.state["behavioral_question"]
  #   })
  #   tool_context.state["previous_states"] = previous_states

  if not _interview_questions: 
    raise ValueError("No more questions available.")
  
  ### get question
  question = _interview_questions[-1]
  tool_context.state["behavioral_question"] = question
  return {
    "behavioral_question": question
  }

get_next_question_tool = FunctionTool(func=get_next_question)

_instruction = """You are an interviewer responsible for asking the interviewee behavioral questions.

Call the 'get_next_question_tool' to get the next question to ask the interviewee.
"""

agent = LlmAgent(
  name="behavioral_questioner",
  description="Ask the interviewee behavioral questions.",
  model="gemini-2.0-flash",
  instruction=_instruction,
  tools=[get_next_question_tool], 
  generate_content_config=types.GenerateContentConfig(
    temperature=2.0
  ),
)