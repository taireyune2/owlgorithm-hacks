#!/bin/bash
IMAGE_NAME="owlspeak-backend"
VERSION="1.0.0"
PROJECT_ID="owlspeak-app"
REGISTRY_PREFIX="us-west1-docker.pkg.dev"
REPO="owlspeak-deployment"
GOOGLE_API_KEY="agent-prod-api-key:latest"

gcloud auth configure-docker us-west1-docker.pkg.dev
docker buildx build --platform=linux/amd64 -t owlspeak/backend:amd64 .
docker tag owlspeak/backend:amd64 $REGISTRY_PREFIX/$PROJECT_ID/$REPO/$IMAGE_NAME:$VERSION
docker push $REGISTRY_PREFIX/$PROJECT_ID/$REPO/$IMAGE_NAME:$VERSION

gcloud run deploy owlspeak-backend \
  --image $REGISTRY_PREFIX/$PROJECT_ID/$REPO/$IMAGE_NAME:$VERSION \
  --platform managed \
  --region us-west1 \
  --min-instances 1 \
  --max-instances 2 \
  --allow-unauthenticated \
  --update-secrets GOOGLE_API_KEY=$GOOGLE_API_KEY \
  --project $PROJECT_ID
