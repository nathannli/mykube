#!/bin/bash

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t nathannnli/mygovee:$1 \
  --push \
  docker-app/