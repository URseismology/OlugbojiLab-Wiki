# The AI Generation Process

To manage the massive scale of the lab's codebase without causing AI context window explosions (Out Of Memory errors), we developed a custom 2-node architecture:

## 1. The HPC Mapper (`roverBckUp.py`)
Running on the **Bluehive HPC Cluster**, this script recursively scans the entire `/scratch/tolugboj_lab` directory. It safely bypasses massive generic libraries (like Anaconda environments), extracts only the structural source code files (`.m`, `.py`, `.sh`, etc.), packages them into `tar.gz` files, and pushes them directly to the Synology NAS.

* **[Download roverBckUp.py](scripts/roverBckUp.py)**

## 2. The AI Synthesizer (`AIBot-WikiCrafter.py`)
Running on our local dual-GPU inference server (`inferencelocal`), an infinite background daemon polls the NAS for new tarballs. 
It uses a **Recursive Map-Reduce** strategy:
1. **File Map:** It reads every single script individually and asks `DeepSeek-Coder-V2` to generate a 3-sentence summary of its inputs, outputs, and purpose.
2. **Folder Reduce:** It combines the file summaries of a single folder and asks `Qwen2.5-72B` to synthesize a folder-level summary.
3. **Subsystem Bubble-up:** It recursively bubbles these folder summaries up the directory tree until it reaches the root.
4. **Final Synthesis:** `Qwen2.5-72B` takes the massive hierarchical summary and writes the comprehensive Wiki you are reading now.

* **[Download AIBot-WikiCrafter.py](scripts/AIBot-WikiCrafter.py)**

## 3. The GitHub Publisher (`AIBot-GitHubPublisher.py`)
A cron job runs weekly to parse the raw NAS Wikis, inject these disclaimers, format the direct NAS download links, and automatically push the updates to this GitHub repository.

* **[Download AIBot-GitHubPublisher.py](scripts/AIBot-GitHubPublisher.py)**
