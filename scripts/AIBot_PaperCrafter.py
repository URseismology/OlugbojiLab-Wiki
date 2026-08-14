import os
import sys
import json
import sqlite3
import hashlib
import paramiko
import re
import requests
import subprocess
import glob
import time
from pathlib import Path

# CONFIGURATION
NAS_HOST = 'repovibranium.earth.rochester.edu'
NAS_USER = 'administrator'
NAS_KEY = '/home/urseismoadmin/.ssh/id_rsa_nas'
NAS_REMOTE_DIRS = [
    'Drive/PaperpileBackup/Paperpile',
    'Drive/1.UofR_Seismology/All Papers'
]
LOCAL_WORK_DIR = '/home/urseismoadmin/AIBot_PaperCrafter'
DB_PATH = os.path.join(LOCAL_WORK_DIR, 'PaperCrafter_Index.db')
OLLAMA_API = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'qwen2.5:72b'

S2_API_KEY = 's2k-5b8Eu3Jn1qCoxgfUXDy87FPkJHWhMP4QkcEuyyX8'

os.makedirs(LOCAL_WORK_DIR, exist_ok=True)
os.makedirs(os.path.join(LOCAL_WORK_DIR, 'tmp'), exist_ok=True)
os.makedirs(os.path.join(LOCAL_WORK_DIR, 'jsonl_summaries'), exist_ok=True)
os.makedirs(os.path.join(LOCAL_WORK_DIR, 'full_texts'), exist_ok=True)
MASTER_JSONL = os.path.join(LOCAL_WORK_DIR, 'Master_PaperCrafter_Index.jsonl')

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            file_hash TEXT PRIMARY KEY,
            file_path TEXT,
            full_text_path TEXT,
            doi TEXT,
            title TEXT,
            journal TEXT,
            authors TEXT,
            publication_year INTEGER,
            cited_by_count INTEGER,
            semantic_scholar_citations INTEGER,
            summary TEXT,
            processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_citations ON papers(cited_by_count DESC)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_semantic_citations ON papers(semantic_scholar_citations DESC)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_year ON papers(publication_year DESC)')
    conn.commit()
    return conn

def extract_doi(text):
    # Less greedy regex to avoid catching URLs like /-/DCSupplemental
    doi_match = re.search(r'(10\.\d{4,9}/[A-Za-z0-9.-]+)', text)
    if doi_match:
        return doi_match.group(1).rstrip('.,;:')
    return None

def fetch_openalex_metadata(doi, fallback_title=None):
    if doi:
        url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    elif fallback_title:
        import urllib.parse
        encoded_title = urllib.parse.quote(fallback_title)
        url = f"https://api.openalex.org/works?filter=title.search:{encoded_title}"
    else:
        return {}
        
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # If we searched by title, we need to grab the first result
            if fallback_title:
                results = data.get('results', [])
                if not results:
                    return {}
                data = results[0]
                
            authors = [a.get('author', {}).get('display_name', '') for a in data.get('authorships', [])]
            return {
                'title': data.get('title'),
                'publication_year': data.get('publication_year'),
                'cited_by_count': data.get('cited_by_count'),
                'journal': data.get('primary_location', {}).get('source', {}).get('display_name', 'Unknown'),
                'authors': ', '.join(authors)
            }
    except Exception as e:
        print(f"OpenAlex Error: {e}")
    return {}

def fetch_semantic_scholar_citations(doi, title):
    import urllib.parse
    headers = {'x-api-key': S2_API_KEY}
    
    # Semantic Scholar strictly enforces 1 request per second. Backoff to be safe.
    time.sleep(1.2)
    
    try:
        if doi:
            url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=citationCount"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('citationCount')
        
        if title:
            # Fallback to title search
            encoded_title = urllib.parse.quote(title)
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_title}&fields=citationCount&limit=1"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    return data['data'][0].get('citationCount')
    except Exception as e:
        print(f"Semantic Scholar extraction failed: {e}")
    
    return None

def synthesize_summary(text, metadata):
    # Inject metadata if it exists
    meta_str = ""
    if metadata:
        meta_str = f"PAPER METADATA:\nTitle: {metadata.get('title')}\nAuthors: {metadata.get('authors')}\nCitations: {metadata.get('cited_by_count')}\n\n"
        
    # Start with the full text
    current_text = text
    
    while len(current_text) > 1000:
        prompt = f"{meta_str}Read the following academic paper text and provide a strict 3-sentence summary covering its core hypothesis, methodology, and conclusion:\n\n{current_text}"
        payload = {'model': OLLAMA_MODEL, 'prompt': prompt, 'stream': False}
        
        try:
            response = requests.post(OLLAMA_API, json=payload, timeout=600)
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                # If Ollama throws an error (e.g. context limit exceeded), halve the text and retry
                print(f"Ollama Error {response.status_code}. Truncating text and retrying...")
                current_text = current_text[:len(current_text)//2]
        except Exception as e:
            print(f"Ollama Connection Error: {e}")
            return "Failed to generate summary."
            
    return "Text was too short or continually failed."

def extract_text_with_marker(pdf_path):
    out_dir = os.path.join(LOCAL_WORK_DIR, 'tmp', 'marker_output')
    subprocess.run(['rm', '-rf', out_dir], check=False)
    
    # Run marker-pdf natively
    cmd = ['/home/urseismoadmin/papercrafter_env_312/bin/marker_single', pdf_path, out_dir]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        md_files = glob.glob(f"{out_dir}/*/*.md")
        if md_files:
            with open(md_files[0], 'r') as f:
                return f.read()
    except Exception as e:
        print(f"Marker extraction failed for {pdf_path}: {e}")
    return ""

def connect_sftp():
    key = paramiko.RSAKey.from_private_key_file(NAS_KEY)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=NAS_HOST, username=NAS_USER, pkey=key)
    return ssh.open_sftp()

def process_papers():
    conn = setup_db()
    c = conn.cursor()
    
    print("Connecting to NAS via SFTP...")
    sftp = connect_sftp()
    
    # We will just traverse NAS_REMOTE_DIRS iteratively (simplified for prototype)
    # A full recursive search would use SFTP traversal logic.
    print("Fetching file list from NAS...")
    # NOTE: Since SFTP recursive is slow, running SSH 'find' is faster
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=NAS_HOST, username=NAS_USER, pkey=paramiko.RSAKey.from_private_key_file(NAS_KEY))
    
    # Resolve absolute paths to fix SFTP relative path download bug
    stdin, stdout, stderr = ssh.exec_command('pwd')
    remote_pwd = stdout.read().decode('utf-8').strip()
    abs_dirs_quoted = [f'"{remote_pwd}/{d}"' for d in NAS_REMOTE_DIRS]
    
    print("Scanning NAS for PDFs...")
    stdin, stdout, stderr = ssh.exec_command(f'find {" ".join(abs_dirs_quoted)} -name "*.pdf" -type f')
    pdf_files = stdout.read().decode().splitlines()
    ssh.close()
    
    print(f"Found {len(pdf_files)} PDF files to process.")
    
    for remote_path in pdf_files:
        # Avoid processing macOS metadata
        if '/._' in remote_path: continue
            
        file_hash = hashlib.sha256(remote_path.encode()).hexdigest()
        
        # Check deduplication
        c.execute("SELECT file_hash FROM papers WHERE file_hash = ?", (file_hash,))
        if c.fetchone():
            continue
            
        print(f"Processing: {remote_path}")
        local_pdf = os.path.join(LOCAL_WORK_DIR, 'tmp', 'current.pdf')
        
        # Translate Synology SSH absolute path to SFTP chroot path
        sftp_path = remote_path.replace(remote_pwd, '/home')
        
        try:
            sftp.get(sftp_path, local_pdf)
        except Exception as e:
            print(f"SFTP fetch failed for {sftp_path}: {e}")
            continue
            
        full_text = extract_text_with_marker(local_pdf)
        if not full_text:
            print("No text extracted, skipping.")
            continue
            
        print(f"Extracted {len(full_text)} characters using GPU OCR.")
        
        # Extrapolate API Metadata
        doi = extract_doi(full_text)
        
        fallback_title = None
        if not doi:
            filename = os.path.basename(remote_path)
            fallback_title = filename.split('-')[0].strip() if '-' in filename else filename.replace('.pdf', '')
            
        metadata = fetch_openalex_metadata(doi, fallback_title)
        
        # Fetch Semantic Scholar citations
        s2_citations = fetch_semantic_scholar_citations(doi, metadata.get('title') or fallback_title)
        
        summary = synthesize_summary(full_text, metadata)
        
        md_path = os.path.join(LOCAL_WORK_DIR, 'full_texts', f"{file_hash}.md")
        
        c.execute('''
            INSERT INTO papers (file_hash, file_path, full_text_path, doi, title, journal, authors, publication_year, cited_by_count, semantic_scholar_citations, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (file_hash, remote_path, md_path, doi, metadata.get('title'), metadata.get('journal'), metadata.get('authors'), metadata.get('publication_year'), metadata.get('cited_by_count'), s2_citations, summary))
        conn.commit()
        
        # Save individual JSONL
        jsonl_data = {
            'file_hash': file_hash, 'file_path': remote_path, 'full_text_local_path': md_path, 'doi': doi,
            **metadata, 'semantic_scholar_citations': s2_citations, 'summary': summary
        }
        jsonl_path = os.path.join(LOCAL_WORK_DIR, 'jsonl_summaries', f"{file_hash}.jsonl")
        with open(jsonl_path, 'w') as f:
            f.write(json.dumps(jsonl_data) + '\n')
            
        # Append to Master JSONL
        with open(MASTER_JSONL, 'a') as f:
            f.write(json.dumps(jsonl_data) + '\n')
            
        # Save Full Markdown Text
        md_path = os.path.join(LOCAL_WORK_DIR, 'full_texts', f"{file_hash}.md")
        with open(md_path, 'w') as f:
            f.write(full_text)
            
        print(f"Completed! DB, JSON, and MD saved.")
        
    sftp.close()

if __name__ == '__main__':
    process_papers()
