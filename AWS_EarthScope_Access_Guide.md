# AWS and EarthScope Access Setup Guide

This guide outlines the steps required to provision and configure access to AWS and the EarthScope Cloud on a new machine (local Mac, compute node, or server) in the lab.

---

## 1. Prerequisites
These tools are not required if you only intend to run manual AWS CLI queries. However, they are **mandatory** to clone, build, and run the containerized data pipeline and automatic EC2 orchestrator (`orchestrator.py`) [1]:
*   **SSH Key Pair:** Generate an SSH key (`ssh-keygen -t ed25519`) and add it to your GitHub profile to clone the code.
*   **Git:** Install Git to pull the repository.
*   **Docker:** Install and start the Docker daemon (used to run Python scripts inside the containerized environment).
*   **Python 3:** Ensure Python 3 and `pip` are installed (needed to run the local orchestrator script).

### Directory Setup
*   **CRITICAL:** Do not clone or run the cloud pipeline inside synchronized folders (like your local Synology/NAS clone of `Admin8_LabAI`) [2]. The high volume of downloading raw files will trigger endless network syncing [2].
*   Always clone the repository to the user's home directory:
    ```bash
    git clone git@github.com:URseismology/wavenet-epicAI.git ~/wavenet-epicAI
    ```

---

## 2. AWS Console & Key Generation
Instead of creating a new account, we use the primary lab root account.

### Step-by-Step Security Key Creation:
1.  **Access the Console:** Go to [aws.amazon.com](https://aws.amazon.com/) and click **Sign In to the Console**.
2.  **Log In:** Select **Root user**, enter the lab root email `tolulope.olugboji@rochester.edu`, and log in.
3.  **Navigate to IAM:** In the top search bar, type `IAM` and click on the **IAM** service.
4.  **Create IAM User (Recommended Best Practice):**
    *   On the left sidebar, click **Users** -> **Create user**.
    *   Name the user `atos-orchestrator` (or similar) and click **Next**.
    *   Select **Attach policies directly**.
    *   Search for and select:
        *   `AmazonEC2FullAccess`
        *   `AmazonS3FullAccess`
    *   Click **Next** and then **Create user**.
5.  **Generate Access Keys:**
    *   In the **Users** list, click on your newly created user (e.g., `atos-orchestrator`).
    *   Click on the **Security credentials** tab.
    *   Scroll down to the **Access keys** section and click **Create access key**.
    *   Select **Command Line Interface (CLI)**, check the confirmation box, and click **Next**.
    *   Click **Create access key**.
    *   **CRITICAL:** Copy the **Access Key ID** and **Secret Access Key**. Save these securely (e.g., download the `.csv` file), as the secret key will never be shown again.

---

## 3. Installing & Configuring AWS CLI
You must install the AWS CLI locally to authorize your machine.

### Installation Instructions:
*   **macOS (Homebrew):**
    ```bash
    brew install awscli
    ```
*   **macOS (Graphical Installer):**
    Download and run the [macOS AWS CLI PKG](https://awscli.amazonaws.com/AWSCLIV2.pkg).
*   **Linux (Ubuntu/Debian):**
    ```bash
    sudo apt-get update && sudo apt-get install -y unzip curl
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    ```

### CLI Configuration:
Run the configuration command in your terminal:
```bash
aws configure
```
Enter the prompt values as follows:
*   **AWS Access Key ID:** `[Your Generated Access Key ID]`
*   **AWS Secret Access Key:** `[Your Generated Secret Access Key]`
*   **Default region name:** `us-east-2` *(CRITICAL: EarthScope S3 data resides in Ohio/us-east-2. Matching this region prevents egress charges and ensures direct access) [2].*
*   **Default output format:** `json` [2]

---

## 4. EarthScope Cloud Authentication
EarthScope manages access to its seismic database using its own identity systems [1]. The authentication token authorizes your AWS IAM credentials to access EarthScope S3 buckets [1].

### Understanding `es login`:
*   **What is it:** The `es` tool is the official EarthScope CLI, distributed as the `earthscope-cli` Python package on PyPI. 
*   **GitHub Host:** The source code and repository for this tool are maintained by the **EarthScope Consortium** on GitHub at [github.com/EarthScope](https://github.com/EarthScope).
*   **Docker Installation:** In the Docker image `urseismogate.earth.rochester.edu/chrisscripts:latest`, this CLI tool is pre-installed globally during the build using `pip install earthscope-cli`. Running `es login` runs this command-line application inside the container, saving credentials to a shared volume.

### Execution Steps:
1.  **Register:** Ensure you have an active account at [earthscope.org](https://www.earthscope.org).
2.  **Run Authentication Command:**
    Run the following command in your terminal:
    ```bash
    docker run -it --rm \
      -v ~/.earthscope:/home/jovyan/.earthscope \
      urseismogate.earth.rochester.edu/chrisscripts:latest \
      es login
    ```
3.  **Complete the Authentication Flow:**
    *   The command line will output a URL (e.g., `https://profile.earthscope.org/...`) and a temporary one-time **User Code**.
    *   Open the link in your web browser, log in to your EarthScope account, and input the code to authorize the device.
    *   Once authorized, the script inside the Docker container will complete the process and save the credentials token to the host’s local `~/.earthscope` directory [1].

---

## 5. Local Execution vs. Cloud Orchestration
*   **Local Direct Download Blocks:** Direct `GetObject` S3 calls from your local machine to restricted EarthScope S3 buckets will fail with a `403 Forbidden` or `FgaAccessDenied` error. This is because EarthScope's bucket policies explicitly block downloads originating from outside the `us-east-2` AWS region [1].
*   **The Orchestrator Solution:** Run the automated cloud script:
    ```bash
    cd ~/wavenet-epicAI
    python3 chrisScripts/singleNCFtest/orchestrator.py
    ```
    This script automatically spins up an EC2 instance in `us-east-2`, mounts your credentials, downloads the data within Docker in the correct region, transfers the processed output back to your machine, and terminates the server to avoid billing [1].

---

## References
*   [1] [AWS Docker Pipeline Guide](file:///Users/olugboji/SynologyDrive/1.UofR_Seismology/1_Admin/Admin8_LabAI/KNOWLEDGE_BASE/AWS_Docker_Pipeline_Guide.md)
*   [2] [OlugbojiLabConnects Manifesto](file:///Users/olugboji/SynologyDrive/1.UofR_Seismology/1_Admin/Admin8_LabAI/KNOWLEDGE_BASE/OlugbojiLabConnects_Manifesto.md)
*   [3] [NAS Connections](file:///Users/olugboji/SynologyDrive/1.UofR_Seismology/1_Admin/Admin8_LabAI/KNOWLEDGE_BASE/NAS_Connections.md)
*   [4] [Three-Part Readme](https://github.com/URseismology/wavenet-epicAI/blob/main/chrisScripts/README.md)
