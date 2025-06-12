#!/bin/bash
image_version="1.0.0"
image_name="owlgorithm-hacks-backend"
# gcloud init
# gcloud auth configure-docker us-west1-docker.pkg.dev
docker tag owlgorithm-hacks-frontend:latest us-west1-docker.pkg.dev/owlgorithm-hacks/owl-speak/owlgorithm-hacks-frontend:$image_version
docker push us-west1-docker.pkg.dev/owlgorithm-hacks/owl-speak/portfolio/shop-face:$image_version


