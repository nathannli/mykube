#!/usr/bin/env bash

set -euo pipefail

# create namespace if not exist
kubectl get namespace openwebui >/dev/null 2>&1 || kubectl create namespace openwebui

# deploy openwebui resources
kubectl apply -f ./kubectl-yaml/
