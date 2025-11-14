#! /bin/bash
# create namespace if not exist
kubectl get namespace kasa-flask-server || kubectl create namespace kasa-flask-server

# deploy bots
kubectl apply -f ./
