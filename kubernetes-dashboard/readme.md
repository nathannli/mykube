
helm install kubernetes-dashboard/kubernetes-dashboard --namespace kubernetes-dashboard --generate-name

follow this tutorial
https://github.com/kubernetes/dashboard/issues/9066#issuecomment-2254511968

for the bearer token, ensure when you copy and paste the token you're not including garbage characters. Check in a text editor