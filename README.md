# OlugbojiLab-Wiki Repository Organization

The [OlugbojiLab-Wiki](https://github.com/URseismology/OlugbojiLab-Wiki) repository has been restructured to cleanly separate manually maintained lab documentation from the automated AI-generated codebase wikis. 

Below is the current layout of the top-level directories and their contents.

## Root Directory `/`
The root directory is strictly reserved for manually created documentation that requires human curation, architectural post-mortems, and core repository structure. This ensures that important information is not overwritten by the automated pipeline.

**Files:**
- [`AWS_EarthScope_Access_Guide.md`](AWS_EarthScope_Access_Guide.md): Detailed guide for provisioning and configuring AWS and EarthScope access on new lab machines.
- [`CodeSearch_Architecture.md`](CodeSearch_Architecture.md): Documentation of the LabAI CodeSearch Ecosystem architecture (semantic RAG backend, web dashboard, and persistent service tunnels).
- [`data-archiving.md`](data-archiving.md): Documentation of the lab's fault-tolerant, automated massive data archival infrastructure.
- [`DrOJupterLabs.md`](DrOJupterLabs.md): Documentation for the JupyterLab setups.
- [`Future_Extensions_TwoAgent_AI.md`](Future_Extensions_TwoAgent_AI.md): Planning document for extending the AI pipeline architecture.
- [`JupyterHub_Network_PostMortem.md`](JupyterHub_Network_PostMortem.md): Architectural details and incident review of the JupyterHub setup.
- [`RsrchTeachingServices.md`](RsrchTeachingServices.md): Primary documentation for Research and Teaching Services architecture.

## `/Auto_Generated_Wikis`
This is a dedicated directory managed entirely by the `AIBot-GitHubPublisher.py` script. Every file inside this directory is automatically generated on a weekly basis by the local AI pipeline (`DeepSeek-Coder-V2` & `Qwen2.5-72B`).

**Contents:**
- [`README.md`](Auto_Generated_Wikis/README.md): The automated index linking to all generated project wikis.
- [`0_AI_Generation_Process.md`](Auto_Generated_Wikis/0_AI_Generation_Process.md): The canonical explanation of the 3-script `roverBckUp` / `WikiCrafter` / `GitHubPublisher` pipeline.
- `*.md`: Over 60+ individually generated codebase wikis corresponding to lab projects (e.g., [`Prj18_Mid_mantle.md`](Auto_Generated_Wikis/Prj18_Mid_mantle.md), [`Prj_Wavenet.md`](Auto_Generated_Wikis/Prj_Wavenet.md), [`Sayan_Swar_WS.md`](Auto_Generated_Wikis/Sayan_Swar_WS.md)). Each file includes a strict ASCII file tree and an `![AI Generated]` badge at the top.

## `/scripts`
This directory holds backups of the scripts used in the automated pipeline and teaching setups. These are pushed automatically by the publisher.

**Contents:**
- [`AIBot-GitHubPublisher.py`](scripts/AIBot-GitHubPublisher.py): The weekly cron script that packages and pushes updates to GitHub.
- [`AIBot-WikiCrafter.py`](scripts/AIBot-WikiCrafter.py): The daemon that runs on `inferencelocal` synthesizing summaries via the local LLM.
- [`AIBot-WikiFormatter.py`](scripts/AIBot-WikiFormatter.py): The script that standardizes ASCII file trees deterministically.
- [`roverBckUp.py`](scripts/roverBckUp.py): The HPC mapper script that tars source code files.
- [`Dockerfile.student.strict_socratic`](scripts/Dockerfile.student.strict_socratic) & [`ta_reporting_script.py`](scripts/ta_reporting_script.py): Scripts related to the student class node infrastructure.
