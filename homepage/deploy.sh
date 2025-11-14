#! /bin/bash
# create namespace if not exist
kubectl get namespace homepage || kubectl create namespace homepage

# deploy bots
kubectl apply -f ./
