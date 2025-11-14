#! /bin/bash

# create namespace if not exist
kubectl get namespace prometheus || kubectl create namespace prometheus
# deploy
kubectl apply -f ./
