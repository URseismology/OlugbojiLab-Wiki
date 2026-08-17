# Nginx Routing, Security & Analytics Architecture

This document maps out the Nginx perimeter configurations deployed on the DMZ gateway (`urseismogate.earth.rochester.edu`).
Because `urseismogate` is the only server exposed through the University hardware firewall (Ports 80/443), it acts as a reverse proxy for all internal computational resources.

## 1. Reverse Proxy Endpoints
All routes are secured by Let's Encrypt SSL.

| Endpoint | Target | Security | Description |
|----------|--------|----------|-------------|
| `/` | `127.0.0.1:5001` | Public | Proxies the primary ATOS Synology DSM portal via an Autossh tunnel. |
| `/lab/` | `127.0.0.1:5005` | JupyterHub Auth | Proxies the JupyterHub portal for students, tunneling back to `terra4-classnode`. |
| `/v2/` | `127.0.0.1:55005` | Basic Auth (Push) | Proxies the Docker Registry API. Pulling (GET) is completely public, but Pushing images requires `urseismoadmin` credentials. |
| `/registry/`| `127.0.0.1:8080` | Basic Auth | Hosts the graphical Docker Registry UI so lab members can visually browse images, tags, and sizes. |
| `/ollama/` | `127.0.0.1:11434`| Basic Auth | Proxies the ML Inference API back to `inferencelocal`. Secured by `.htpasswd` to prevent unauthorized GPU hijacking. |
| `/spec2vec`| HTTP 301 Redirect| N/A | Redirects traffic directly to `https://spec2vec.mintlify.site/`. (A redirect is used because Mintlify explicitly blocks iframe masking via `x-frame-options: DENY`). |

## 2. Real-Time Analytics Tracking
To generate quantitative traffic logs for funding agencies, we do not rely on 3rd-party SaaS trackers. Instead, all Nginx traffic is analyzed natively on the gateway.

### GoAccess Dashboard
- **Location:** `https://urseismogate.earth.rochester.edu/analytics/`
- **Security:** `urseismoadmin` Basic Authentication.
- **How it Works:** A system cron job runs `goaccess` every 60 seconds against `/var/log/nginx/access.log`.
- **Bot Filtering:** The automated Uptime Kuma ping monitors (which generate ~3,800 requests/day) and static website assets (CSS/JS) are strictly filtered out before parsing (`grep -v 'Uptime-Kuma' ... --ignore-statics=req`). This guarantees that the dashboard ONLY shows genuine, human traffic hitting the core endpoints for your grant reports.
