#!/bin/bash
BACKEND_URL="https://owlspeak-backend-473519344497.us-west1.run.app"

docker buildx build \
  -f Dockerfile.prod \
  --platform=linux/amd64 \
  --build-arg VITE_BACKEND_API_URL=$BACKEND_URL \
  --build-arg VITE_WEBSOCKET_URL=${BACKEND_URL/https/wss} \
  -t owlspeak/frontend:latest .