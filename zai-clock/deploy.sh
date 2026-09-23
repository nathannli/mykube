#! /bin/bash
set -euo pipefail
cd "$(dirname "$0")"

# create namespace if not exist
kubectl get namespace zai-clock >/dev/null 2>&1 || kubectl create namespace zai-clock

# self-signed cert for myclock.internal (re-issued on every deploy, no cert-manager in cluster)
CERT_DIR=$(mktemp -d)
trap 'rm -rf "$CERT_DIR"' EXIT
openssl req -x509 -nodes -newkey rsa:2048 -days 1095 \
  -keyout "$CERT_DIR/tls.key" -out "$CERT_DIR/tls.crt" \
  -subj "/CN=myclock.internal" 2>/dev/null
kubectl create secret tls zai-clock-tls -n zai-clock \
  --cert="$CERT_DIR/tls.crt" --key="$CERT_DIR/tls.key" \
  --dry-run=client -o yaml | kubectl apply -f -

# site content straight from index.html (single source of truth)
kubectl create configmap zai-clock -n zai-clock \
  --from-file=index.html \
  --dry-run=client -o yaml | kubectl apply -f -

# deploy workloads
kubectl apply -f deployment.yaml -f service.yaml -f ingress.yaml
