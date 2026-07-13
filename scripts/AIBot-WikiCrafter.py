#!/usr/bin/env python3
import os
import sys
import json
import time
import shutil
import tarfile
import sqlite3
import urllib.request
import datetime
import logging

# --- CONFIGURATION ---
NAS_CODE_DIR = "/mnt/ADAMA-Shared/GodModeData/CodeBaseFull"
NAS_WIKI_DIR = "/mnt/ADAMA-Shared/GodModeData/Wikis"
POLL_INTERVAL_SECONDS = 600

OLLAMA_URL = "http://localhost:11434/api/generate"
CODE_MODEL = "deepseek-coder-v2:latest"
SYNTHESIS_MODEL = "qwen2.5:72b"

WORK_DIR = "/home/urseismoadmin/AIBot_workdir"
DB_PATH = os.path.join(WORK_DIR, "AIBot-WikiCrafter_state.db")
LOG_PATH = os.path.join(WORK_DIR, "AIBot-WikiCrafter.log")

os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(NAS_WIKI_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def log_print(msg):
    print(msg)
    logging.info(msg)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS processed (filename TEXT PRIMARY KEY, processed_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS file_summaries (project TEXT, file_path TEXT, summary TEXT, PRIMARY KEY(project, file_path))''')
    c.execute('''CREATE TABLE IF NOT EXISTS folder_summaries (project TEXT, folder_path TEXT, summary TEXT, PRIMARY KEY(project, folder_path))''')
    c.execute('''CREATE TABLE IF NOT EXISTS subsystem_summaries (project TEXT, folder_path TEXT, summary TEXT, PRIMARY KEY(project, folder_path))''')
    conn.commit()
    return conn

def is_processed(conn, filename):
    c = conn.cursor()
    c.execute("SELECT 1 FROM processed WHERE filename=?", (filename,))
    return c.fetchone() is not None

def mark_processed(conn, filename):
    c = conn.cursor()
    c.execute("INSERT INTO processed (filename, processed_at) VALUES (?, ?)", (filename, datetime.datetime.now().isoformat()))
    conn.commit()

def get_summary(conn, table, project, path):
    c = conn.cursor()
    c.execute(f"SELECT summary FROM {table} WHERE project=? AND path_col=?", (project, path))
    row = c.fetchone()
    return row[0] if row else None

def set_summary(conn, table, project, path, summary):
    c = conn.cursor()
    c.execute(f"INSERT OR REPLACE INTO {table} (project, path_col, summary) VALUES (?, ?, ?)", (project, path, summary))
    conn.commit()

def ask_ollama(model, prompt):
    data = {"model": model, "prompt": prompt, "stream": False}
    req = urllib.request.Request(OLLAMA_URL, json.dumps(data).encode('utf-8'))
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=1800) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", "").strip()
    except Exception as e:
        log_print(f"  [ERROR] Ollama request failed: {e}")
        return ""

def summarize_file(conn, project, file_path, code_content):
    # Check cache
    c = conn.cursor()
    c.execute("SELECT summary FROM file_summaries WHERE project=? AND file_path=?", (project, file_path))
    row = c.fetchone()
    if row: return row[0]
    
    # Chunk if massive
    if len(code_content) > 30000:
        code_content = code_content[:30000] + "\n...[TRUNCATED TO SAVE GPU CONTEXT]"
        
    prompt = f"Analyze this script ({file_path}) and provide a concise 3-sentence summary of its exact function, inputs, and outputs.\n\nCODE:\n{code_content}"
    log_print(f"    -> [File Map] Analyzing {os.path.basename(file_path)} (Prompt: {len(prompt)} chars)...")
    summary = ask_ollama(CODE_MODEL, prompt)
    
    if summary:
        c.execute("INSERT INTO file_summaries (project, file_path, summary) VALUES (?, ?, ?)", (project, file_path, summary))
        conn.commit()
    return summary

def summarize_local_folder(conn, project, folder_path, file_summaries):
    if not file_summaries: return ""
    
    c = conn.cursor()
    c.execute("SELECT summary FROM folder_summaries WHERE project=? AND folder_path=?", (project, folder_path))
    row = c.fetchone()
    if row: return row[0]

    prompt = f"Here are the summaries of all scripts located directly in the directory '{folder_path}'. Write a single unified paragraph explaining what this specific directory accomplishes.\n\n"
    for path, summ in file_summaries.items():
        prompt += f"--- {os.path.basename(path)} ---\n{summ}\n\n"
        
    log_print(f"   -> [Folder Reduce] Synthesizing local scripts in {folder_path}...")
    summary = ask_ollama(CODE_MODEL, prompt)
    
    if summary:
        c.execute("INSERT INTO folder_summaries (project, folder_path, summary) VALUES (?, ?, ?)", (project, folder_path, summary))
        conn.commit()
    return summary

def summarize_subsystem(conn, project, folder_path, local_folder_summary, child_subsystem_summaries):
    c = conn.cursor()
    c.execute("SELECT summary FROM subsystem_summaries WHERE project=? AND folder_path=?", (project, folder_path))
    row = c.fetchone()
    if row: return row[0]
    
    prompt = f"You are an expert software architect analyzing a codebase subsystem located at '{folder_path}'.\n"
    
    if local_folder_summary:
        prompt += f"Here is the summary of the scripts stored directly in this root folder:\n{local_folder_summary}\n\n"
        
    if child_subsystem_summaries:
        prompt += "Here are the summaries of the sub-directories (modules) inside this folder:\n"
        for child, summ in child_subsystem_summaries.items():
            prompt += f"--- Sub-module: {os.path.basename(child)} ---\n{summ}\n\n"
            
    prompt += "Synthesize this information into a high-level overview of this entire subsystem and how its components interact. Be extremely concise but comprehensive (max 2 paragraphs)."
    
    log_print(f"  -> [Subsystem Bubble-up] Synthesizing subsystem '{folder_path}'...")
    summary = ask_ollama(SYNTHESIS_MODEL, prompt)
    
    if summary:
        c.execute("INSERT INTO subsystem_summaries (project, folder_path, summary) VALUES (?, ?, ?)", (project, folder_path, summary))
        conn.commit()
    return summary

def recursive_process_folder(conn, project, code_root, current_rel_path):
    current_abs_path = os.path.join(code_root, current_rel_path) if current_rel_path != "ROOT" else code_root
    
    # 1. Process files in this directory directly
    file_summaries = {}
    child_folders = []
    
    for item in os.listdir(current_abs_path):
        item_path = os.path.join(current_abs_path, item)
        if os.path.isfile(item_path):
            rel_item = os.path.relpath(item_path, code_root)
            try:
                with open(item_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                file_summaries[rel_item] = summarize_file(conn, project, rel_item, content)
            except Exception:
                pass
        elif os.path.isdir(item_path):
            child_folders.append(item)
            
    # 2. Get local folder summary
    local_summary = summarize_local_folder(conn, project, current_rel_path, file_summaries)
    
    # 3. Recursively process children
    child_subsystem_summaries = {}
    for child in child_folders:
        child_rel = os.path.relpath(os.path.join(current_abs_path, child), code_root)
        child_summary = recursive_process_folder(conn, project, code_root, child_rel)
        if child_summary:
            child_subsystem_summaries[child_rel] = child_summary
            
    # 4. Bubble up subsystem summary
    subsystem_summary = summarize_subsystem(conn, project, current_rel_path, local_summary, child_subsystem_summaries)
    return subsystem_summary

def process_tarball(conn, filename):
    log_print(f"\n--- Starting Map-Reduce processing for {filename} ---")
    local_tarball = os.path.join(NAS_CODE_DIR, filename)
    extract_dir = os.path.join(WORK_DIR, f"extracted_{filename.replace('.tar.gz', '')}")
    
    try:
        log_print(f"Extracting directly from NAS mount to {extract_dir}...")
        os.makedirs(extract_dir, exist_ok=True)
        with tarfile.open(local_tarball, "r:gz") as tar:
            tar.extractall(path=extract_dir)
            
        map_path = os.path.join(extract_dir, "map_topology.json")
        topology_summary = "No Data Topology Found."
        project_name = filename.split("_codebase_")[0]
        
        if os.path.exists(map_path):
            log_print("Parsing hierarchical data topology...")
            with open(map_path, 'r') as f:
                map_data = json.load(f)
            project_name = map_data.get("project_name", project_name)
            top_level = map_data.get("topology", {})
            topology_summary = f"Mapped Directories: {len(top_level)}\n\n"
            for dir_name, patterns in top_level.items():
                topology_summary += f"- {dir_name}/\n"
                for pat, stats in patterns.items():
                    topology_summary += f"    {pat} ({stats['count']} files, {stats['size']/1024/1024:.2f} MB)\n"
                
        # --- MAP-REDUCE PIPELINE ---
        code_dir = os.path.join(extract_dir, "code")
        root_summary = ""
        
        if os.path.exists(code_dir):
            log_print("Starting Recursive Map-Reduce Pipeline...")
            root_summary = recursive_process_folder(conn, project_name, code_dir, "ROOT")
            
        # --- FINAL EDITORIAL SYNTHESIS ---
        log_print("Synthesizing final polished Wiki with Qwen2.5...")
        draft_prompt = "You are the Editor-in-Chief for our Lab's AI documentation system. Using the highly compressed summary of the entire codebase and the raw data topology, write a comprehensive, professional, highly-polished Markdown Wiki for this project designed to onboard new team members.\n\n"
        draft_prompt += f"### Data Topology (What files exist and where):\n{topology_summary}\n\n"
        draft_prompt += f"### Complete Codebase Architecture Overview:\n{root_summary}\n\n"
        draft_prompt += "Structure the Wiki beautifully with:\n"
        draft_prompt += "1. Project Overview\n2. Data Architecture (explain the data patterns)\n3. Code Reference (how the scripts work and connect to the data)\n4. Workflows (how data flows through the scripts)."
        
        wiki_content = ask_ollama(SYNTHESIS_MODEL, draft_prompt)
        
        # --- Export & NAS Sync ---
        final_wiki_dir = os.path.join(NAS_WIKI_DIR, project_name)
        os.makedirs(final_wiki_dir, exist_ok=True)
        wiki_file_path = os.path.join(final_wiki_dir, "Home.md")
        
        with open(wiki_file_path, 'w', encoding='utf-8') as wf:
            wf.write(wiki_content)
            
        log_print(f"Wiki published successfully to {wiki_file_path}")

    except Exception as e:
        log_print(f"Error processing {filename}: {e}")
    finally:
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)

def list_remote_tarballs():
    if not os.path.exists(NAS_CODE_DIR):
        return []
    return [f for f in os.listdir(NAS_CODE_DIR) if f.endswith(".tar.gz") and "_codebase_" in f]

def main():
    log_print("Starting AIBot-WikiCrafter Daemon (Map-Reduce V4)...")
    conn = init_db()
    
    while True:
        log_print(f"\n[{datetime.datetime.now().isoformat()}] Polling NAS for new payloads...")
        tarballs = list_remote_tarballs()
        
        for tb in tarballs:
            if not is_processed(conn, tb):
                log_print(f"Found new payload: {tb}")
                process_tarball(conn, tb)
                mark_processed(conn, tb)
                
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
