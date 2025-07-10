#!/bin/bash
docker buildx build \
  --platform=linux/arm64 \
  -t owlspeak/backend:arm64 -f Dockerfile.pod .