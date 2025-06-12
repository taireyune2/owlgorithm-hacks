#!/bin/bash
cd ~/workspace/owlgorithm-hacks/frontend
docker build -t owlspeak/frontend:latest -f Dockerfile.prod .