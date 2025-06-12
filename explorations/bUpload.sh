#!/bin/bash
image_version="1.0.0"
image_name="owlspeak/backend"
# gcloud init
# gcloud auth configure-docker us-west1-docker.pkg.dev
docker tag $image_name:latest us-west1-docker.pkg.dev/owlgorithm-hacks/owl-speak/$image_name:$image_version
docker push us-west1-docker.pkg.dev/owlgorithm-hacks/owl-speak/$image_name:$image_version