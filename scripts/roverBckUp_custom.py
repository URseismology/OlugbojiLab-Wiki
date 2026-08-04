#!/usr/bin/env python3
import os
import sys
import json
import argparse
import datetime
import shutil
import re
import subprocess
import concurrent.futures
import sqlite3

# Default code extensions to extract
DEFAULT_CODE_EXTS = {
    '.py', '.sh', '.bash', '.pl', '.pm', '.R', '.m', '.bat', '.ps1',
    '.c', '.cpp', '.h', '.hpp', '.cc', '.cxx', '.f90', '.f', '.f77', '.f95', '.for',
    '.java', '.go', '.rs', '.scala', '.kt', '.swift',
    '.ipynb', '.yaml', '.yml', '.json', '.toml', '.ini', '.cfg', '.conf',
    '.slurm', '.sbatch', '.pbs', '.condor'
}

DEFAULT_EXCLUDE_DIRS = {
    '.git', '.svn', '.hg', '__pycache__', '.ipynb_checkpoints', '.vscode', '.idea',
    'node_modules', '.pytest_cache', 'venv', '.venv', 'env',
    'softwares', 'anaconda', 'anaconda3', 'miniconda', 'miniconda3', 'envs'
}

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS projects
                 (name TEXT PRIMARY KEY, status TEXT, timestamp TEXT)''')
    conn.commit()
    return conn

def set_project_status(conn, name, status):
    c = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR REPLACE INTO projects (name, status, timestamp) VALUES (?, ?, ?)", (name, status, timestamp))
    conn.commit()

def get_project_status(conn, name):
    c = conn.cursor()
    c.execute("SELECT status FROM projects WHERE name=?", (name,))
    row = c.fetchone()
    return row[0] if row else None

def log_error(error_msg, error_log_path="roverBckUp_errors.log"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(error_log_path, "a") as f:
        f.write(f"[{timestamp}] {error_msg}\n")

def get_pattern(filename):
    """Replaces contiguous digits with '*' to group similar files"""
    pattern = re.sub(r'\d+', '*', filename)
    return pattern

def scan_dir_worker(dir_path, exclude_dirs, code_extensions, error_log_path):
    local_dirs = []
    patterns = {}
    code_files = []
    
    try:
        with os.scandir(dir_path) as it:
            for entry in it:
                if entry.name in exclude_dirs:
                    continue
                
                try:
                    if entry.is_dir(follow_symlinks=False):
                        local_dirs.append(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        ext = os.path.splitext(entry.name)[1].lower()
                        is_code = ext in code_extensions
                        if is_code:
                            code_files.append({"src": entry.path, "name": entry.name})
                        
                        try:
                            size = entry.stat(follow_symlinks=False).st_size
                        except Exception as e:
                            log_error(f"StatError on {entry.path}: {e}", error_log_path)
                            size = 0
                        
                        pat = get_pattern(entry.name)
                        if pat not in patterns:
                            patterns[pat] = {"count": 0, "size": 0, "is_code": is_code}
                        patterns[pat]["count"] += 1
                        patterns[pat]["size"] += size
                except PermissionError as pe:
                    log_error(f"PermissionError (entry access) in {dir_path}: {pe}", error_log_path)
                except OSError as oe:
                    log_error(f"OSError (entry access) in {dir_path}: {oe}", error_log_path)

    except PermissionError as pe:
        log_error(f"PermissionError (scandir) on {dir_path}: {pe}", error_log_path)
    except Exception as e:
        log_error(f"Unknown Error (scandir) on {dir_path}: {e}", error_log_path)
        
    return dir_path, local_dirs, patterns, code_files

def copy_worker(item, src_dir, temp_code_dir, error_log_path):
    src = item["src"]
    rel_path = os.path.relpath(src, src_dir)
    dest = os.path.join(temp_code_dir, rel_path)
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
    except PermissionError as pe:
        log_error(f"PermissionError (copying file) {src}: {pe}", error_log_path)
    except Exception as e:
        log_error(f"CopyError {src}: {e}", error_log_path)

def process_project(project_dir, project_name, args, conn):
    print(f"\n--- Starting project: {project_name} ---")
    set_project_status(conn, project_name, "RUNNING")
    
    topology = {}
    all_code_files = []
    error_log_path = os.path.join(args.root_dir, "roverBckUp_errors.log")
    
    # Phase 1: Scan
    start_time = datetime.datetime.now()
    dirs_processed = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.threads) as executor:
        future_to_dir = {executor.submit(scan_dir_worker, project_dir, DEFAULT_EXCLUDE_DIRS, DEFAULT_CODE_EXTS, error_log_path): project_dir}
        
        while future_to_dir:
            done, _ = concurrent.futures.wait(future_to_dir.keys(), return_when=concurrent.futures.FIRST_COMPLETED)
            
            for future in done:
                dir_path = future_to_dir.pop(future)
                try:
                    res_dir, local_dirs, patterns, code_files = future.result()
                    
                    if patterns:
                        rel_dir = os.path.relpath(res_dir, project_dir)
                        if rel_dir == ".": rel_dir = "ROOT"
                        topology[rel_dir] = patterns
                        
                    all_code_files.extend(code_files)
                    
                    for d in local_dirs:
                        future_to_dir[executor.submit(scan_dir_worker, d, DEFAULT_EXCLUDE_DIRS, DEFAULT_CODE_EXTS, error_log_path)] = d
                except Exception as e:
                    log_error(f"FutureError processing {dir_path}: {e}", error_log_path)
                
                dirs_processed += 1
                if dirs_processed % 500 == 0:
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {project_name}: Processed {dirs_processed} dirs...")

    # Phase 2: Copy
    work_dir = os.path.abspath(os.path.join(args.root_dir, f".roverBckUp_work_{project_name}"))
    temp_code_dir = os.path.join(work_dir, "code")
    os.makedirs(temp_code_dir, exist_ok=True)

    print(f"[{project_name}] Copying {len(all_code_files)} code files...")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.threads) as executor:
        futures = [executor.submit(copy_worker, item, project_dir, temp_code_dir, error_log_path) for item in all_code_files]
        concurrent.futures.wait(futures)

    # Phase 3: Topology
    map_summary_path = os.path.join(work_dir, "map_topology.json")
    with open(map_summary_path, 'w', encoding='utf-8') as f:
        json.dump({"project_name": project_name, "source": project_dir, "topology": topology}, f, indent=2)

    # Phase 4: Tarball
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    tarball_filename = os.path.join(args.root_dir, f"{project_name}_codebase_{timestamp}.tar.gz")
    print(f"[{project_name}] Packaging into {tarball_filename}...")
    
    try:
        subprocess.run(["tar", "-czf", tarball_filename, "-C", work_dir, "map_topology.json", "code"], check=True)
    except Exception as e:
        log_error(f"TarError creating archive for {project_name}: {e}", error_log_path)
        set_project_status(conn, project_name, "FAILED_TAR")
        shutil.rmtree(work_dir, ignore_errors=True)
        return

    # Phase 5: Push to NAS
    print(f"[{project_name}] Pushing to {args.dest_nas}...")
    try:
        subprocess.run(["rsync", "--partial", "--progress", tarball_filename, args.dest_nas], check=True)
        set_project_status(conn, project_name, "DONE")
        print(f"[{project_name}] Transfer complete. Status marked DONE.")
        # Optional: remove local tarball after successful push to save space
        os.remove(tarball_filename)
    except Exception as e:
        log_error(f"RsyncError pushing {project_name}: {e}", error_log_path)
        set_project_status(conn, project_name, "FAILED_RSYNC")
            
    print(f"[{project_name}] Cleaning up work directory...")
    shutil.rmtree(work_dir, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="RoverBckUp: Robust HPC Folder Mapper")
    parser.add_argument("--root-dir", required=True, help="Root directory containing multiple project folders")
    parser.add_argument("--dest-nas", required=True, help="Destination on NAS for tarballs (e.g. user@host:/path)")
    parser.add_argument("--threads", type=int, default=16, help="Number of concurrent threads")
    parser.add_argument("--single-project", type=str, help="If provided, treats the root-dir as a single project with this name instead of iterating over its subfolders.")
    args = parser.parse_args()

    root_dir = os.path.abspath(args.root_dir)
    if not os.path.exists(root_dir):
        print(f"Error: Root directory '{root_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    db_path = os.path.join(root_dir, "roverBckUp_state.db")
    conn = init_db(db_path)
    error_log_path = os.path.join(root_dir, "roverBckUp_errors.log")
    
    print(f"Starting RoverBckUp on {root_dir} with {args.threads} threads.")
    print(f"Checkpoints will be saved to {db_path}")
    print(f"Errors will be logged to {error_log_path}")

    if getattr(args, 'single_project', None):
        status = get_project_status(conn, args.single_project)
        if status == "DONE":
            print(f"\nSkipping project '{args.single_project}': Already processed (Status: DONE)")
        else:
            process_project(root_dir, args.single_project, args, conn)
    else:
        # Iterate over top-level subdirectories (projects)
        for entry in os.scandir(root_dir):
            if entry.is_dir(follow_symlinks=False):
                project_name = entry.name
                project_dir = entry.path
                
                # Skip if explicitly excluded
                if project_name in DEFAULT_EXCLUDE_DIRS:
                    continue
                
                # Check state
                status = get_project_status(conn, project_name)
                if status == "DONE":
                    print(f"\nSkipping project '{project_name}': Already processed (Status: DONE)")
                    continue
                
                process_project(project_dir, project_name, args, conn)

    print("\nAll projects processed. RoverBckUp finished.")

if __name__ == "__main__":
    main()
