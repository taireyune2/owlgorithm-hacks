FROM python:3.12-alpine

# set a working directory to run docker commands
WORKDIR /app
# copy the requirements file into the container
COPY ./requirements.txt .
# and install the dependencies  
RUN pip install --upgrade pip --no-cache-dir -r requirements.txt
# copy the application into the app container
COPY . /app /app/

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]