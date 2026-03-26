https://grafana.com/docs/grafana/latest/setup-grafana/installation/kubernetes/

after deploying, use unbound dns to add a hosts to point mygrafana.internal to the rpi5 or rpi ip address

tls:
1. issue a certificate whose SAN includes `mygrafana.internal`
    ```
    brew install mkcert nss
    mkcert -install
    cd /Volumes/data/personal/mykube/grafana
    mkcert mygrafana.internal
    ```
    Created a new certificate valid for the following names 📜
    - "mygrafana.internal"
    The certificate is at "./mygrafana.internal.pem" and the key at "./mygrafana.internal-key.pem" ✅
    It will expire on 26 June 2028 🗓
2. make sure the issuing CA is trusted by your Mac/browser
3. copy `tls-secret.example.yaml` to `tls-secret.yaml`
4. replace the placeholder `tls.crt` and `tls.key` values in `tls-secret.yaml`
    ```
    kubectl -n grafana create secret tls grafana-tls \
    --cert=mygrafana.internal.pem \
    --key=mygrafana.internal-key.pem \
    --dry-run=client -o yaml > tls-secret.yaml
    ```
5. deploy with `kubectl apply -f ./grafana`

notes:
- the secret name must stay `grafana-tls` to match `ingress.yaml`
- if the certificate chain includes intermediates, include the full chain in `tls.crt`
- without this secret, Traefik falls back to its default self-signed certificate

for the discord alerts, remember to add the suffic url like '/alert' to the end of the url


prometheus datasource:
http://prometheus-svc.prometheus:9090

contact points
webhook -> name: discord-general-webhook -> http://discord-general-channel-alert-bot-node-port.discord-bots:5000/alert
webhook -> name: poweroff-webhook -> http://kasa-flask-server-exporter.kasa-flask-server:9101/poweroff

alerts:
1) trigger poweroff when sum(pc ene) < 15
2) trigger discord msg when any pc uses > 220
