# Environment

Follow the README to install .venv .

Copy a .env file into `root/exploration2/server`

### Modify ADK source code

- Find the file functions.py using control-p (command-p) within the new .venv folder.
- Search for trace_tool_call on line 288. Comment out the whole function call.

# Run Demo

Follow README to run: 

```bash
python server/server_adk.py
```

```bash
# Using Python's built-in HTTP server
python -m http.server 8000
```

Then navigate to `http://localhost:8000/client/index.html` in your browser.