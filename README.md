# Termix Headscale ↔ Tailscale API Bridge

Translates Headscale's `/api/v1/node` API into Tailscale API v2 format (`/tailnet/-/devices?fields=all`) so Termix's Tailscale plugin can work with a self-hosted Headscale instance.

## Why?
Termix expects Tailscale API v2 (`GET /tailnet/-/devices?fields=all` with `Authorization: Bearer <api-key>`). Headscale exposes `GET /api/v1/node` instead. This small adapter translates the response to the expected shape.

## Mapping
- `id` ← `node.id`
- `name` ← `node.name` (or `node.givenName` fallback)
- `hostname` ← `node.givenName` or `node.name`
- `addresses` ← `node.ipAddresses` (array)
- `os` ← `""` (not exposed by Headscale in this form)
- `lastSeen` ← `node.lastSeen`
- `online` ← `node.online`

## Usage

### Option 1: Add to existing Termix docker-compose (recommended)
Copy `adapter.py` to the same directory as your `docker-compose.yml` (e.g. `/opt/termix/`), then add:

```yaml
  hs2ts-adapter:
    image: python:3-slim
    container_name: hs2ts-adapter
    restart: unless-stopped
    working_dir: /app
    volumes:
      - ./adapter.py:/app/adapter.py:ro
    command: ["python3", "/app/adapter.py"]
    ports:
      - "8091:8091"
    networks:
      - termix-net
```

Start it: `docker compose up -d hs2ts-adapter`

### Option 2: Standalone (Docker)
```bash
docker build -t hs2ts-adapter .
docker run -d --name hs2ts-adapter -p 8091:8091 hs2ts-adapter
```

## Configure Termix
In Termix → Tailscale plugin settings:
- `apiBaseUrl`: `http://<termix-host>:8091` (or `http://hs2ts-adapter:8091` if on the same Docker network)
- `apiKey`: your Headscale API key (use the full key; do **not** truncate)

Note: The adapter forwards the Bearer token to Headscale as-is (`Authorization: Bearer <key>`).

## Configuration via environment
- `HEADSCALE_API` (default: `https://<your-headscale>/api/v1/node`) – Headscale `/api/v1/node` endpoint
- `LISTEN_HOST` (default: `0.0.0.0`)
- `LISTEN_PORT` (default: `8091`)

## Security
- Never commit real API keys to git. Use placeholders like `<KEY36>` in docs.
- The adapter binds to `0.0.0.0` by default; restrict to Docker network in production if not exposing publicly.
- Uses HTTPS to reach Headscale by default.

## License
MIT
