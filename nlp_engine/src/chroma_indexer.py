import os
import json
import pandas as pd
import chromadb
from tqdm import tqdm

# Define paths relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PIPELINE_DIR = os.path.join(os.path.dirname(BASE_DIR), "data_pipeline")

GOLD_FILE = os.path.join(DATA_PIPELINE_DIR, "data", "processed", "fsbm_researchers_vectors.parquet")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_data")  # Where the DB files will live
RAW_DATA_FILE = os.path.join(DATA_PIPELINE_DIR, "data", "raw", "fsbm_researchers_raw.json")


def _first_non_empty(*values, default=""):
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default


def _to_int(value, default=0):
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


def _parse_authors(value):
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


def _build_article_lookup():
    if not os.path.exists(RAW_DATA_FILE):
        return {}

    try:
        with open(RAW_DATA_FILE, "r", encoding="utf-8") as handle:
            researchers = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}

    lookup = {}
    for researcher in researchers:
        researcher_name = _first_non_empty(researcher.get("nom_complet"))
        for article in researcher.get("articles", []):
            article_id = _first_non_empty(article.get("article_id"))
            if not article_id:
                continue
            authors = _parse_authors(article.get("auteurs"))
            lookup[article_id] = {
                "title": _first_non_empty(article.get("titre"), default=article_id),
                "authors": authors,
                "author_display": ", ".join(authors) if authors else researcher_name,
                "year": _first_non_empty(article.get("date_publication"), default="N/A"),
                "citations": _to_int(article.get("citations"), default=0),
                "chercheur_id": _first_non_empty(researcher.get("chercheur_id"), default=""),
                "nom_complet": researcher_name,
            }
    return lookup


def build_vector_database():
    print(f"[*] Starting ChromaDB Indexing Process...")

    if not os.path.exists(GOLD_FILE):
        print(f"[!] Gold Parquet file not found at: {GOLD_FILE}")
        return

    # 1. Load the Gold Dataset
    df = pd.read_parquet(GOLD_FILE)
    print(f"[*] Loaded {len(df)} vectorized articles.")
    article_lookup = _build_article_lookup()
    print(f"[*] Loaded {len(article_lookup)} article records from raw lookup.")

    # 2. Initialize ChromaDB Persistent Client
    # This creates a folder (chroma_data) and saves SQLite/vector files inside it
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

    # Create a collection using cosine similarity (standard for sentence-transformers)
    collection = client.get_or_create_collection(
        name="fsbm_publications",
        metadata={"hnsw:space": "cosine"}
    )

    print(f"[*] Connected to ChromaDB Collection: 'fsbm_publications'")

    # 3. Prepare data batches for ChromaDB
    # We must convert pandas columns to flat Python lists
    ids = df["article_id"].astype(str).tolist()
    embeddings = df["embedding_zembed1"].tolist()
    documents = df["abstract_clean"].tolist()

    # Create metadata dicts (must handle missing dates safely)
    metadatas = []
    for _, row in df.iterrows():
        article_id = _first_non_empty(row.get("article_id"))
        lookup_data = article_lookup.get(article_id, {})

        title = _first_non_empty(
            row.get("title"),
            row.get("titre"),
            lookup_data.get("title"),
            article_id,
        )
        authors = _parse_authors(row.get("authors")) or _parse_authors(row.get("auteurs")) or lookup_data.get("authors", [])
        author_display = ", ".join(authors) if authors else _first_non_empty(
            row.get("nom_complet"),
            lookup_data.get("author_display"),
            lookup_data.get("nom_complet"),
            default="Unknown author",
        )
        year = _first_non_empty(row.get("year"), row.get("date_publication"), lookup_data.get("year"), default="N/A")
        citations = _to_int(row.get("citations"), default=_to_int(lookup_data.get("citations"), default=0))
        researcher_id = _first_non_empty(row.get("chercheur_id"), lookup_data.get("chercheur_id"), default="")

        metadatas.append({
            # Canonical keys (consumed by backend/frontend)
            "title": title,
            "authors": author_display,
            "year": year,
            "citations": citations,
            "chercheur_id": researcher_id,
            "Laboratoire": _first_non_empty(row.get("Laboratoire"), default="Unknown"),
            "Equipe": _first_non_empty(row.get("Equipe"), default="Unknown"),
            "journal": _first_non_empty(row.get("journal"), default=""),
            "pdf_url": _first_non_empty(row.get("pdf_url"), default=""),

            # Legacy keys (kept for compatibility)
            "titre": title,
            "nom_complet": author_display,
            "date_publication": year,
        })

    # 4. Insert into ChromaDB (Batching to avoid memory spikes)
    batch_size = 500
    print(f"[*] Inserting {len(ids)} documents into ChromaDB...")

    for i in tqdm(range(0, len(ids), batch_size)):
        # Use upsert so repeated indexing runs refresh metadata/embeddings safely.
        collection.upsert(
            ids=ids[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            documents=documents[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size]
        )

    print(f"\n[+] Success! All vectors indexed in ChromaDB.")
    print(f"[+] Database saved locally at: {CHROMA_DB_DIR}")


if __name__ == "__main__":
    build_vector_database()
