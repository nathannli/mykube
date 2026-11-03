# AquaComputer high flow next Prometheus exporter

This project exports AquaComputer High Flow NEXT sensor readings as Prometheus metrics. It uses `lm-sensors` to read the USB HID device, a script to write a Node Exporter textfile-collector file, and a systemd timer to refresh metrics every minute.

## Requirements

- Linux with systemd
- AquaComputer High Flow NEXT connected by USB
- `lm-sensors`, `jq`, `curl`, and `systemd`
- Prometheus Node Exporter
- Root access for package installation and systemd setup

Commands below assume the checkout is `/home/nathan/data/personal/mykube/aquacomputer-highflow-next` and the service account is `nathan`. Change `REPO` and `SERVICE_USER` if needed.

## 1. Install and verify sensor tools

Install `lm-sensors`, `jq`, and `curl` with the system package manager. Examples:

```bash
# Debian or Ubuntu
sudo apt-get update
sudo apt-get install -y lm-sensors jq curl

# Fedora
sudo dnf install -y lm_sensors jq curl
```

Confirm that `sensors` detects the device and that its name matches the script's expected `highflownext-hid-3-3` key:

```bash
sensors
sensors -j | jq -e '."highflownext-hid-3-3"'
```

If the second command fails, inspect the JSON device keys and update the key in `highflow-exporter.sh` to match the detected device. Do not continue until readings are available.

## 2. Install Node Exporter

Install the official Prometheus Node Exporter binary for the host's OS and architecture from <https://github.com/prometheus/node_exporter/releases>. Use the current stable release and verify its published checksum before installing. Place the binary at:

```text
/usr/local/bin/node_exporter
```

Verify it:

```bash
/usr/local/bin/node_exporter --version
```

If Node Exporter is already installed as a system service, keep that installation and edit its unit to include the textfile collector flag in step 3. Do not create a second Node Exporter service.

## 3. Configure Node Exporter textfile collector

Set the values used by the remaining commands:

```bash
REPO=/home/nathan/data/personal/mykube/aquacomputer-highflow-next
SERVICE_USER=nathan
SERVICE_GROUP=$(id -gn "$SERVICE_USER")
```

Create the collector directory and grant the exporter account write access:

```bash
sudo install -d -o "$SERVICE_USER" -g "$SERVICE_GROUP" -m 0755 /var/lib/node_exporter/textfile_collector
```

Create `/etc/systemd/system/node_exporter.service` with this content. If an existing unit has other required settings, preserve them and add the `--collector.textfile.directory` argument to its `ExecStart` instead of replacing the unit blindly.

```ini
[Unit]
Description=Prometheus Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=nathan
Group=nathan
ExecStart=/usr/local/bin/node_exporter --collector.textfile.directory=/var/lib/node_exporter/textfile_collector
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

If `SERVICE_USER` is not `nathan`, replace both `User` and `Group` values with the selected account and its primary group. Then enable and start Node Exporter:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now node_exporter.service
systemctl is-enabled node_exporter.service
systemctl is-active node_exporter.service
```

Node Exporter listens on TCP port `9100` by default. Restrict firewall access to the Prometheus server or trusted monitoring network; do not expose this endpoint publicly.

## 4. Install and test the High Flow exporter

Install the script at the project path and ensure it is executable and writable by `SERVICE_USER`:

```bash
sudo chown "$SERVICE_USER:$SERVICE_GROUP" "$REPO/highflow-exporter.sh"
chmod 0755 "$REPO/highflow-exporter.sh"
```

Run it as the service account so permissions match its scheduled execution:

```bash
sudo -u "$SERVICE_USER" "$REPO/highflow-exporter.sh"
```

Check the generated file and verify Node Exporter serves all five metrics:

```bash
cat /var/lib/node_exporter/textfile_collector/highflow.prom
curl --fail --silent http://127.0.0.1:9100/metrics | grep '^highflow_'
```

Expected metric names:

- `highflow_flow_lph`
- `highflow_water_quality_percent`
- `highflow_conductivity_nscm`
- `highflow_coolant_temp_celsius`
- `highflow_dissipated_power_watts`

Do not proceed if the script fails, the metrics file is missing, or the metrics endpoint does not return these names. Check `sensors -j`, `jq`, file ownership, and the Node Exporter journal.

## 5. Schedule metric refresh with systemd

Create `/etc/systemd/system/highflow-exporter.service`:

```ini
[Unit]
Description=Write AquaComputer High Flow NEXT Prometheus metrics
After=node_exporter.service

[Service]
Type=oneshot
User=nathan
Group=nathan
ExecStart=/home/nathan/data/personal/mykube/aquacomputer-highflow-next/highflow-exporter.sh
```

Create `/etc/systemd/system/highflow-exporter.timer`:

```ini
[Unit]
Description=Refresh AquaComputer High Flow NEXT metrics every minute

[Timer]
OnBootSec=30s
OnUnitActiveSec=60s
Unit=highflow-exporter.service

[Install]
WantedBy=timers.target
```

If the checkout path or account differs, update `ExecStart`, `User`, and `Group`. Enable the timer and run the service once:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now highflow-exporter.timer
sudo systemctl start highflow-exporter.service
```

Verify service and timer:

```bash
systemctl status highflow-exporter.service --no-pager
systemctl status highflow-exporter.timer --no-pager
systemctl list-timers highflow-exporter.timer --no-pager
journalctl -u highflow-exporter.service -n 20 --no-pager
```

## 6. Configure Prometheus scraping

On the Prometheus server, add the host to `scrape_configs` using a reachable address:

```yaml
scrape_configs:
  - job_name: highflow
    static_configs:
      - targets:
          - <host-or-ip>:9100
```

Allow TCP `9100` from the Prometheus server, validate the Prometheus configuration, and reload Prometheus. Confirm the target is `UP` and the `highflow_*` metrics appear.

## Troubleshooting

- **No sensor JSON key:** Check USB connection and `sensors -j`; update the key in the script only if the detected device key differs.
- **Permission denied writing `highflow.prom`:** Ensure `/var/lib/node_exporter/textfile_collector` is owned by the configured service account and writable by it.
- **Exporter script fails:** Inspect `journalctl -u highflow-exporter.service`; verify `sensors`, `jq`, and sensor JSON.
- **Metrics missing from Node Exporter:** Check its `ExecStart` includes `--collector.textfile.directory=/var/lib/node_exporter/textfile_collector`, then inspect `systemctl status node_exporter` and `journalctl -u node_exporter`.
- **Prometheus target down:** Check Node Exporter is active, listening on port `9100`, reachable from Prometheus, and permitted by the host firewall.
