#! /bin/bash
# create namespace if not exist
kubectl get namespace discord-bots || kubectl create namespace discord-bots

# deploy bots
kubectl apply -f ./
