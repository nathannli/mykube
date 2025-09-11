# deletes expired replicaset sets
kubectl get rs -n kasa-flask-server \
            -o jsonpath='{range .items[?(@.status.replicas==0)]}{.metadata.name}{"\n"}{end}' \
          | xargs -r kubectl delete rs -n kasa-flask-server