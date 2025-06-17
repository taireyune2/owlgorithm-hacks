# Backend Application

The backend for the Owlgorithm application. This app handles the 

## Setup
path: backend/
```
python3 -m venv .venv
source .venv/bin/activate
which python
pip install -r requirements-dev.txt
```

## Run Service

### Modify ADK source code

- Find the file functions.py using control-p (command-p) within the new .venv folder: .venv/lib/python3.12/site-packages/google/adk/flows/llm_flows/functions.py. 

- Search for trace_tool_call on line 288. Comment out the whole function call.

### Run Service

From the root/backend/python, run
```
uvicorn service:app --reload

# or python service.py
```

To interact with the application in dev model, go directly to localhost:8000.

To use the full UI interface, follow the frontend README to spinup the react application.

### pytest

path: backend/python
```
pytest interviewer/agent_behavior_test.py::test_core
```



client audio -> agent

agent:
  - respond with audio
  - call function
