https://grafana.com/docs/grafana/latest/setup-grafana/installation/kubernetes/

after deploying, use unbound dns to add a hosts to point mygrafana.internal to the rpi5 or rpi ip address

for the discord alerts, remember to add the suffic url like '/alert' to the end of the url


prometheus datasource:
http://prometheus-svc.prometheus:9090

contact points
webhook -> name: discord-general-webhook -> http://discord-general-channel-alert-bot-node-port.discord-bots:5000/alert
webhook -> name: poweroff-webhook -> http://kasa-flask-server-exporter.kasa-flask-server:9101/poweroff

alerts:
1) trigger poweroff when sum(pc ene) < 15
2) trigger discord msg when any pc uses > 220