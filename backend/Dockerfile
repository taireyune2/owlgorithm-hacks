FROM python:3.12-alpine

### install requirements
COPY requirements.txt /home/service/requirements.txt
WORKDIR /home/service
RUN pip install -r requirements.txt
RUN rm /home/service/requirements.txt

### modifying adk source code
COPY configs/functions.py /usr/local/lib/python3.12/site-packages/google/adk/flows/llm_flows/functions.py

### copy source code
COPY python/ /home/service/python
COPY configs/containerized.json /home/service/configs/containerized.json

### set environment variables
ENV CONFIG_DIR=/home/service/configs/containerized.json
ENV GOOGLE_GENAI_USE_VERTEXAI=FALSE

WORKDIR /home/service/python

### run
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8080"]