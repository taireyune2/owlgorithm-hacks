#!/bin/bash
cd ~/workspace/owlgorithm-hacks/backend
docker run -it --rm \
  --name owlspeak-backend-dev -p 8000:8000 \
  --network owlspeak-dev \
  --env-file .env \
  owlspeak/backend:latest 
