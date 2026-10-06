#! /bin/bash
# create namespace if not exist
kubectl get namespace homepage || kubectl create namespace homepage

# deploy bots
kubectl apply -f ./

# recreate the existing pod so config changes are picked up
kubectl rollout restart deployment/homepage -n homepage
kubectl rollout status deployment/homepage -n homepage
