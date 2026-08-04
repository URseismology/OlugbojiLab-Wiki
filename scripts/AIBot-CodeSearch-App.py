import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
import sqlite3
import os
import tarfile
import shutil
import time

CHROMA_DB_PATH = "/home/urseismoadmin/codesearch_db"
NAS_CODE_DIR = "/mnt/ADAMA-Shared/GodModeData/CodeBaseFull"
WORKSPACE_DIR = "/home/urseismoadmin/AIBot_workdir/export_workspace"

st.set_page_config(page_title="LabAI Code Explorer", layout="wide")
st.title("🔬 LabAI Codebase Explorer & Prototyping Engine")

@st.cache_resource
def get_db_client():
    return chromadb.PersistentClient(path=CHROMA_DB_PATH)

@st.cache_resource
def get_collection():
    client = get_db_client()
    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text"
    )
    return client.get_collection(name="lab_codebase", embedding_function=ollama_ef)

collection = get_collection()

query = st.text_input("🔍 Semantic Search (e.g. 'code for calculating Hilbert-Huang transform')")

def extract_file_from_tar(project, file_path):
    # Find the right tarball (assuming project name matches the prefix of the tarball)
    tarballs = [f for f in os.listdir(NAS_CODE_DIR) if f.startswith(project) and f.endswith(".tar.gz")]
    if not tarballs:
        return "Error: Could not find the source tarball for this project."
    
    tarball_path = os.path.join(NAS_CODE_DIR, tarballs[0])
    
    try:
        with tarfile.open(tarball_path, "r:gz") as tar:
            # We need to find the exact member. Sometimes the path in tar has a leading dir
            members = tar.getmembers()
            for member in members:
                if member.name.endswith(file_path):
                    f = tar.extractfile(member)
                    if f:
                        content = f.read().decode('utf-8')
                        return content
            return f"Error: File '{file_path}' not found inside the tarball."
    except Exception as e:
        return f"Error extracting file: {e}"

def export_to_workspace(project, file_path, content):
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    out_name = f"{project}_{os.path.basename(file_path)}"
    out_path = os.path.join(WORKSPACE_DIR, out_name)
    with open(out_path, "w") as f:
        f.write(content)
    return out_path

if query:
    st.write("Searching embeddings...")
    results = collection.query(
        query_texts=[query],
        n_results=10
    )
    
    if results['documents']:
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        
        for i, (doc, meta) in enumerate(zip(docs, metas)):
            project = meta['project']
            path = meta['path']
            obj_type = meta['type']
            
            with st.expander(f"[{obj_type.upper()}] {project} - {path}"):
                st.markdown(f"**Summary:**\n\n{doc.split('Summary: ')[-1].split('Type:')[0]}")
                
                if obj_type == "file":
                    if st.button(f"Extract & View Code", key=f"view_{i}"):
                        code = extract_file_from_tar(project, path)
                        st.code(code, language="python" if path.endswith(".py") else "matlab")
                        
                        export_path = export_to_workspace(project, path, code)
                        st.success(f"✅ Exported to {export_path} for Cloud AI Agents!")
