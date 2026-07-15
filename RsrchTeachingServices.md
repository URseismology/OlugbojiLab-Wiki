# Research & Teaching Services Architecture

This document provides a comprehensive overview of the backend hardware, network topology, and configuration files that power the Olugboji Lab's research and teaching infrastructure. It is designed for System Administrators and AI Agents to track operational capabilities, troubleshoot issues, and manage deployments.

## 1. Global Network Topology (Zero-Trust DMZ)

Our lab utilizes a highly secure, encrypted pipeline extending from the public internet into the protected university subnet.

### The Gateway: `urseismogate`
*   **Hostname:** `urseismogate.earth.rochester.edu`
*   **Role:** The public-facing DMZ server.
*   **Architecture:** Runs an `Nginx` reverse proxy. It listens on ports 80/443 and routes external traffic into the internal lab nodes via strict URL path matching (e.g., `/jupyter`, `/v2/`).

### The Storage Hub: `ATOS-nas`
*   **Role:** The central 160TB Synology NAS.
*   **Services Hosted:**
    *   **Private Docker Registry:** Hosted via Container Manager on port `5005`.
    *   **Student Workspaces:** Raw file storage mapped into JupyterHub environments.
*   **Networking:** Maintains a persistent reverse SSH tunnel to `urseismogate`, pushing its internal ports (like 5005) to the DMZ (e.g., `55005`), allowing the gateway to serve NAS applications to the internet without exposing the NAS directly.

---

## 2. The Computational Nodes

### The Student Node: `terra4-classnode`
*   **IP Address:** `128.151.53.100`
*   **Role:** The primary CPU and UI hosting server for students.
*   **Services Hosted:** 
    *   **JupyterHub Server:** Runs on local port `8001`. Spawns isolated Docker containers for each student.
*   **Configuration Files:**
    *   *Docker Compose:* `~/jupyterhub_server/docker-compose.yml` (Deploys the hub)
    *   *Hub Config:* `~/jupyterhub_server/jupyterhub_config.py` (Manages student spawning and NAS volume mounting)

### The Socratic AI Node: `terravibranium-gpu`
*   **IP Address:** `128.151.53.156`
*   **Role:** A dedicated GPU machine explicitly used for **teaching, learning, coding, and small debugs**.
    > [!IMPORTANT]
    > **Hardware Separation:** This machine is completely separate from `inferencelocal` (the dual-GPU massive inference server used for heavy research). `terravibranium-gpu` is sized specifically for student interactive workloads.
*   **Services Hosted:**
    *   **Ollama AI Microservice:** Runs an RTX 3090 GPU via the NVIDIA Container Toolkit.
    *   **Deployed Model:** `coding-assistant` (a custom Socratic compilation of `deepseek-coder-v2`).
*   **Networking Architecture:** The Ollama API is exposed natively on the internal subnet at `http://128.151.53.156:11434`. It accepts direct traffic from `terra4-classnode` without requiring an `autossh` tunnel.
*   **Configuration Files:**
    *   *NVIDIA CDI Spec:* `/etc/cdi/nvidia.yaml` (Manages GPU passthrough to Docker)
    *   *Docker Compose:* `docker-compose.yml` (Spawns the Ollama engine mapping `11434:11434`)
    *   *Model Blueprint:* `Modelfile` (Contains the Socratic system prompt that forbids giving direct answers)

---

## 3. Future Extensions (Public Exposure)

Currently, the AI backend and JupyterHub are restricted to the internal network. We have planned extensions to securely expose both **Architecture A (Remote GPU Spawning)** and **Architecture B (API Tunneling)** to the outside world using the `urseismogate` DMZ:

1.  **Architecture B (Socratic Microservice Exposure):**
    *   We will configure an `autossh` reverse tunnel from `terravibranium-gpu` to `urseismogate`, mapping port `11434` to `localhost:55003` on the DMZ.
    *   An Nginx routing block will expose `https://urseismogate.earth.rochester.edu/ai-api` securely, allowing authenticated external clients to query the Socratic coding assistant from anywhere.

2.  **Architecture A (Full PyTorch GPU Remote Spawning):**
    *   For mature students needing raw GPU access, we will configure JupyterHub (or a dedicated secondary hub) to spawn remote Docker Swarm instances directly onto `terravibranium-gpu` rather than `terra4`.
    *   We will then map the JupyterHub UI itself from `terra4` to the DMZ using an `autossh` tunnel (mapping `8001` to `55002`).
    *   Nginx will route `https://urseismogate.earth.rochester.edu/jupyter` to this tunnel, providing seamless external access to heavy PyTorch notebook environments.
