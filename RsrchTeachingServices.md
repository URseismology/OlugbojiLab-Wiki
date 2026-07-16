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
        > [!NOTE]
        > **Alignment Tax & HCI Considerations:** Because this model is significantly smaller than frontier web models, applying a strict "Socratic" prompt (forcing it to act as a digital TA without giving direct answers) imposes an *Alignment Tax*. The model spends heavily on formatting and persona adherence, which can occasionally degrade its mathematical reasoning on complex multidimensional problems (e.g., struggling to conceptualize 4D space). Students are warned to use the AI as an advanced autocomplete and brainstorming peer rather than an infallible mathematical engine.
*   **Networking Architecture:** The Ollama API is exposed natively on the internal subnet at `http://128.151.53.156:11434`. It accepts direct traffic from `terra4-classnode` without requiring an `autossh` tunnel.
*   **Configuration Files:**
    *   *NVIDIA CDI Spec:* `/etc/cdi/nvidia.yaml` (Manages GPU passthrough to Docker)
    *   *Docker Compose:* `docker-compose.yml` (Spawns the Ollama engine mapping `11434:11434`)
    *   *Model Blueprint:* `Modelfile` (Contains the Socratic system prompt that forbids giving direct answers)

---

## 3. Deployed Extensions (DMZ Reverse Proxy)

We have successfully mapped the internal JupyterHub environment (`terra4-classnode`) to the public internet via the DMZ gateway.

### Architecture A (Swarm JupyterHub Exposure):
*   **The Tunnel:** A persistent `systemd` user service (`jupyter-tunnel.service`) running on `terra4-classnode` uses `autossh` to forward local port `8001` to remote port `55008` on the gateway.
*   **The Gateway:** `urseismogate` runs Nginx, intercepting traffic to `https://urseismogate.earth.rochester.edu/lab/` and routing it into the `55008` tunnel.
*   **JupyterHub Config:** JupyterHub is configured with `c.JupyterHub.base_url = '/lab'` so internal routing seamlessly aligns with the Nginx proxy path.

### Nginx Installation & Rollback Procedure
Because `urseismogate` is highly sensitive, we do not require passwordless `sudo` access to deploy changes. Instead, we use an automated script:
1.  **Installation Script:** `~/apply_nginx.sh` is uploaded to `urseismoadmin-m2@urseismogate`.
2.  **Backup Mechanism:** When executed via `sudo bash ~/apply_nginx.sh`, the script automatically creates a timestamped backup of the live configuration (e.g., `/etc/nginx/sites-available/synology-proxy.backup_2026-07-16_09-04-37`) before injecting the new proxy settings and restarting the daemon.
3.  **Emergency Rollback:** To restore a previous configuration, an administrator simply logs into the gateway and runs:
    ```bash
    sudo cp /etc/nginx/sites-available/synology-proxy.backup_YYYY-MM-DD_HH-MM-SS /etc/nginx/sites-available/synology-proxy
    sudo systemctl restart nginx
    ```

---

## 4. JupyterHub Swarm Integration & Stabilization

We utilize Docker Swarm to schedule `jupyterhub-singleuser` containers across multiple physical nodes (CPU vs GPU). Two critical stabilization fixes have been permanently applied to ensure this architecture functions seamlessly:

### Socratic Identity Override (Dynamic Patching)
The `jupyter-ai` library ships with a hardcoded `Jupyternaut` system prompt that ignores the local `Modelfile` prompt logic. To enforce our custom "Socratic Coding Assistant for Dr. Olugboji's Planetary Imaging and Earth Hazards Lab" persona, a dynamic Python patch is baked directly into `Dockerfile.student` and `Dockerfile.student-gpu`.
*   **The Mechanism:** The `Dockerfile` executes a python one-liner during the build process that uses `import jupyter_ai_magics.base_provider as bp; file_path=bp.__file__.replace('.pyc', '.py')` to dynamically locate the system prompt code, regardless of the base container's Python version (3.11, 3.13, etc.).
*   **Deployment Note:** The GPU image must be built directly on `urseismoadmin-Super-Server` to ensure the local Swarm worker node caches the updated image without requiring a full private registry push.
*   **Strict Socratic Mode:** If you wish to escalate the AI's strictness so that it **refuses** to provide copy-paste code blocks and forces students to solve their own bugs, replace your active `Dockerfile.student` with the provided template: [scripts/Dockerfile.student.strict_socratic](scripts/Dockerfile.student.strict_socratic) and trigger a Swarm rebuild.

### Docker Swarm Networking & Spawner Timeouts
Because the Swarm manager (`terra4-classnode`) must communicate with single-user containers distributed across external worker nodes over an overlay network (`jupyter-swarm-net`), three critical `jupyterhub_config.py` parameters are strictly enforced:
*   `c.Spawner.start_timeout = 300`: Extended from the default 60s to 300s to allow massive multi-gigabyte GPU images sufficient time to unpack and mount on the remote nodes.
*   `c.Spawner.port = 8888`: Ensures Docker Swarm explicitly maps the internal container port to `8888` rather than dynamically assigning an unreachable random port or defaulting to port 80.
*   `c.Spawner.ip = '0.0.0.0'`: Crucial for overlay network routing. If missing, the Jupyter server binds natively to `127.0.0.1` (localhost) inside the container, completely refusing all traffic from the Swarm manager. Setting it to `0.0.0.0` ensures the socket listens across the entire `jupyter-swarm-net` interface.
