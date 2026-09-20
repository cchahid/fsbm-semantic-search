import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FSBM Semantic Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration & Paths ---
# Navigate up from backend/src/main.py -> backend/ -> root project folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DB_DIR = os.path.join(BASE_DIR, "nlp_engine", "chroma_data")

# --- Global Variables ---
client = None
collection = None
model = None


@app.on_event("startup")
async def startup_event():
    global client, collection, model
    print("[*] Starting API Server...")

    # 1. Connect to ChromaDB
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        collection = client.get_collection(name="fsbm_publications")
        print(f"[*] Connected to ChromaDB. Total documents: {collection.count()}")
    except Exception as e:
        print(f"[!] Error connecting to ChromaDB: {e}")

    # 2. Load the Embedding Model
    print("[*] Loading zembed-1 model... (This may take a minute)")
    try:
        model = SentenceTransformer("zeroentropy/zembed-1-embedding", trust_remote_code=True)
        print("[*] Model loaded successfully.")
    except Exception as e:
        print(f"[!] Error loading model: {e}")


@app.get("/")
def read_root():
    return {"status": "API is running", "model": "zembed-1", "database": "ChromaDB"}


@app.get("/search")
def search_articles(query: str, top_k: int = 5):
    if not model or not collection:
        raise HTTPException(status_code=500, detail="Database or Model not loaded.")

    print(f"[*] Processing search query: '{query}'")

    # 1. Convert the user's text query into a vector
    # This might take ~30 seconds on a standard CPU
    query_vector = model.encode([query])[0].tolist()

    # 2. Search ChromaDB using Cosine Similarity
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k
    )

    # 3. Format the results for the frontend
    formatted_results = []
    if results['ids']:
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "article_id": results['ids'][0][i],
                "distance": results['distances'][0][i],  # Lower distance = higher similarity
                "metadata": results['metadatas'][0][i],
                "abstract": results['documents'][0][i]
            })

    return {"query": query, "results": formatted_results}