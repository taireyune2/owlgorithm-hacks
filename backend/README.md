# Python

## Setup
path: backend/
```
python3 -m venv .venv
source .venv/bin/activate
which python
pip install -r requirements-dev.txt
```

## Console Demo

path: backend/python
```
python console.py --config-dir ../configs/console-dev-config.json
```

When prompted to enter User ID, enter any random characters.  
When prompted to provide text file response, enter `../examples/response.txt` for 
the provided response.

## Run Service

### Modify ADK source code

- Find the file functions.py using control-p (command-p) within the new .venv folder.
- Search for trace_tool_call on line 288. Comment out the whole function call.

### Run Service

```
python service.py --config-dir ../configs/dev.json
```

To interact with the application, either go directly to localhost:8000 or follow the frontend README to spinup the react application.

### pytest

path: backend/python
```
pytest interviewer/agent_behavior_test.py::test_core
```


