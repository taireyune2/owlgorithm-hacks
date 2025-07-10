#!/bin/bash
FOLDER="owlspeak"
IMAGE="frontend"
REGISTRY="363560690820.dkr.ecr.us-west-2.amazonaws.com"
VERSION="1.0.0"

aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $REGISTRY
docker tag owlspeak/frontend:arm64 $REGISTRY/$FOLDER/$IMAGE:$VERSION
docker push $REGISTRY/$FOLDER/$IMAGE:$VERSION