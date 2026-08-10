#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "Missing .env. Copy .env.example and set TOKEN first." >&2
  exit 1
fi

TOKEN="$(rg '^TOKEN=' .env | head -n 1 | cut -d= -f2-)"

if [[ -z "$TOKEN" || "$TOKEN" == "replace-with-a-random-secret" ]]; then
  echo "Set TOKEN in .env to a random secret first." >&2
  exit 1
fi

export TOKEN

case "${1:-up}" in
  up)
    if docker container inspect browserless >/dev/null 2>&1; then
      docker start browserless
      exit 0
    fi

    docker run -d \
      --name browserless \
      --restart unless-stopped \
      --init \
      --env TOKEN \
      --env ALLOW_GET=false \
      --env CONCURRENT=4 \
      --env CORS=false \
      --env ENABLE_DEBUGGER=false \
      --env QUEUED=8 \
      --env TIMEOUT=30000 \
      --publish 127.0.0.1:3000:3000 \
      --shm-size=1g \
      ghcr.io/browserless/chromium:v2.55.3
    ;;
  down)
    docker rm -f browserless
    ;;
  logs)
    docker logs -f browserless
    ;;
  status)
    docker ps --filter name=browserless
    ;;
  *)
    echo "Usage: $0 {up|down|logs|status}" >&2
    exit 1
    ;;
esac
