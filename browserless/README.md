# Browserless

Personal local Browserless Chromium service. It binds only to this Mac mini at
`127.0.0.1:3000`; it is not reachable from the LAN or internet.

## Start

```sh
cd browserless
printf 'TOKEN=%s\n' "$(openssl rand -hex 32)" > .env
docker-compose up -d
```

Open `http://127.0.0.1:3000/docs?token=<TOKEN>` for local API docs.

## Connect

```js
import puppeteer from 'puppeteer-core';

const browser = await puppeteer.connect({
  browserWSEndpoint: 'ws://127.0.0.1:3000?token=<TOKEN>',
});
```

## Operate

```sh
docker-compose logs -f
docker-compose down
docker-compose pull && docker-compose up -d
```

`browserless.sh` provides same deployment without Compose.

`CONCURRENT=4`, `QUEUED=8`, and `TIMEOUT=30000` are intentionally conservative
starting limits. Increase only after observing normal workload memory and CPU.

Keep this service loopback-only. For remote use, use an authenticated private
network such as Tailscale or add a TLS reverse proxy; do not publish port 3000
directly.

Browserless is SSPL or commercially licensed. This deployment is intended for
personal projects only; review its license before any commercial or closed-source
CI use.
