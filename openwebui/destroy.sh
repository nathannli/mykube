#!/usr/bin/env bash

set -euo pipefail

# remove openwebui resources
kubectl delete -f ./kubectl-yaml/ --ignore-not-found

# uninstall helm release if present
helm status openwebui -n openwebui >/dev/null 2>&1 && helm uninstall openwebui -n openwebui

# delete namespace (also removes PVCs)
kubectl delete namespace openwebui --ignore-not-found
