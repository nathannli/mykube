#! /bin/bash
# create namespace if not exist
kubectl get namespace metabase || kubectl create namespace metabase

kubectl apply -f ./
