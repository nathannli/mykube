# https://github.com/prometheus-community/helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/prometheus --namespace prometheus