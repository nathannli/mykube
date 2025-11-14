#! /bin/bash
# create namespace if not exist
kubectl get namespace discord-bots || kubectl create namespace discord-bots

# deploy bots
kubectl apply -f ./alert-bot/kube-configs/
kubectl apply -f ./energy-bot/kube-configs/
