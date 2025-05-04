#!/bin/bash

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t nathannnli/mykasa:latest \
  --push \
  docker-app/