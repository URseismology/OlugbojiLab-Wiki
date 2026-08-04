import argparse
import os
import tarfile
import shutil
import subprocess

NAS_CODE_DIR = "/mnt/ADAMA-Shared/GodModeData/CodeBaseFull"
WORKSPACE_DIR = "/home/urseismoadmin/AIBot_workdir/workspaces"

def main():
    parser = argparse.ArgumentParser(description="LabAI Codebase Scaffolder")
    parser.add_argument("--like", required=True, help="Existing project prefix to use as template (e.g., 'Prj4_Mai')")
    parser.add_argument("--name", required=True, help="Name of the new project (e.g., 'New_Simulation')")
    args = parser.parse_args()

    print(f"🔍 Locating template for '{args.like}'...")
    
    # Find the tarball
    tarballs = [f for f in os.listdir(NAS_CODE_DIR) if f.startswith(args.like) and f.endswith(".tar.gz")]
    if not tarballs:
        print(f"❌ Error: Could not find any tarballs starting with '{args.like}' in {NAS_CODE_DIR}")
        return
    
    source_tar = os.path.join(NAS_CODE_DIR, tarballs[0])
    print(f"✅ Found template: {tarballs[0]}")
    
    new_project_path = os.path.join(WORKSPACE_DIR, args.name)
    if os.path.exists(new_project_path):
        print(f"❌ Error: Workspace '{new_project_path}' already exists.")
        return
        
    os.makedirs(new_project_path, exist_ok=True)
    
    print(f"📦 Extracting template to {new_project_path}...")
    try:
        with tarfile.open(source_tar, "r:gz") as tar:
            tar.extractall(path=new_project_path)
    except Exception as e:
        print(f"❌ Error extracting tarball: {e}")
        return

    print("🔧 Initializing fresh git repository...")
    try:
        subprocess.run(["git", "init"], cwd=new_project_path, check=True, capture_output=True)
        # Create a basic .gitignore
        with open(os.path.join(new_project_path, ".gitignore"), "w") as f:
            f.write("*.pyc\n__pycache__/\n*.log\n.DS_Store\n")
        subprocess.run(["git", "add", "."], cwd=new_project_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Initial commit scaffolded from {args.like}"], cwd=new_project_path, check=True, capture_output=True)
    except Exception as e:
        print(f"⚠️ Warning: Failed to initialize git repository: {e}")

    print(f"\n🎉 Success! New project '{args.name}' is ready at:\n➡️  {new_project_path}")
    print("\nYou can now mount this workspace in JupyterHub or edit it locally.")

if __name__ == "__main__":
    main()
