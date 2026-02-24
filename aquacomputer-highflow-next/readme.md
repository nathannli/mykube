1) you need to use `sensors` to read the current stats of the probe
2) you need node_exporter for prometheus installed 
fsh ➜ brew list -l | rg node
drwxrwxr-x 3 nathan nathan 4096 Feb 23 20:22 node
drwxrwxr-x 3 nathan nathan 4096 Nov  4 09:39 node_exporter
3) u need to open port 9100
4) on the prometheus server, u scrape this device