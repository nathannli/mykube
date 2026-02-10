# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **personal Kubernetes-based home automation and smart device monitoring system**. It runs on K3s (lightweight Kubernetes) and manages a collection of containerized applications that monitor IoT smart devices (TP-Link Kasa smart plugs, Govee devices) and provide alerting, analytics, and visualization through a complete observability stack.

## Architecture

### Core Components

The repository follows a **microservices architecture** with independent containerized applications:

- **Flask Servers**: REST API servers that expose Prometheus metrics
  - `kasa-flask-server/`: Monitors TP-Link Kasa smart plugs (power consumption, device state)
  - `govee-flask-server/`: Monitors Govee IoT devices (smart lights, sensors)

- **Discord Bots**: User-facing bots for alerts and queries
  - `alert-bot/`: Sends alerts to Discord channels
  - `energy-bot/`: Provides Discord commands (e.g., `/getusage`) for power consumption queries

- **Observability Stack**:
  - `prometheus/`: Time-series metrics database (ConfigMap-based configuration)
  - `grafana/`: Visualization dashboards
  - `metabase/`: Business intelligence and analytics (PostgreSQL backend)

- **Infrastructure**:
  - `traefik/`: Reverse proxy and ingress controller
  - `homepage/`: Personal dashboard aggregator (ghcr.io/gethomepage/homepage)
  - `kubernetes-dashboard/`: K8s cluster management UI
  - `postgres/`: PostgreSQL database (persistent data for Metabase, finance tracking)

- **Operations**:
  - `cron-scripts/`: Automated maintenance (PostgreSQL backups)
  - `bin/`: Cluster utilities (ReplicaSet cleanup)
  - `system-upgrade/`: K3s automated upgrade configuration

### Data Flow

```
Smart Devices (Kasa, Govee)
    ↓
Flask REST APIs → Prometheus metrics (port 9101)
    ↓
Prometheus (scrapes every 300s, stores in PVC)
    ↓
Grafana (visualization) + Metabase (BI analytics)
    ↓
Discord Bots (alerts, user queries)
```

### Technology Stack

- **Orchestration**: K3s (lightweight Kubernetes)
- **Containerization**: Docker with multi-platform builds (linux/amd64, linux/arm64)
- **Web Framework**: Flask (Python)
- **Device Libraries**: python-kasa, requests
- **Bots**: discord.py
- **Metrics**: prometheus_client library, Prometheus server
- **Database**: PostgreSQL (external)
- **Config Management**: Kubernetes ConfigMaps and Secrets

### Network Configuration

- **Home Local Network**: `10.195.1.0/24` (custom IP range configured by user)
  - Smart devices (TP-Link Kasa plugs, Govee devices) are on this network
  - K3s cluster must have network access to this range for device communication
  - Flask servers connect to devices on this network via IPs like `10.195.1.226:9999`

## Common Development Commands

### Building and Deploying Container Images

All containerized applications follow this pattern:

```bash
# Build and push multi-platform image (amd64 + arm64)
cd <component>/docker-app/
./dockerbuild.sh <version>

# Example:
cd flask-servers/kasa-flask-server/docker-app/
./dockerbuild.sh v1.0.0
```

The `dockerbuild.sh` script uses `docker buildx` to build for both `linux/amd64` and `linux/arm64` and pushes to the `nathannnli/<image>:<version>` Docker Hub registry.

### Deploying to Kubernetes

```bash
# Apply all manifests for a component
kubectl apply -f <component>/kube-configs/

# Check deployment status
kubectl get deployments -n <namespace>
kubectl describe deployment <name> -n <namespace>
kubectl logs -f deployment/<name> -n <namespace>

# Example - deploy kasa-flask-server:
kubectl apply -f flask-servers/kasa-flask-server/kube-configs/
```

### Testing Python Applications

Each Flask server has `requirements.txt` in `docker-app/`:

```bash
# Install dependencies locally
cd <component>/docker-app/
pip install -r requirements.txt

# Run the Flask app
python flask-app.py

# For Discord bots
python <bot-name>.py
```

### Managing Kubernetes Resources

```bash
# View all resources
kubectl get all -n <namespace>

# Port-forward to access services locally
kubectl port-forward -n <namespace> service/<service-name> 8000:8000

# Example - access Prometheus (normally on port 9090):
kubectl port-forward -n prometheus service/prometheus 9090:9090

# View logs
kubectl logs -f pod/<pod-name> -n <namespace>
```

### Database Operations

```bash
# Backup PostgreSQL (automated by cron-scripts)
bash cron-scripts/pg-backup.sh

# The script backs up two databases: `finance` and `parents_finance`
# Backups are uploaded to FTP (10.0.0.18) with 60-day retention
```

### Cleanup and Maintenance

```bash
# Remove expired ReplicaSets (reduces cluster clutter)
bash bin/delete_expired_replicaset_sets.sh
```

## Kubernetes Configuration Patterns

Each application follows a standard directory structure:

```
<component>/
├── docker-app/
│   ├── Dockerfile
│   ├── dockerbuild.sh
│   ├── flask-app.py (or bot-name.py)
│   ├── config.py
│   ├── requirements.txt
│   └── my_logger.py (optional)
└── kube-configs/
    ├── deployment.yml
    ├── service-*.yml
    ├── configmap.yml
    └── secret.yml (not in repo - K8s native)
```

### Key K8s Configuration Details

**Prometheus Configuration** (`prometheus/configmap.yml`):
- Scrape interval: 300 seconds (5 minutes)
- Scrape timeout: 60 seconds
- Targets: Kasa exporter (port 9101), Govee exporter (port 9101), external hardware node exporters
- Uses in-cluster DNS (e.g., `kasa-flask-server-exporter.kasa-flask-server.svc.cluster.local`)

**Deployment Patterns**:
- ClusterIP Services for internal communication
- NodePort Services for external access (e.g., Prometheus on 31090, Kasa exporter on 30101)
- Persistent Volumes for stateful data (Prometheus TSDB)
- HostPath volumes for local mounts (homepage images)
- Secrets for sensitive credentials (device passwords, API tokens)
- ConfigMaps for non-sensitive configuration (device IPs, endpoints)

## Git Workflow and Versioning

This project uses **Conventional Commits** with **git-cliff** for automated changelog generation (see `cliff.toml`).

### Commit Message Format

```
<type>(<scope>): <message>

# Types: feat, fix, doc, perf, refactor, style, test, chore, ci
# Scopes: kasa, govee, prometheus, discord, etc.
# Breaking changes should include "BREAKING CHANGE:" in body
```

### Changelog Generation

```bash
# Generate CHANGELOG.md (uses Conventional Commits)
git cliff -o CHANGELOG.md

# Commit categories:
# 🚀 Features (feat)
# 🐛 Bug Fixes (fix)
# 🚜 Refactor (refactor)
# 📚 Documentation (doc)
# ⚡ Performance (perf)
# 🎨 Styling (style)
# 🧪 Testing (test)
# ⚙️ Miscellaneous Tasks (chore, ci)
# 🛡️ Security (body contains "security")
```

## Important Files Reference

- `cliff.toml`: Git-cliff configuration for changelog generation
- `prometheus/configmap.yml`: Prometheus scrape targets and configuration
- `CHANGELOG.md`: Auto-generated changelog following git-cliff template
- `README.md`: Basic K3s setup instructions
- Each `flask-servers/*/docker-app/requirements.txt`: Python dependencies for that service

## Debugging Tips

1. **Check service connectivity**:
   ```bash
   kubectl exec -it pod/<pod-name> -n <namespace> -- curl http://service-name:port
   ```

2. **View Prometheus targets**:
   - Port-forward to Prometheus (9090) and visit `/api/v1/targets`

3. **Check ConfigMap values**:
   ```bash
   kubectl get configmap <name> -n <namespace> -o yaml
   ```

4. **Monitor logs in real-time**:
   ```bash
   kubectl logs -f deployment/<name> -n <namespace>
   ```

5. **Inspect application config**:
   - Flask servers use `config.py` for configuration
   - Check ConfigMaps for externalized settings (device IPs, endpoints)
