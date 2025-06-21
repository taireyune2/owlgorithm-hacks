FROM python:3.12-alpine

### install requirements
WORKDIR /interview-agent
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

### modifying adk source code
COPY configs/functions.py /usr/local/lib/python3.12/site-packages/google/adk/flows/llm_flows/functions.py

### copy source code
COPY . .
ENV PYTHONPATH=/interview-agent/python

### run
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8080"]
