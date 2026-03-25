#!/usr/bin/env bash

set -euo pipefail

# create namespace if not exist
kubectl get namespace headlamp >/dev/null 2>&1 || kubectl create namespace headlamp

# deploy headlamp resources
kubectl apply -f ./

# ensure admin service account exists
kubectl -n headlamp get serviceaccount headlamp-admin >/dev/null 2>&1 || \
  kubectl -n headlamp create serviceaccount headlamp-admin

# ensure admin binding exists
kubectl get clusterrolebinding headlamp-admin >/dev/null 2>&1 || \
  kubectl create clusterrolebinding headlamp-admin \
    --serviceaccount=headlamp:headlamp-admin \
    --clusterrole=cluster-admin
