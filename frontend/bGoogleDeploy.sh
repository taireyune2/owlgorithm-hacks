#!/bin/bash
IMAGE_NAME="owlspeak-frontend"
VERSION="1.0.0"
PROJECT_ID="owlspeak-app"
REGISTRY_PREFIX="us-west1-docker.pkg.dev"
REPO="owlspeak-deployment"

BACKEND_URL="https://owlspeak-backend-473519344497.us-west1.run.app"

gcloud auth configure-docker us-west1-docker.pkg.dev
docker buildx build \
  -f Dockerfile.prod \
  --platform=linux/amd64 \
  --build-arg VITE_BACKEND_API_URL=$BACKEND_URL \
  --build-arg VITE_WEBSOCKET_URL=${BACKEND_URL/https/wss} \
  -t owlspeak/frontend:amd64 .
docker tag owlspeak/frontend:amd64 $REGISTRY_PREFIX/$PROJECT_ID/$REPO/$IMAGE_NAME:$VERSION
docker push $REGISTRY_PREFIX/$PROJECT_ID/$REPO/$IMAGE_NAME:$VERSION

# Deploy to Cloud Run with environment variables
gcloud run deploy owlspeak-frontend \
  --image $REGISTRY_PREFIX/$PROJECT_ID/$REPO/$IMAGE_NAME:$VERSION \
  --platform managed \
  --region us-west1 \
  --min-instances 1 \
  --max-instances 2 \
  --allow-unauthenticated \
  --project $PROJECT_ID
  # --set-env-vars VITE_BACKEND_API_URL=$BACKEND_URL,VITE_WEBSOCKET_URL=$BACKEND_URL/$SOCKET_EXTENSION \

