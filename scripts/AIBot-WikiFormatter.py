#!/usr/bin/env python3
import os
import sqlite3
import re

DB_PATH = "/home/urseismoadmin/AIBot_workdir/AIBot-WikiCrafter_state.db"
NAS_WIKI_DIR = "/mnt/ADAMA-Shared/GodModeData/Wikis"

def build_tree(paths):
    tree = {}
    for p in paths:
        parts = p.split('/')
        current = tree
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]
    return tree

def format_tree(tree, prefix=''):
    lines = []
    keys = sorted(list(tree.keys()))
    for i, k in enumerate(keys):
        is_last = (i == len(keys) - 1)
        connector = '└── ' if is_last else '├── '
        child_prefix = '    ' if is_last else '│   '
        
        lines.append(prefix + connector + k + ("/" if tree[k] else ""))
        if tree[k]:
            lines.extend(format_tree(tree[k], prefix + child_prefix))
    return lines

def get_ascii_tree_for_project(project_name):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT file_path FROM file_summaries WHERE project=?", (project_name,))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return None
            
        paths = [row[0] for row in rows]
        tree = build_tree(paths)
        
        ascii_lines = format_tree(tree)
        return "```text\n" + project_name + "/\n" + "\n".join(ascii_lines) + "\n```"
    except Exception as e:
        print(f"Error reading DB for {project_name}: {e}")
        return None

def update_markdown_file(filepath, ascii_tree):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check if already contains ASCII tree characters
    if "├──" in content or "└──" in content:
        print(f"  Skipping {os.path.basename(filepath)} - Already contains ASCII tree.")
        return False
        
    # Regex to match the section.
    pattern = re.compile(r'(##\s*(?:\d+\.)?\s*Data Architecture.*?)(?=\n##\s|\Z)', re.IGNORECASE | re.DOTALL)
    
    match = pattern.search(content)
    if match:
        original_section = match.group(1)
        header_match = re.match(r'(##\s*(?:\d+\.)?\s*Data Architecture[^\n]*\n)', original_section, re.IGNORECASE)
        header = header_match.group(1) if header_match else "## 2. Data Architecture\n"
        
        new_section = f"{header}\n{ascii_tree}\n"
        
        new_content = content[:match.start()] + new_section + content[match.end():]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  Updated {os.path.basename(filepath)} successfully.")
        return True
    else:
        print(f"  Could not find 'Data Architecture' section in {os.path.basename(filepath)}.")
        return False

def main():
    print("Starting AIBot-WikiFormatter...")
    if not os.path.exists(NAS_WIKI_DIR):
        print(f"Error: {NAS_WIKI_DIR} not found.")
        return
        
    for item in os.listdir(NAS_WIKI_DIR):
        proj_dir = os.path.join(NAS_WIKI_DIR, item)
        if os.path.isdir(proj_dir):
            home_md = os.path.join(proj_dir, "Home.md")
            if os.path.exists(home_md):
                print(f"Processing project: {item}")
                tree_text = get_ascii_tree_for_project(item)
                if tree_text:
                    update_markdown_file(home_md, tree_text)
                else:
                    print(f"  No database records found for {item}.")

if __name__ == "__main__":
    main()
