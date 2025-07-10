#!/bin/bash
BACKEND_URL="https://owlspeak.keypointvision.com/api"

docker buildx build \
  -f Dockerfile.pod \
  --platform=linux/arm64 \
  --build-arg VITE_BACKEND_API_URL=$BACKEND_URL \
  --build-arg VITE_WEBSOCKET_URL=${BACKEND_URL/https/wss} \
  -t owlspeak/frontend:arm64 .