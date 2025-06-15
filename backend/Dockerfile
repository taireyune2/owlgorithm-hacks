FROM python:3.12-alpine

### install requirements
COPY requirements.txt /home/service/requirements.txt
WORKDIR /home/service
RUN pip install -r requirements.txt
RUN rm /home/service/requirements.txt

### copy source code
COPY python/ /home/service/python
COPY python/.container /home/service/python/.env
COPY configs/containerized.json /home/service/configs/.
WORKDIR /home/service/python

### run
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000"]