#! /bin/bash
# create namespace if not exist
kubectl get namespace grafana || kubectl create namespace grafana

# deploy bots
kubectl apply -f ./
