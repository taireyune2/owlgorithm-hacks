#!/bin/bash
image_name="owlgorithm-hacks-frontend"
PROJECT_ID=
Registry_URL=
repository_name=
docker tag ${Registry_URL}/${PROJECT_ID}/${repository_name}/${image_name}:latest
gcloud auth configure-docker us-west1-docker.pkg.dev
docker buildx build \
  --platform=linux/amd64,linux/arm64 \
  -f Dockerfile.prod \
  -t us-west1-docker.pkg.dev/${PROJECT_ID}/${repository_name}/owlgorithm-hacks-frontend:latest \
  --push .
docker push us-west1-docker.pkg.dev/${PROJECT_ID}/${repository_name}/owlgorithm-hacks-frontend:latest

