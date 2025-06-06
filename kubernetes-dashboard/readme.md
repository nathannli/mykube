
helm install kubernetes-dashboard/kubernetes-dashboard --namespace kubernetes-dashboard --generate-name -f helm-values.yaml

helm list -n kubernetes-dashboard
helm delete kubernetes-dashboard-1749167661 --namespace kubernetes-dashboard


follow this tutorial
https://github.com/kubernetes/dashboard/issues/9066#issuecomment-2254511968