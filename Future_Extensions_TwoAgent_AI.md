# Implemented: Two-Agent Socratic Pipeline

This document outlines the architectural upgrade to the lab's AI Coding Assistant, which was designed to solve the "Alignment Tax" and dimensionality/mathematical hallucination problems observed when using single, constrained models.

**STATUS:** Successfully deployed to the `/lab-beta` staging environment on `terra5-classnode`!

## 1. The Core Concept: Two-Agent Pedagogy
Currently, Jupyter AI talks directly to a proxy middleware rather than a single Ollama model. When we forced mathematical models to act as conversational teachers via a strict "Socratic" prompt, their mathematical reasoning occasionally degraded.

To solve this, we propose a **Middleware API Proxy** on the GPU server that orchestrates two separate models:
1. **Agent A (The Solver):** A heavy model (e.g., `deepseek-coder-v2` or `codestral`) that solves the raw math/code perfectly in the background without any personality constraints.
2. **Agent B (The Pedagogue):** A smaller, highly empathetic model (e.g., `llama3` or `phi-3`) that takes the student's question and Agent A's perfect answer, and generates a conversational, Socratic hint based on the true ground truth.

## 2. Hardware Infrastructure (Staging Environment)
**CRITICAL SAFETY CONSTRAINT:** This experimental LangChain Middleware Proxy was built on an isolated cluster so it does NOT impact the live `terra4-classnode` production environment. 

We utilized a dedicated staging frontend machine:
*   **Frontend Hub:** `terra5-classnode`
    *   **Role:** Acts as the staging JupyterHub environment (`/lab-beta`) mimicking the production `terra4-classnode`. It hosts a completely isolated CPU-only Docker Swarm network for testing.
*   **Backend GPU:** `terravibranium-gpu`
    *   **Role:** Hosts the raw Ollama daemon on `11434` AND hosts our Python FastAPI Middleware container on an isolated port (`8000`).
*   **DMZ Gateway:** `urseismogate`
    *   **Role:** Nginx routes external traffic from `https://urseismogate.earth.rochester.edu/lab-beta/` securely into `terra5-classnode` via an autossh tunnel on port `55009`.

## 3. Software Infrastructure & Templates

## 3. Software Infrastructure (Proxy Implementation)

To execute this architecture, we deployed a Python FastAPI middleware server on `terravibranium-gpu`. 

### Middleware Implementation (`proxy.py`)
This script uses FastAPI to impersonate the standard Ollama `/api/chat` endpoint, tricking Jupyter AI into sending its `messages` array here. It extracts the user's prompt, passes it to the mathematical solver, and then forces the pedagogical model to translate the true answer into a Socratic hint with strict guardrails to prevent instruction-drift tangents.

```python
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
import uvicorn
from typing import List, Dict, Any

app = FastAPI()

# 1. Initialize the two models connecting to the local Ollama daemon
solver = Ollama(model="qwen2.5-coder:14b", base_url="http://128.151.53.156:11434")
pedagogue = Ollama(model="llama3.1", base_url="http://128.151.53.156:11434")

class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    stream: bool = False

@app.post("/api/chat")
async def generate_chat(req: ChatRequest):
    # Extract the last user message
    user_message = next((m["content"] for m in reversed(req.messages) if m["role"] == "user"), "")
    
    # Step 1: Unconstrained Mathematical Solving
    true_answer = solver.invoke(user_message)
    
    # Step 2: Socratic Translation
    pedagogy_prompt = PromptTemplate.from_template(
        "You are an expert Teaching Assistant. A student asked: {student_q}\n"
        "The complete solution is: {true_a}\n\n"
        "Your task is to guide the student to this solution without giving them the final working code. "
        "If the student provides code or an answer, explicitly evaluate it first. Tell them if they are on the right track or gently point out what they missed.\n"
        "You SHOULD provide structural help, such as:\n"
        "- The explicit mathematical formula they need (e.g., the Haversine formula equation).\n"
        "- Code scaffolding or pseudo-code with blanks (e.g., `___ = math.sin(___)`).\n"
        "- Explanations of the specific functions they need to use.\n\n"
        "CRITICAL RULES:\n"
        "1. You MUST NOT provide a fully corrected, copy-pasteable working code block. Leave the final implementation to the student.\n"
        "2. STAY FOCUSED on the specific mathematical or logic problem. DO NOT ask tangential questions about basic programming concepts (like data types, floats, or syntax) unless the student asks. Keep your guiding questions strictly focused on solving the core equation or bug.\n"
        "Always end with an encouraging, guiding question."
    )
    chain = pedagogy_prompt | pedagogue
    socratic_response = chain.invoke({"student_q": user_message, "true_a": true_answer})
    
    # Return disguised as a standard Ollama chat response
    return {
        "model": req.model,
        "message": {
            "role": "assistant",
            "content": socratic_response
        },
        "done": True
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
