import sqlite3
import chromadb
from chromadb.utils import embedding_functions
import os
import time

SQLITE_DB_PATH = "/home/urseismoadmin/AIBot_workdir/AIBot-WikiCrafter_state.db"
CHROMA_DB_PATH = "/home/urseismoadmin/codesearch_db"

def main():
    print(f"Connecting to SQLite DB at {SQLITE_DB_PATH}...")
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"Error: Database {SQLITE_DB_PATH} does not exist.")
        return

    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    # Get file summaries
    cursor.execute("SELECT project, file_path, summary FROM file_summaries")
    file_rows = cursor.fetchall()
    
    # Get folder summaries
    cursor.execute("SELECT project, folder_path, summary FROM folder_summaries")
    folder_rows = cursor.fetchall()
    
    print(f"Found {len(file_rows)} file summaries and {len(folder_rows)} folder summaries.")

    print(f"Connecting to ChromaDB at {CHROMA_DB_PATH}...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Use Ollama for embeddings
    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text"
    )

    # Get or create collection
    collection = client.get_or_create_collection(
        name="lab_codebase",
        embedding_function=ollama_ef
    )

    documents = []
    metadatas = []
    ids = []

    # Process files
    for project, file_path, summary in file_rows:
        doc_id = f"file_{project}_{file_path}"
        content = f"Project: {project}\nFile Path: {file_path}\nSummary: {summary}\nType: File"
        
        documents.append(content)
        metadatas.append({"project": project, "path": file_path, "type": "file"})
        ids.append(doc_id)

    # Process folders
    for project, folder_path, summary in folder_rows:
        doc_id = f"folder_{project}_{folder_path}"
        content = f"Project: {project}\nFolder Path: {folder_path}\nSummary: {summary}\nType: Folder"
        
        documents.append(content)
        metadatas.append({"project": project, "path": folder_path, "type": "folder"})
        ids.append(doc_id)

    if not documents:
        print("No documents found to index.")
        return

    # Upsert in batches to avoid overwhelming Ollama
    batch_size = 500
    total = len(documents)
    
    print(f"Indexing {total} items into ChromaDB using nomic-embed-text...")
    for i in range(0, total, batch_size):
        end = min(i + batch_size, total)
        print(f"Upserting batch {i} to {end}...")
        
        batch_docs = documents[i:end]
        batch_metas = metadatas[i:end]
        batch_ids = ids[i:end]
        
        # We manually retry if Ollama is busy
        success = False
        attempts = 0
        while not success and attempts < 3:
            try:
                collection.upsert(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
                success = True
            except Exception as e:
                attempts += 1
                print(f"Error on batch {i}-{end}: {e}. Retrying {attempts}/3 in 5s...")
                time.sleep(5)
                
        if not success:
            print(f"Failed to index batch {i}-{end} after 3 attempts.")
            
    print("Indexing complete!")
    print(f"Total documents in collection: {collection.count()}")

if __name__ == "__main__":
    main()
