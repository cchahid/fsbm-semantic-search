import json
import os
import re
from typing import Any

import chromadb
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
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
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DB_DIR = os.path.join(BASE_DIR, "nlp_engine", "chroma_data")
RAW_DATA_FILE = os.path.join(BASE_DIR, "data_pipeline", "data", "raw", "fsbm_researchers_raw.json")
ENRICHMENT_FILE = os.path.join(BASE_DIR, "data_pipeline", "data", "raw", "openalex_enrichment.json")
PDF_DIRECTORY = os.path.join(BASE_DIR, "data_pipeline", "data", "raw", "pdf's")
if not os.path.isdir(PDF_DIRECTORY):
    PDF_DIRECTORY = os.path.join(BASE_DIR, "data_pipeline", "data", "raw", "pdfs")

if os.path.isdir(PDF_DIRECTORY):
    app.mount("/pdfs", StaticFiles(directory=PDF_DIRECTORY), name="pdfs")
else:
    print(f"[!] Local PDF directory not found: {PDF_DIRECTORY}")

# --- Global Variables ---
client = None
collection = None
model = None
article_lookup: dict[str, dict[str, Any]] = {}
faculty_profiles: list[dict[str, Any]] = []


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
        return [str(author).strip() for author in value if str(author).strip()]

    text = str(value).strip()
    if not text:
        return []
    if " and " in text:
        return [chunk.strip() for chunk in text.split(" and ") if chunk.strip()]
    if "," in text:
        return [chunk.strip() for chunk in text.split(",") if chunk.strip()]

    return [text]


def _derive_department(affiliation: str) -> str:
    text = (affiliation or "").strip()
    if not text:
        return "FSBM Research Faculty"

    professor_match = re.search(r"professor in ([^,]+)", text, flags=re.IGNORECASE)
    if professor_match:
        return f"{professor_match.group(1).strip().title()} Department"

    lowered = text.lower()
    keyword_map = [
        ("computer", "Computer Science Department"),
        ("informatics", "Computer Science Department"),
        ("data", "Data Science Department"),
        ("math", "Mathematics Department"),
        ("physics", "Physics Department"),
        ("chem", "Chemistry Department"),
        ("bio", "Biology Department"),
        ("geology", "Earth Sciences Department"),
    ]
    for keyword, department in keyword_map:
        if keyword in lowered:
            return department

    return "FSBM Research Faculty"


def _load_raw_researchers() -> list[dict[str, Any]]:
    if not os.path.exists(RAW_DATA_FILE):
        print(f"[!] Raw data file not found: {RAW_DATA_FILE}")
        return []

    try:
        with open(RAW_DATA_FILE, "r", encoding="utf-8") as handle:
            rows = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[!] Failed to load raw data file: {exc}")
        return []

    if not isinstance(rows, list):
        return []
    return rows


def _load_pdf_urls() -> dict[str, str]:
    if not os.path.exists(ENRICHMENT_FILE):
        return {}
    try:
        with open(ENRICHMENT_FILE, "r", encoding="utf-8") as handle:
            enrichment = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[!] Failed to load PDF enrichment data: {exc}")
        return {}

    rows = enrichment.values() if isinstance(enrichment, dict) else enrichment
    return {
        str(row.get("article_id")): str(row.get("pdf_url")).strip()
        for row in rows
        if isinstance(row, dict) and row.get("article_id") and str(row.get("pdf_url", "")).strip()
    }


def _build_article_lookup(researchers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
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


def _build_faculty_profiles(researchers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []

    for researcher in researchers:
        metrics = researcher.get("metriques", {}) or {}
        name = _first_non_empty(researcher.get("nom_complet"), default="Unknown researcher")
        affiliation = _first_non_empty(researcher.get("affiliation"), default="FSBM")
        publications = researcher.get("articles", []) if isinstance(researcher.get("articles"), list) else []

        top_publication = ""
        top_citations = 0
        if publications:
            best_article = max(publications, key=lambda row: _to_int(row.get("citations"), default=0))
            top_publication = _first_non_empty(best_article.get("titre"))
            top_citations = _to_int(best_article.get("citations"), default=0)

        profiles.append({
            "id": _first_non_empty(researcher.get("chercheur_id"), default=name.lower().replace(" ", "-")),
            "name": name,
            "department": _derive_department(affiliation),
            "affiliation": affiliation,
            "citations_total": _to_int(metrics.get("citations_totales"), default=0),
            "h_index": _to_int(metrics.get("h_index"), default=0),
            "i10_index": _to_int(metrics.get("i10_index"), default=0),
            "publications_count": len(publications),
            "top_publication": top_publication,
            "top_publication_citations": top_citations,
        })

    profiles.sort(
        key=lambda row: (
            row.get("citations_total", 0),
            row.get("h_index", 0),
            row.get("i10_index", 0),
        ),
        reverse=True,
    )
    return profiles


@app.on_event("startup")
async def startup_event():
    global client, collection, model, article_lookup, faculty_profiles
    print("[*] Starting API Server...")

    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        collection = client.get_collection(name="fsbm_publications")
        print(f"[*] Connected to ChromaDB. Total documents: {collection.count()}")
    except Exception as exc:
        print(f"[!] Error connecting to ChromaDB: {exc}")

    researchers = _load_raw_researchers()
    article_lookup = _build_article_lookup(researchers)
    for article_id, pdf_url in _load_pdf_urls().items():
        article_lookup.setdefault(article_id, {})["pdf_url"] = pdf_url
    faculty_profiles = _build_faculty_profiles(researchers)
    print(f"[*] Loaded {len(article_lookup)} article records from raw data lookup.")
    print(f"[*] Loaded {len(faculty_profiles)} faculty profiles.")

    print("[*] Loading zembed-1 model... (This may take a minute)")
    try:
        model = SentenceTransformer("zeroentropy/zembed-1-embedding", trust_remote_code=True)
        print("[*] Model loaded successfully.")
    except Exception as exc:
        print(f"[!] Error loading model: {exc}")


@app.get("/")
def read_root():
    return {"status": "API is running", "model": "zembed-1", "database": "ChromaDB"}


@app.get("/faculty-profiles")
def get_faculty_profiles():
    return {"count": len(faculty_profiles), "profiles": faculty_profiles}


@app.get("/search")
def search_articles(query: str, top_k: int = 5):
    if not model or not collection:
        raise HTTPException(status_code=500, detail="Database or Model not loaded.")

    print(f"[*] Processing search query: '{query}'")

    query_vector = model.encode([query])[0].tolist()
    results = collection.query(query_embeddings=[query_vector], n_results=top_k)

    formatted_results = []
    if results["ids"]:
        for i in range(len(results["ids"][0])):
            article_id = str(results["ids"][0][i])
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            lookup_data = article_lookup.get(article_id, {})
            metadata = dict(metadata or {})
            for key in ("chercheur_id", "Laboratoire", "Equipe", "journal", "pdf_url"):
                if not metadata.get(key) and lookup_data.get(key):
                    metadata[key] = lookup_data[key]

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
                "distance": distance,
                "metadata": metadata,
                "abstract": abstract_text,
            })

    return {"query": query, "results": formatted_results}
