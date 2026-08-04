# LabAI CodeSearch Ecosystem Architecture

This document outlines the architecture of the semantic search and retrieval ecosystem for the Olugboji Lab's massive codebase. This system allows AI agents (like DeepSeek via Open WebUI) and human users (via Streamlit) to intelligently query over 85,000 code files across the lab's storage infrastructure.

## 1. Core Components

The architecture is built on a distributed, three-tier model bridging the lab's various network zones.

### A. The Data Pipeline (SQLite & ChromaDB)
*   **`roverBckUp.py` & `roverBckUp_custom.py`**: HPC data scrapers that compress and push raw project files from student machines (e.g., `10.5.246.255`) to the central NAS (`ATOS-nas`).
*   **`AIBot-WikiCrafter.py`**: A background daemon on `inferencelocal` that detects new tarballs, extracts them, and uses local LLMs to generate high-level semantic summaries of every code file. These are stored in `AIBot-WikiCrafter_state.db` (SQLite).
*   **`AIBot-KnowledgeIndexer.py`**: The vectorization engine. It reads the SQLite database and uses Ollama (`nomic-embed-text`) to generate dense embeddings, storing them in a local **ChromaDB** instance on `inferencelocal`.

### B. The User Interfaces
*   **Streamlit Dashboard (`AIBot-CodeSearch-App.py`)**: A human-friendly web interface hosted on `inferencelocal` (Port 8501). It provides real-time semantic searching and features a dynamic `.tar.gz` extractor to preview source code in-memory without permanently unpacking gigabytes of data.
*   **Open WebUI Integration (`openwebui_tool.py`)**: A custom Python tool injected into the lab's Open WebUI instance. This empowers the chat LLMs to query the codebase autonomously before generating code.
*   **`scaffold_project.py`**: A CLI utility to bootstrap new Git repositories directly from the codebase tarballs.

### C. The HTTP Bridge
Because Open WebUI operates in isolated Docker containers, it cannot natively read the host's ChromaDB directory. 
*   **`AIBot-CodeSearch-API.py`**: A FastAPI backend running on `inferencelocal` that wraps the ChromaDB instance and exposes it via HTTP, acting as the bridge for the `openwebui_tool.py`.

---

## 2. Network Topology & Reverse Proxy

To make the Streamlit dashboard accessible securely from the public internet, we utilize the DMZ Gateway (`urseismogate`).

1.  **The Autossh Tunnel (`codesearch-tunnel.service`)**: Runs on `inferencelocal`. It bridges the local Streamlit port `8501` to a remote port `55010` on `urseismogate`.
2.  **The Nginx Proxy (`apply_nginx_codesearch.sh`)**: An automated script that updates the proxy on `urseismogate`. It creates a `location /code-search/` block routing traffic into the `55010` tunnel.
3.  **Daemon Management (`codesearch-app.service`)**: Ensures the Streamlit application automatically restarts upon machine reboots.

For more details on the global network architecture, refer to the [Research & Teaching Services Architecture](RsrchTeachingServices.md).
