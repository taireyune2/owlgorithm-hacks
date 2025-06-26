#!/bin/bash
docker run -it --rm \
  --name owlspeak-backend-dev -p 8000:8000 \
  --network owlspeak-dev \
  owlspeak/backend:latest 
