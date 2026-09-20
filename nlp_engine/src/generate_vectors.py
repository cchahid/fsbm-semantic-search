import os
import pandas as pd
from sentence_transformers import SentenceTransformer

# Define paths dynamically based on your project structure
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PIPELINE_DIR = os.path.join(os.path.dirname(BASE_DIR), "data_pipeline")

# Input from the cleaner
SILVER_FILE = os.path.join(DATA_PIPELINE_DIR, "data", "processed", "fsbm_researchers_clean.parquet")
# Output to be used by ChromaDB
GOLD_FILE = os.path.join(DATA_PIPELINE_DIR, "data", "processed", "fsbm_researchers_vectors.parquet")


def generate_embeddings():
    print("[*] Starting NLP Vectorization Process (Silver -> Gold)...")

    # 1. Load the cleaned dataset
    if not os.path.exists(SILVER_FILE):
        print(f"[!] Cleaned dataset not found at {SILVER_FILE}")
        return

    df = pd.read_parquet(SILVER_FILE)
    print(f"[*] Loaded {len(df)} articles for vectorization.")

    # 2. Load the Embedding Model
    # Using the official Hugging Face path for the zembed-1 model
    model_name = "zeroentropy/zembed-1-embedding"

    try:
        print(f"[*] Loading transformer model: {model_name}...")
        # trust_remote_code=True is sometimes required for new or custom model architectures
        model = SentenceTransformer(model_name, trust_remote_code=True)
    except Exception as e:
        print(f"[!] Failed to load model '{model_name}'.")
        print(f"    Error: {e}")
        print("    Fallback: Using 'all-MiniLM-L6-v2' (lighter model) for demonstration.")
        model = SentenceTransformer("all-MiniLM-L6-v2")

    # 3. Generate Vectors
    # Concatenate the Title and Abstract for richer semantic context
    df['text_to_embed'] = "Title: " + df['titre'].astype(str) + " . Abstract: " + df['abstract_clean'].astype(str)
    abstracts = df['text_to_embed'].tolist()

    print(f"[*] Encoding {len(abstracts)} abstracts... (This may take a minute depending on your CPU/GPU)")

    # encode() handles batching automatically. batch_size=32 prevents RAM overflow.
    # show_progress_bar gives you a nice visual in the PyCharm terminal.
    # encode() handles batching automatically.
    embeddings = model.encode(abstracts, batch_size=32, show_progress_bar=True)

    # 4. Attach Vectors to the DataFrame
    # Convert the numpy arrays to standard Python lists so they save perfectly in Parquet
    df['embedding_zembed1'] = embeddings.tolist()

    # 5. Save the Gold Layer
    df.to_parquet(GOLD_FILE, index=False)

    vector_dim = len(df['embedding_zembed1'].iloc[0])

    print(f"\n[+] Success! All abstracts vectorized.")
    print(f"[+] Vector Dimension: {vector_dim}")
    print(f"[+] Gold layer saved to: {GOLD_FILE}")


if __name__ == "__main__":
    generate_embeddings()