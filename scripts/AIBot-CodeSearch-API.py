from fastapi import FastAPI
import chromadb
from chromadb.utils import embedding_functions

app = FastAPI()

CHROMA_DB_PATH = "/home/urseismoadmin/codesearch_db"
try:
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url="http://127.0.0.1:11434/api/embeddings",
        model_name="nomic-embed-text"
    )
    collection = client.get_collection(name="lab_codebase", embedding_function=ollama_ef)
except Exception as e:
    collection = None
    print("DB Init Error:", e)

@app.get("/search")
def search(q: str):
    if not collection:
        return {"error": "Database not initialized"}
    try:
        results = collection.query(
            query_texts=[q],
            n_results=3
        )
        if not results['documents'] or not results['documents'][0]:
            return {"results": []}
            
        return {"results": results['documents'][0]}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Listen on docker host interface so openwebui can reach it
    uvicorn.run(app, host="0.0.0.0", port=8502)
