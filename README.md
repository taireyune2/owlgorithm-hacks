# owlgorithm-hacks

## Overview


## Repository Structure

```
- .venv/
- .vscode/
  - launch.json
- app/
  - main_agent/              # Root agent folder    
    - __init__.py
    - agent.py
  - static/                  # Frontend html and js files
    - js/    
      - app.js               # Contains the interaction  
    - index.html             # The ui page
  - .env                     # Contains the API key for google ADK
  - main.py                  # Fast API server
- .gitignore
- README.md
- requirements.txt     
```

## Key Features

- **Bidirectional Audio Streaming**: Real-time voice conversation with the Gemini model
- **WebSocket Communication**: Low-latency bidirectional communication
- **Function Calling**: Demonstration of ADK tool integration with an basic agent
- **Full ADK Integration**: Uses ADK's `LiveRequestQueue` and `Runner` for communication with Gemini

## Getting Started

### Prerequisites

- Google Cloud project with API access
- Python 3.9+
- Google ADK installed (`pip install google-adk`)
- PyAudio for audio processing

### Google ADK API Keys
- https://aistudio.google.com/app/apikey
- Create API key

### Installation

1. Clone this repository
   ```
   git clone https://github.com/taireyune2/owlgorithm-hacks.git
   ```

2. Create virtual environment
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   which python
   deactivate 
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Open the client in your browser
   ```
   Run And Debug Python: FastAPI in visual studio 
   Open localhost:8000
   ```

## How It Works

The implementation uses several key technologies:

1. **ADK Integration**: The server uses ADK's `LiveRequestQueue` to stream audio and video to Gemini
2. **WebSockets**: Bidirectional communication between client and server
3. **Media Processing**: Browser APIs capture and process audio/video
4. **Async Processing**: Python's asyncio powers the server-side concurrency

### Server Architecture

The server manages several concurrent tasks:
- WebSocket connection handling
- Audio processing and streaming
- Response handling from Gemini

### Client Implementation

The client handles:
- Audio recording and playback
- WebSocket communication
- UI updates and transcription display

## Additional Resources
- [Custom Audio Steaming app Doc](https://google.github.io/adk-docs/streaming/custom-streaming/)
- [Google ADK Example with Live streaming](https://github.com/google/adk-docs/tree/main/examples/python/snippets/streaming/adk-streaming-ws/app)
- [Multimodal Live API](https://github.com/SaschaHeyer/gen-ai-livestream/tree/main/multimodal-live-api/ui)

## License
This project is licensed under the MIT License.
