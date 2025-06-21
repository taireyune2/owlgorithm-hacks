#!/bin/bash


image_name="owlgorithm-hacks-frontend"
PROJECT_ID=
Registry_URL=
repository_name=

# Set your backend service URL (your deployed backend)
BACKEND_URL="https://interview-agent-178724632712.us-west1.run.app"

docker tag ${Registry_URL}/${PROJECT_ID}/${repository_name}/${image_name}:latest
gcloud auth configure-docker us-west1-docker.pkg.dev
docker buildx build \
  --platform=linux/amd64,linux/arm64 \
  -f Dockerfile.prod \
  --build-arg VITE_BACKEND_API_URL=$BACKEND_URL \
  --build-arg VITE_WEBSOCKET_URL=${BACKEND_URL/https/wss} \
  -t us-west1-docker.pkg.dev/${PROJECT_ID}/${repository_name}/owlgorithm-hacks-frontend:latest \
  --push .
docker push us-west1-docker.pkg.dev/${PROJECT_ID}/${repository_name}/owlgorithm-hacks-frontend:latest

# Deploy to Cloud Run with environment variables
gcloud run deploy owlgorithm-hacks-frontend \
  --image us-west1-docker.pkg.dev/${PROJECT_ID}/${repository_name}/owlgorithm-hacks-frontend:latest \
  --platform managed \
  --region us-west1 \
  --allow-unauthenticated \
  --set-env-vars VITE_BACKEND_API_URL=$BACKEND_URL,VITE_WEBSOCKET_URL=${BACKEND_URL/https/wss} \
  --project $PROJECT_ID