#!/bin/bash

VERSION=v1

# Clone repo if not already present
if [ ! -d "Transmission" ]; then
  git clone --recurse-submodules https://github.com/transmission/transmission Transmission
else
  cd Transmission
  git pull --rebase --prune
  git submodule update --init --recursive
  cd ..
fi

echo $(pwd)
# Build and push docker image (Dockerfile does build)
docker build -t nathannnli/mytransmission:$VERSION ./Transmission -f ./Dockerfile
docker push nathannnli/mytransmission:$VERSION
