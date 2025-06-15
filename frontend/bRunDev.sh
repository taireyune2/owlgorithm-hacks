#!/bin/bash
cd ~/workspace/owlgorithm-hacks/frontend
docker build -t owlspeak/frontend:latest -f Dockerfile.dev .
docker run -it --rm \
  --name owlspeak-frontend-dev -p 3000:3000  \
  --network owlspeak-dev \
  -e NODE_ENV=development \
  owlspeak/frontend:latest 
  