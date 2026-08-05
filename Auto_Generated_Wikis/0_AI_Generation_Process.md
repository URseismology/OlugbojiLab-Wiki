# The AI Generation Process

To manage the massive scale of the lab's codebase without causing AI context window explosions (Out Of Memory errors), we developed a custom multi-stage architecture:

## 1. The HPC Mapper (`roverBckUp.py`)
Running on the **Bluehive HPC Cluster** (or local machines like `10.5.246.255`), this script recursively scans user directories. It safely bypasses massive generic libraries (like Anaconda environments), extracts only the structural source code files (`.m`, `.py`, `.sh`, etc.), packages them into `tar.gz` files, and pushes them directly to the Synology NAS.

* **[Download roverBckUp.py](../scripts/roverBckUp.py)**

## 2. The AI Synthesizer (`AIBot-WikiCrafter.py`)
Located at `/home/urseismoadmin/AIBot-WikiCrafter.py` on our local dual-GPU inference server (`inferencelocal`), an infinite background daemon polls the NAS for new tarballs. 
It uses a **Recursive Map-Reduce** strategy:
1. **File Map:** It reads every single script individually and asks `DeepSeek-Coder-V2` to generate a 3-sentence summary of its inputs, outputs, and purpose. (Stored in a local SQLite database).
2. **Folder Reduce:** It combines the file summaries of a single folder and asks `Qwen2.5-72B` to synthesize a folder-level summary.
3. **Subsystem Bubble-up:** It recursively bubbles these folder summaries up the directory tree until it reaches the root.
4. **Final Synthesis:** `Qwen2.5-72B` takes the massive hierarchical summary and writes the comprehensive Wiki you are reading now to the NAS.

### Daemon Service Management
The synthesizer is **not** a cron job; it is an infinite `while True` daemon. To ensure it never fails or permanently dies upon crashing, it should be managed as a `systemd` service with automatic restarts.
* **Service File Location:** `/home/urseismoadmin/AIBot-WikiCrafter.service`
* **Restarting the daemon:** `systemctl --user restart AIBot-WikiCrafter.service`

* **[Download AIBot-WikiCrafter.py](../scripts/AIBot-WikiCrafter.py)**

## 3. The GitHub Publisher (`AIBot-GitHubPublisher.py`)
Because generating the AI Wikis takes hours, the generation step is completely decoupled from publishing. A **cron job** runs weekly to parse the raw NAS Wikis, inject standard disclaimers, format the direct NAS download links, and automatically push the updates to this GitHub repository. 

* **[Download AIBot-GitHubPublisher.py](../scripts/AIBot-GitHubPublisher.py)**

## 4. The Vector Indexer (`AIBot-KnowledgeIndexer.py`)
To power the lab's interactive semantic codebase search (via Open WebUI and Streamlit), a fourth distinct script vectorizes the code. Once the `AIBot-WikiCrafter` finishes generating the SQLite database summaries, this indexer script reads those summaries, converts them into high-dimensional mathematical vectors using Ollama's `nomic-embed-text` model, and stores them in a local **ChromaDB** vector database on `inferencelocal`. 

*(Note: Currently, this indexer does not run automatically; it must be executed manually after a massive new code ingestion finishes, or tied to a separate cron schedule).*

* **[Download AIBot-KnowledgeIndexer.py](../scripts/AIBot-KnowledgeIndexer.py)**
