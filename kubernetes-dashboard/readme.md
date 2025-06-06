
helm install kubernetes-dashboard/kubernetes-dashboard --namespace kubernetes-dashboard --generate-name -f helm-values.yaml

helm list -n kubernetes-dashboard
helm delete kubernetes-dashboard-1749167661 --namespace kubernetes-dashboard


follow this tutorial
https://github.com/kubernetes/dashboard/issues/9066#issuecomment-2254511968

for the bearer token, ensure when you copy and paste the token you're not including garbage characters. Check in a text editor