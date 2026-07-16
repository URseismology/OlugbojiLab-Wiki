# Future Extensions: Two-Agent Socratic Pipeline

This document conceptualizes a future architectural upgrade to the lab's AI Coding Assistant. The goal is to solve the "Alignment Tax" and dimensionality/mathematical hallucination problems observed when using single, constrained models.

## 1. The Core Concept: Two-Agent Pedagogy
Currently, Jupyter AI talks directly to a single Ollama model (`deepseek-coder-v2`). When we force this mathematical model to act as a conversational teacher via a strict "Socratic" prompt, its mathematical reasoning occasionally degrades.

To solve this, we propose a **Middleware API Proxy** on the GPU server that orchestrates two separate models:
1. **Agent A (The Solver):** A heavy model (e.g., `deepseek-coder-v2` or `codestral`) that solves the raw math/code perfectly in the background without any personality constraints.
2. **Agent B (The Pedagogue):** A smaller, highly empathetic model (e.g., `llama3` or `phi-3`) that takes the student's question and Agent A's perfect answer, and generates a conversational, Socratic hint based on the true ground truth.

## 2. Infrastructure: The "Staging" Hub
**CRITICAL SAFETY CONSTRAINT:** Because introducing a custom LangChain Middleware Proxy is a significant architectural rewrite, **this extension must NOT be deployed on the live `terra4-classnode` production environment.**

Instead, the implementation plan is to deploy a completely isolated staging environment:
1. Spin up a secondary JupyterHub instance (e.g., `jupyterhub-staging`).
2. Map it to a separate test port or sub-path via the Nginx DMZ gateway (e.g., `/lab-beta/`).
3. Deploy the custom Python FastAPI proxy on `terravibranium-gpu` on an isolated port (e.g., `8000`).
4. Point the staging JupyterHub's `OLLAMA_HOST` variable to the new proxy port.

This allows TAs and developers to stress-test the latency and accuracy of the Two-Agent pipeline without risking the stability or availability of the active student lab.
