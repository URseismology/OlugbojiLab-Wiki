# Future Extensions: Two-Agent Socratic Pipeline

This document conceptualizes a future architectural upgrade to the lab's AI Coding Assistant. The goal is to solve the "Alignment Tax" and dimensionality/mathematical hallucination problems observed when using single, constrained models.

## 1. The Core Concept: Two-Agent Pedagogy
Currently, Jupyter AI talks directly to a single Ollama model (`deepseek-coder-v2`). When we force this mathematical model to act as a conversational teacher via a strict "Socratic" prompt, its mathematical reasoning occasionally degrades.

To solve this, we propose a **Middleware API Proxy** on the GPU server that orchestrates two separate models:
1. **Agent A (The Solver):** A heavy model (e.g., `deepseek-coder-v2` or `codestral`) that solves the raw math/code perfectly in the background without any personality constraints.
2. **Agent B (The Pedagogue):** A smaller, highly empathetic model (e.g., `llama3` or `phi-3`) that takes the student's question and Agent A's perfect answer, and generates a conversational, Socratic hint based on the true ground truth.

## 2. Hardware Infrastructure (Staging Environment)
**CRITICAL SAFETY CONSTRAINT:** This experimental LangChain Middleware Proxy must NOT be deployed on the live `terra4-classnode` production environment. 

To safely prototype this, we will utilize a dedicated staging frontend machine:
*   **Frontend Hub:** `terra4b-classnode`
    *   **Role:** Acts as the staging JupyterHub environment mimicking the production `terra4-classnode`. It hosts a completely isolated Docker Swarm network for testing.
*   **Backend GPU:** `terravibranium-gpu`
    *   **Role:** Hosts the raw Ollama daemon on `11434` AND hosts our new Python FastAPI Middleware container on an isolated port (e.g., `8000`).
*   **DMZ Gateway (Optional):** `urseismogate`
    *   **Role:** If external testing is required, Nginx can route a subpath like `https://urseismogate.earth.rochester.edu/lab-beta/` securely into `terra4b-classnode` via an autossh tunnel.

## 3. Software Infrastructure & Templates

To execute this architecture, an AI Agent will need to deploy a Python FastAPI middleware server on `terravibranium-gpu`. 

### Middleware Implementation Template (`proxy.py`)
This script uses FastAPI to impersonate the standard Ollama API endpoint, tricking Jupyter AI into sending its chat logs here. It then uses LangChain to orchestrate the Two-Agent flow.

```python
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
import uvicorn

app = FastAPI()

# 1. Initialize the two models connecting to the local Ollama daemon
solver = Ollama(model="deepseek-coder-v2", base_url="http://localhost:11434")
pedagogue = Ollama(model="llama3:8b", base_url="http://localhost:11434")

class ChatRequest(BaseModel):
    prompt: str

@app.post("/api/generate")
async def generate_chat(req: ChatRequest):
    # Step 1: Unconstrained Mathematical Solving
    true_answer = solver.invoke(req.prompt)
    
    # Step 2: Socratic Translation
    pedagogy_prompt = PromptTemplate.from_template(
        "You are an expert TA. A student asked this question: {student_q}\n"
        "The correct answer is: {true_a}\n"
        "Provide a 1-sentence hint pointing the student toward the answer without writing the code for them."
    )
    chain = pedagogy_prompt | pedagogue
    socratic_response = chain.invoke({"student_q": req.prompt, "true_a": true_answer})
    
    # Return disguised as a standard Ollama response to trick Jupyter AI
    return {"model": "coding-assistant", "response": socratic_response, "done": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 4. Agent Activation Prompt

Whenever the lab is ready to implement this extension, simply open a new session with an AI Agent and paste the following prompt block:

> "We are ready to deploy our experimental 'Two-Agent Socratic Pipeline' for our JupyterHub lab environment. 
> 
> Please read the `Future_Extensions_TwoAgent_AI.md` document located in the `URseismology/OlugbojiLab-Wiki` repository. Our target frontend is `terra4b-classnode` and our backend GPU is `terravibranium-gpu`. 
> 
> Your first task is to SSH into `terravibranium-gpu`, create a Dockerfile for the FastAPI proxy middleware provided in the documentation, spin it up on port 8000, and ensure it can successfully query the local Ollama daemon. Then, we will configure JupyterHub on `terra4b-classnode` to point to port 8000."
