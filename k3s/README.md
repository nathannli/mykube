# K3s server configuration

These files mirror `/etc/rancher/k3s/` on `rpi5`.

Install the tracked server configuration with:

```bash
sudo install -Dm644 config.yaml.d/10-api-san.yaml /etc/rancher/k3s/config.yaml.d/10-api-san.yaml
sudo systemctl restart k3s
```

Do not store K3s certificates or private keys in this repository.
