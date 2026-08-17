# LabAI Fleet Monitoring Architecture

This document outlines the monitoring infrastructure for the UR Seismology Lab computational fleet. 
All monitoring is centralized via **Uptime Kuma**, which runs in a Docker container on the DMZ gateway (`urseismogate`).

## 1. Node Inventory & Monitoring Strategy
The lab utilizes 11 distinct monitor endpoints. Because of the strict University hardware firewall policies, the DMZ gateway (`urseismogate`) is physically prevented from initiating TCP Port 22 (SSH) connections inward to the trusted local network (`128.151.53.x`). 
Therefore, internal machines are monitored via **ICMP Ping**, while reverse-tunnels are monitored via their **HTTPS** endpoints.

| Name | Type | Target/URL | Purpose |
|------|------|------------|---------|
| **repovibranium** | Ping | `128.151.53.116` | Legacy Synology NAS |
| **ATOS-nas** | Ping | `10.17.7.230` | Core Lab NAS and Docker Registry host |
| **ATOS DSM (via Nginx)** | HTTP | `https://urseismogate.earth.rochester.edu/` | Synology DSM UI (Port 5001) tunnel |
| **inferencelocal** | Ping | `128.151.53.34` | ML Inference machine (Ollama host) |
| **Ollama API (Tunnel)** | HTTP | `https://urseismogate.earth.rochester.edu/ollama/` | Ollama GPU API Tunnel (secured by Basic Auth) |
| **terravibranium** | Ping | `128.151.53.167` | Computational node |
| **terravibranium-gpu** | Ping | `128.151.53.156` | Primary GPU Inference node (RTX 3090) |
| **terra4-classnode** | Ping | `128.151.53.100` | Student JupyterHub host |
| **JupyterHub (via Nginx)**| HTTP | `https://urseismogate.earth.rochester.edu/lab/` | Centralized JupyterHub student portal |
| **terra5-classnode** | Ping | `128.151.53.161` | Archival/lightweight compute node |
| **Local Mac / mothership** | Ping | `10.17.7.237` | Lab Director's iMac Pro |

## 2. Dashboard Access
The live status dashboard is securely accessible here:
👉 **[Uptime Kuma Status Dashboard](https://urseismogate.earth.rochester.edu/status/)**

*(Requires `urseismoadmin` Basic Authentication via Nginx)*

## 3. Disaster Recovery
If the Uptime Kuma SQLite database ever corrupts (throwing `Internal Server Error` or loop crashes):
1. SSH into `urseismogate`.
2. Delete the corrupted Docker volume: `sudo rm -rf /root/kuma/data/kuma.db*`.
3. Restart the container: `sudo docker restart uptime-kuma`.
4. Re-run the local python deployment script to instantly push all 11 monitors back into the clean database.
