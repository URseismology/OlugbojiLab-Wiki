# Literature Discovery AI System (Revised Plan v3)

This implementation plan outlines the architecture and deployment batches for the local-first, agentic literature discovery ecosystem. The core philosophy remains: **Metadata First, Graph First, PDF Second, Deep Evidence Last.**

## Answers to Your Feedback

* **Semantic Scholar Recommendations API:** You are absolutely right! Semantic Scholar has a powerful `/recommendations` endpoint that accepts positive and negative paper IDs. We will integrate this directly into Batch 3. Instead of manually crawling citation-by-citation (which is slow), we will take the papers our local `qwen2.5-14b` Judge marked as `ACQUIRE` and feed them to the API as "positive seeds", while feeding the `DISCARD` papers as "negative seeds". This creates an incredibly powerful Active-Learning Loop (Step 16 of the architecture) where Semantic Scholar's backend does the heavy semantic graph traversal for us based on the local AI's localized judgements!
* **Gemini Models & Account Tier:** Based on the API key test I just ran on your server, your Pro/Developer tier account gives you access to a massive and highly advanced suite of models. Specifically, you have access to:
  * `gemini-1.5-pro` and `gemini-1.5-flash` (with massive 2-million token context windows, perfect for deep synthesis of dozens of PDFs at once).
  * `gemini-2.5-flash` (including native audio support).
  * `deep-research-pro` and `deep-research-max` (highly advanced agentic research models).
  * You also have access to `imagen-4.0` (image generation) and `veo-3.1` (video generation). 
  We will specifically target the `gemini-1.5-pro` (or the newer `2.5`/`deep-research` models if you prefer) for the Streamlit Deep Synthesis UI to take advantage of that massive context window.

---

## Proposed Architecture

### 1. The Scout & Judge API (`AIBot-LitDiscovery-API.py`)
A FastAPI backend running on `inferencelocal`. It handles all interactions with `qwen2.5-14b`, Semantic Scholar, and OpenAlex. 

### 2. The Knowledge Graph DB (`LitDiscovery_Graph.db`)
A SQLite database consisting of three primary tables:
* **`candidates`**: Stores both the external canonical metadata (DOI, title, abstract, citation counts) AND the deep local interpretations (research-question match, methodological match, reasoning for ranking, confidence, novelty potential, and current decision state). This allows the UI to instantly display exactly *why* the AI ranked a paper highly.
* **`edges`**: Maps citation and reference relationships between candidate DOIs to build the internal graph.
* **`prompts`**: An audit log storing the exact LLM prompt and reasoning output that resulted in a candidate's ranking (as required by specification #23).

### 3. The Web Dashboard (`AIBot-LitDiscovery-App.py`)
A Streamlit interface hosted on `inferencelocal` (Port 8502, tunneled to 55011). It visualizes the staged pipeline (Steps 5-10) in real-time, displays the interactive priority queue, and serves as the Cloud AI Deep Synthesis terminal for fully acquired papers.

---

## Deployment Strategy (Iterative Batches)

### Batch 1: The Initial MVP (API & Metadata Engine)
*We will build the foundational backend engine (Steps 4-8) before touching the UI.*

#### Detailed Implementation of Steps 4-8:
* **Step 4 (Research Question Expansion):** The API receives a natural language query. It sends a structured prompt to `qwen2.5-14b` forcing it to output a JSON object containing `TARGET`, `MECHANISM`, `METHODS`, `SYNONYMS`, and `EXCLUSIONS`.
* **Step 5 (Initial Discovery):** The Python script parses the LLM's JSON and executes parallel HTTP requests to Semantic Scholar and OpenAlex. It retrieves up to 500 candidate metadata objects.
* **Step 6 (Metadata-First Assessment):** The API iterates through the candidates. It explicitly instructs `qwen2.5-14b` to assign a state (`DISCARD`, `WATCH`, `EXPAND`, `ACQUIRE`, `UNKNOWN`) and extract local interpretation tags (methodological match, etc.) based strictly on the abstract.
* **Step 7 (Candidate Representation):** The Python script writes the accepted candidates into `LitDiscovery_Graph.db` (`candidates` table), storing the external metrics alongside the deep local interpretation strings.
* **Step 8 (Relative Ranking):** The API batches the candidates into groups of 10. It prompts the LLM with the metadata of all 10 simultaneously, asking it to rank them relative to each other based on expected research value. The resulting priority score is saved to sort the final queue.

### Batch 2: The Streamlit Web Interface (Discovery UI)
*Visualize the Research Frontier and interact with the pipeline.*
- **Pipeline Visualizer:** A live progress bar showing the backend transitioning through Steps 4 (Query), 5 (API Crawl), 6 (Assessment), and 8 (Ranking).
- **Interactive Priority Queue:** A sorted table of the top 30 candidates, displaying the AI's reasoning for why each paper was ranked highly.
- **Two-Step Acquisition:** Each paper will have two actionable buttons:
  1. **Add to Paperpile:** A bookmarklet/DOI resolver link that triggers your Paperpile chrome extension.
  2. **Acquire to NAS:** A local toggle that marks the paper's DB state as pending manual download to the NAS.

### Batch 3: Graph Traversal (The Cartographer & Active Learning)
*Supercharge discovery using Semantic Scholar Recommendations.*
- Rather than manually crawling citations, the API will query the Semantic Scholar `/recommendations` API.
- **Active Learning Loop:** We will pass the DOIs of papers the local Judge marked as `ACQUIRE` as "positive examples" and papers marked as `DISCARD` as "negative examples". 
- This allows Semantic Scholar's backend to do the heavy graph traversal and instantly return highly personalized, deduplicated candidate papers that match the exact nuanced preferences of the local AI Judge.

### Batch 4: The Cloud AI Deep Synthesis Integration
*Connect to the existing GPU pipeline and the Cloud.*
- When you drop a PDF into the NAS folder, the existing `AIBot_PaperCrafter.py` daemon parses the PDF and updates the database state to `FULL_TEXT_ANALYZED`.
- **Cloud Synthesis UI:** The Streamlit dashboard will feature a "Deep Synthesis" tab. This tab will load the rich Markdown and JSON artifacts generated by `PaperCrafter` and pipe them via API to a cloud model (like Gemini 1.5 Pro). This enables you to chat with, compare, and deeply synthesize the full contents of multiple acquired papers simultaneously using massive context windows.

---

## Verification Plan (Batch 1)
- Write and execute `AIBot-LitDiscovery-API.py` directly from the command line.
- Submit the test query: *"Find research on geological ocean soundscape and how H-wave and T-phases generated by geological hazards are detected and recorded by these waves."*
- We will monitor the terminal output to ensure `qwen2.5-14b` successfully structures the query, retrieves candidates, populates the rich interpretation metadata, and performs comparative rankings without any JSON parsing errors.
