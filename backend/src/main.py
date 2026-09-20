import json
import os
from typing import Any

import chromadb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer

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
RAW_DATA_FILE = os.path.join(BASE_DIR, "data_pipeline", "data", "raw", "fsbm_researchers_raw.json")

# --- Global Variables ---
client = None
collection = None
model = None
article_lookup = {}


def _first_non_empty(*values: Any, default: str = "") -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default


def _to_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _parse_authors(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        authors = [str(author).strip() for author in value if str(author).strip()]
        return authors

    text = str(value).strip()
    if not text:
        return []

    if " and " in text:
        return [chunk.strip() for chunk in text.split(" and ") if chunk.strip()]
    if "," in text:
        return [chunk.strip() for chunk in text.split(",") if chunk.strip()]

    return [text]


def _load_article_lookup() -> dict[str, dict[str, Any]]:
    if not os.path.exists(RAW_DATA_FILE):
        print(f"[!] Raw data file not found: {RAW_DATA_FILE}")
        return {}

    try:
        with open(RAW_DATA_FILE, "r", encoding="utf-8") as handle:
            researchers = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[!] Failed to load raw data file: {exc}")
        return {}

    lookup: dict[str, dict[str, Any]] = {}
    for researcher in researchers:
        researcher_name = _first_non_empty(researcher.get("nom_complet"), default="Unknown author")
        for article in researcher.get("articles", []):
            article_id = _first_non_empty(article.get("article_id"))
            if not article_id:
                continue

            authors = _parse_authors(article.get("auteurs"))
            if not authors and researcher_name:
                authors = [researcher_name]

            lookup[article_id] = {
                "title": _first_non_empty(article.get("titre"), default=article_id),
                "authors": authors,
                "year": _first_non_empty(article.get("date_publication"), default="N/A"),
                "citations": _to_int(article.get("citations"), default=0),
                "abstract_raw": _first_non_empty(article.get("abstract")),
            }

    return lookup


@app.on_event("startup")
async def startup_event():
    global client, collection, model, article_lookup
    print("[*] Starting API Server...")

    # 1. Connect to ChromaDB
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        collection = client.get_collection(name="fsbm_publications")
        print(f"[*] Connected to ChromaDB. Total documents: {collection.count()}")
    except Exception as e:
        print(f"[!] Error connecting to ChromaDB: {e}")

    article_lookup = _load_article_lookup()
    print(f"[*] Loaded {len(article_lookup)} article records from raw data lookup.")

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
    if results["ids"]:
        for i in range(len(results["ids"][0])):
            article_id = str(results["ids"][0][i])
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            metadata = metadata or {}
            lookup_data = article_lookup.get(article_id, {})

            title = _first_non_empty(
                metadata.get("title"),
                metadata.get("titre"),
                lookup_data.get("title"),
                article_id,
            )

            authors = _parse_authors(
                metadata.get("authors")
                or metadata.get("auteurs")
                or metadata.get("author")
                or metadata.get("nom_complet")
                or lookup_data.get("authors")
            )
            if not authors:
                authors = ["Unknown author"]

            year = _first_non_empty(
                metadata.get("year"),
                metadata.get("publication_year"),
                metadata.get("date_publication"),
                lookup_data.get("year"),
                default="N/A",
            )

            citations = _to_int(
                metadata.get("citations")
                or metadata.get("citation_count")
                or lookup_data.get("citations"),
                default=0,
            )

            distance = results["distances"][0][i] if results.get("distances") else None
            match_score = None
            if isinstance(distance, (int, float)):
                match_score = round(max(0.0, min(1.0, 1 - distance)) * 100)

            abstract_text = _first_non_empty(
                lookup_data.get("abstract_raw"),
                results["documents"][0][i] if results.get("documents") else "",
                default="",
            )

            formatted_results.append({
                "id": article_id,
                "article_id": article_id,
                "title": title,
                "authors": authors,
                "author_display": ", ".join(authors),
                "year": year,
                "citations": citations,
                "match_score": match_score,
                "distance": distance,  # Lower distance = higher similarity
                "metadata": metadata,
                "abstract": abstract_text,
            })

    return {"query": query, "results": formatted_results}
