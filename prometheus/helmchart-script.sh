# https://github.com/prometheus-community/helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/prometheus --namespace prometheus

# if modified the prometheus-values.yml file, run the following command to update the helm chart
helm upgrade prometheus prometheus-community/prometheus --namespace prometheus --values prometheus/prometheus-values.yml
