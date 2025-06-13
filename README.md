## How to start the frontend?
Run the following command to start the frontend. It will give you a url to open the interview page
- cd frontend
- npm run dev


## How to start the backend?
There are 2 ways to start the backend. Before you do that, remember to activate the environment using source {path to your virtual environment folder}/bin/activate

### First way:
- Follow this link to create a launch.json for VS Code: https://code.visualstudio.com/docs/debugtest/debugging-configuration
- In the launch.json file, put the following:
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run service.py with config",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/backend/python/service.py",
            "args": ["--config-dir", "${workspaceFolder}/backend/configs/dev.json"],
            "console": "integratedTerminal"
        }
    ]
}
- When you start debugging, it will automatically go to the folder to open the app. "${workspaceFolder}/backend/python/service.py",

### Second way:
- cd into backend/python
- python service.py --config-dir ../configs/dev.json