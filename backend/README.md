# Python

## Setup
path: backend/
```
python3 -m venv .venv
source .venv/bin/activate
which python
pip install -r requirements.txt
```

## Console Demo

path: backend/python
```
python console.py --config-dir ../configs/console-dev-config.json
```

When prompted to enter User ID, enter any random characters.  
When prompted to provide text file response, enter `../examples/response.txt` for 
the provided response.

### pytest

path: backend/python
```
pytest
```