import os
import pandas as pd
import chromadb
from tqdm import tqdm

# Define paths relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PIPELINE_DIR = os.path.join(os.path.dirname(BASE_DIR), "data_pipeline")

GOLD_FILE = os.path.join(DATA_PIPELINE_DIR, "data", "processed", "fsbm_researchers_vectors.parquet")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_data")  # Where the DB files will live


def build_vector_database():
    print(f"[*] Starting ChromaDB Indexing Process...")

    if not os.path.exists(GOLD_FILE):
        print(f"[!] Gold Parquet file not found at: {GOLD_FILE}")
        return

    # 1. Load the Gold Dataset
    df = pd.read_parquet(GOLD_FILE)
    print(f"[*] Loaded {len(df)} vectorized articles.")

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
        metadatas.append({
            "titre": str(row.get("titre", "Titre inconnu")),
            "nom_complet": str(row.get("nom_complet", "Auteur inconnu")),
            "chercheur_id": str(row.get("chercheur_id", "")),
            "date_publication": str(row.get("date_publication", "N/A"))
        })

    # 4. Insert into ChromaDB (Batching to avoid memory spikes)
    batch_size = 500
    print(f"[*] Inserting {len(ids)} documents into ChromaDB...")

    for i in tqdm(range(0, len(ids), batch_size)):
        collection.add(
            ids=ids[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            documents=documents[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size]
        )

    print(f"\n[+] Success! All vectors indexed in ChromaDB.")
    print(f"[+] Database saved locally at: {CHROMA_DB_DIR}")


if __name__ == "__main__":
    build_vector_database()