# JupyterHub Swarm Networking Post-Mortem

**Incident Date:** July 2026
**Issue:** Swarm single-user containers (`student-lab` and `student-lab-gpu`) timing out after 120 seconds with a `TimeoutError`.

## Root Cause Analysis
During an update to `jupyterhub_config.py` to increase the `Spawner.start_timeout` to 300 seconds, an outdated scratch configuration was accidentally pushed over the live production configuration on `terra4-classnode`.

The outdated configuration was missing three absolutely critical networking directives required for JupyterHub to route traffic over Docker Swarm overlay networks (`jupyter-swarm-net`) when placed behind an Nginx reverse proxy.

### 1. `c.JupyterHub.base_url = '/lab'`
Without this directive, JupyterHub expects all traffic to originate from the root domain `/`. However, the Nginx reverse proxy forwards traffic to JupyterHub via `/lab`. This mismatch caused an infinite `302 Redirect` loop (`/lab` -> `/hub/` -> `/lab/hub/...`) making the entire site inaccessible from the outside web.

### 2. `c.Spawner.port = 8888`
By default, DockerSpawner / SwarmSpawner requires the internal port of the single-user container to be explicitly defined. Because this line was deleted, JupyterHub defaulted to dynamically assigning port `0`. When JupyterHub attempted to establish a connection to verify the single-user server was awake, it fell back to the standard HTTP port (`80`). Since JupyterLab runs natively on `8888`, port `80` refused the connection, leading to the `TimeoutError`.

### 3. `c.Spawner.ip = '0.0.0.0'`
By default, the Jupyter server running inside the single-user container will bind securely to `127.0.0.1` (localhost). This means it refuses all external network requests. Setting `c.Spawner.ip = '0.0.0.0'` explicitly instructs the single-user container to listen on all interfaces, allowing JupyterHub to communicate with it across the `jupyter-swarm-net` overlay network.

## The Fix
All three directives were manually restored to the live `jupyterhub_config.py`.
The JupyterHub Docker container was then forcefully recreated (`docker compose up -d --force-recreate jupyterhub`) to immediately mount and apply the restored configuration. 

**Result:** The redirect loop was resolved, the port mappings successfully allowed Swarm container polling, and the CPU containers successfully utilized the 5-minute timeout window.
