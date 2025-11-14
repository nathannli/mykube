#! /bin/bash
# create namespace if not exist
kubectl get namespace govee-flask-server || kubectl create namespace govee-flask-server

# deploy bots
kubectl apply -f ./
