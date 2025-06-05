https://artifacthub.io/packages/helm/k8s-dashboard/kubernetes-dashboard
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
helm upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --create-namespace --namespace kubernetes-dashboard
helm list -n kubernetes-dashboard                                                                                                                                  false
