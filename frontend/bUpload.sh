#!/bin/bash
IMAGE_NAME="owlspeak-frontend"
VERSION="1.0.0"
PROJECT_ID="owlspeak-app"
REGISTRY_PREFIX="us-west1-docker.pkg.dev"
REPO="owlspeak-deployment"

gcloud auth configure-docker us-west1-docker.pkg.dev
docker tag owlspeak/frontend:latest $REGISTRY_PREFIX/$PROJECT_ID/$REPO/$IMAGE_NAME:$VERSION
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

