#!/usr/bin/env bash

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

deploy_targets=(
  "discord-bots|deploy.sh"
  "flask-servers/govee-flask-server/kube-configs|deploy.sh"
  "flask-servers/kasa-flask-server/kube-configs|deploy.sh"
  "grafana|deploy.sh"
  "headlamp|deploy.sh"
  "homepage|deploy.sh"
  "metabase|deploy.sh"
  "prometheus|deploy.sh"
)

for target in "${deploy_targets[@]}"; do
  IFS="|" read -r folder script <<< "$target"
  script_path="$ROOT_DIR/$folder/$script"

  if [[ ! -f "$script_path" ]]; then
    echo "Skipping $folder: $script not found at $script_path" >&2
    continue
  fi

  echo "Running $folder/$script"

  (
    cd "$ROOT_DIR/$folder" || exit 1
    bash "./$script"
  ) || exit 1
done
