#! /bin/bash
# create namespace if not exist
kubectl get namespace kubernetes-dashboard || kubectl create namespace kubernetes-dashboard

helm install kubernetes-dashboard/kubernetes-dashboard --namespace kubernetes-dashboard --generate-name

kubectl apply -f ./
