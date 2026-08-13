# Deploying Research to the Private Docker Registry

This guide covers how to package GitHub repositories into Docker images and deploy them to the lab's private registry (`urseismogate.earth.rochester.edu`). It also details the registry's Zero-Trust architecture, cost-saving benefits, and security configurations.

---

## 1. Registry Architecture & Cost Savings

The lab operates a **Zero-Trust DMZ Architecture** to host our private Docker registry without exposing internal storage to the public internet.

*   **The DMZ Gateway (`urseismogate`):** A public-facing Nginx reverse proxy that intercepts all incoming traffic.
*   **The Internal NAS (`ATOS-nas`):** A Synology NAS located securely behind the university firewall, hosting the actual Docker Registry.
*   **The Reverse Tunnel:** A persistent SSH tunnel routes traffic securely from the Nginx proxy directly to the internal NAS.

### Why not use AWS ECR or Docker Hub?
Hosting Massive Machine Learning and Seismology images (often 5GB - 20GB+) on commercial registries is extremely expensive:
*   **AWS ECR Storage:** ~$0.10 per GB/month (500GB = $600/year). Our NAS storage is **$0**.
*   **AWS Egress Fees:** ~$0.09 per GB (1TB bandwidth = $1,080/year). Our university bandwidth is **$0**.
*   **Docker Hub Teams:** ~$9 per user/month. Our internal registry supports unlimited users for **$0**.

By utilizing this architecture, the lab saves thousands of dollars annually while maintaining full control over proprietary code.

---

## 2. Packaging Docker Images Directly from GitHub

### Why Docker instead of `pip` or Git Clone?
While `pip install` and `git clone` are great for pulling Python code, they depend entirely on your host machine's operating system, C-compilers, and system libraries. Seismology and geophysics workflows often rely on complex, low-level Fortran/C libraries (e.g., SAC, GMT, GDAL) that are notoriously difficult to install natively and break easily. 
**Docker solves this** by packaging the *entire* operating system environment, libraries, and dependencies into an immutable container. If an image runs successfully on a student's laptop, it is guaranteed to run identically on the High-Performance Compute nodes without any "dependency hell."

### Building Directly via URL
You **do not** need to clone a repository locally to build its Docker image. Docker natively supports building directly from a `.git` URL, and the registry's proxy handles the routing transparently.

### Example: Building a Public Geophysics Repo
*Note: This is an example. The direct URL build method below works seamlessly for **public** repositories. If you are building a private repository, it is generally easier to `git clone` it locally (which uses your SSH keys) and run `docker build .` from inside the cloned directory.*

Assuming the public repository has a `Dockerfile` in its root directory, run the following commands:

```bash
# 1. Build the image directly from the GitHub URL (append .git!)
docker build -t urseismogate.earth.rochester.edu/gsm_forward_rheology:latest https://github.com/PSU-Geofluids-Lab/GSM_Forward_Rheology.git

# 2. Push it securely through the DMZ to our internal NAS
docker push urseismogate.earth.rochester.edu/gsm_forward_rheology:latest
```

> [!TIP]
> **No Dockerfile? Use repo2docker!**
> [jupyter-repo2docker](https://repo2docker.readthedocs.io/en/latest/) is a powerful command-line utility. If a repository doesn't have a `Dockerfile`, you can run `jupyter-repo2docker https://github.com/user/repo`. It automatically scans the repo (e.g., for `requirements.txt` or `environment.yml`), detects the language, and builds a fully functioning Jupyter Docker image without you having to write a single line of Docker code!

---

## 3. Registry Security & Authentication

To prevent unauthorized users from pushing or overwriting lab images, the `/v2/` registry endpoint on `urseismogate` is protected by Nginx Basic Authentication. 

*   **Pulling (GET):** Open to the public/lab members (no authentication required).
*   **Pushing (POST/PUT):** Restricted to authorized lab members. You must run `docker login urseismogate.earth.rochester.edu` first.

### Managing Authorized Users
User credentials are managed via the standard Apache `htpasswd` utility on the gateway. If you need to add a new lab member, log into the gateway and run:

```bash
# Ensure the utility is installed
sudo apt-get install -y apache2-utils

# Add a new user (You will be prompted to set their password)
sudo htpasswd /etc/nginx/.htpasswd new_username
```

### Nginx Security Configuration (The `limit_except` block)
If you ever need to rebuild the proxy, ensure the `/v2/` location block in `/etc/nginx/sites-available/synology-proxy` includes the following security restriction:

```nginx
    location /v2/ {
        # Require password ONLY for Pushing/Uploading (POST, PUT, DELETE)
        limit_except GET {
            auth_basic "Restricted Lab Registry";
            auth_basic_user_file /etc/nginx/.htpasswd;
        }

        # Route traffic to the ATOS NAS Registry reverse tunnel
        proxy_pass http://127.0.0.1:55005;
        
        # ... standard proxy headers ...
    }
```

> [!CAUTION]
> **Configuration Rollbacks:** Never run `systemctl restart nginx` manually after edits. Always use the lab's `sudo bash ~/apply_nginx.sh` script to ensure automatic backups are created before the daemon reloads.
