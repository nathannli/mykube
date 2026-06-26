# Highflow Next Prometheus Exporter Setup

## Prerequisites

1. Install and configure `lm-sensors`.

   Verify the probe is detected:

   ```bash
   sensors
   ```

   The output should contain a section similar to:

   ```text
   highflownext-hid-3-1
   ```

2. Install Prometheus Node Exporter.

3. Ensure TCP port **9100** is open so Prometheus can scrape this machine.

---

## Configure Node Exporter

Create the textfile collector directory:

```bash
sudo mkdir -p /var/lib/node_exporter/textfile_collector
sudo chown <user>:<group> /var/lib/node_exporter/textfile_collector
```

Update your `node_exporter.service` to enable the textfile collector:

```ini
[Unit]
Description=Prometheus Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=<user>
Group=<group>
ExecStart=/path/to/node_exporter \
  --collector.textfile.directory=/var/lib/node_exporter/textfile_collector
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Reload and restart Node Exporter:

```bash
sudo systemctl daemon-reload
sudo systemctl restart node_exporter
```

Verify it is running:

```bash
systemctl status node_exporter
```

---

## Install the exporter script

Place the exporter script somewhere on the system (for example, `~/highflow-exporter.sh`) and make it executable:

```bash
chmod +x highflow-exporter.sh
```

Run it once:

```bash
./highflow-exporter.sh
```

Verify the metrics file was created:

```bash
cat /var/lib/node_exporter/textfile_collector/highflow.prom
```

Verify Node Exporter exposes the metrics:

```bash
curl localhost:9100/metrics | grep highflow
```

---

## Run the exporter automatically

Run the exporter periodically using either:

* a `systemd` timer (recommended), or
* `cron` (every minute).

Example cron entry:

```cron
* * * * * /path/to/highflow-exporter.sh >/dev/null 2>&1
```

---

## Configure Prometheus

On your Prometheus server, add this machine as a scrape target:

```yaml
scrape_configs:
  - job_name: highflow
    static_configs:
      - targets:
          - <hostname-or-ip>:9100
```

Reload Prometheus after updating the configuration.

---

## Available Metrics

The exporter publishes the following metrics:

* `highflow_flow_lph`
* `highflow_water_quality_percent`
* `highflow_conductivity_nscm`
* `highflow_coolant_temp_celsius`
* `highflow_dissipated_power_watts`

