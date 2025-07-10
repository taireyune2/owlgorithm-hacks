#!/bin/bash
docker buildx build --platform=linux/amd64 -t owlspeak/backend:amd64 .