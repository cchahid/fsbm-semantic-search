import pandas as pd
import json
import os
import re

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRONZE_FILE = os.path.join(BASE_DIR, "data", "raw", "fsbm_researchers_raw.json")
SILVER_FILE = os.path.join(BASE_DIR, "data", "processed", "fsbm_researchers_clean.parquet")


def clean_text(text):
    """Basic NLP text normalization for abstracts."""
    if not isinstance(text, str) or not text.strip():
        return ""
    # Lowercase
    text = text.lower()
    # Remove HTML tags and special characters (keep basic punctuation)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^\w\s\.,;-]', '', text)
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def process_incremental_batch():
    print("[*] Starting Cleaning Process (Bronze -> Silver)...")

    # 1. Safely load the Bronze data (Raw JSON)
    try:
        with open(BRONZE_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(
            f"[!] Cannot read raw data (Scraper might be writing to it right now). Try again in a few seconds.\nError: {e}")
        return

    # Flatten the hierarchical JSON into a tabular format for Pandas
    flattened_articles = []
    for researcher in raw_data:
        for article in researcher.get("articles", []):
            flattened_articles.append({
                "chercheur_id": researcher.get("chercheur_id"),
                "nom_complet": researcher.get("nom_complet"),
                "article_id": article.get("article_id"),
                "titre": article.get("titre"),
                "auteurs": article.get("auteurs", []),
                "date_publication": article.get("date_publication"),
                "citations": article.get("citations", 0),
                "journal": article.get("journal"),
                "abstract_raw": article.get("abstract")
            })

    df_bronze = pd.DataFrame(flattened_articles)
    if df_bronze.empty:
        print("[*] Bronze layer is empty. Nothing to process.")
        return

    # Keep the latest duplicate by article_id if any accidental duplicates exist in raw data.
    df_bronze = df_bronze.drop_duplicates(subset=["article_id"], keep="last")

    # 2. Clean the complete Bronze dataset.
    # For this project size, rebuilding Silver from source of truth is safer than incremental patching.
    os.makedirs(os.path.dirname(SILVER_FILE), exist_ok=True)
    print(f"[*] Processing {len(df_bronze)} scraped articles...")

    # Remove rows with no abstract (cannot be vectorized later)
    df_bronze["abstract_raw"] = df_bronze["abstract_raw"].fillna("").astype(str)
    df_clean = df_bronze[df_bronze["abstract_raw"].str.strip() != ""].copy()

    # Normalize text for embeddings
    df_clean["abstract_clean"] = df_clean["abstract_raw"].apply(clean_text)

    # Normalize authors to a stable display string
    df_clean["auteurs"] = df_clean["auteurs"].apply(
        lambda authors: authors if isinstance(authors, list) else []
    )
    df_clean["auteurs_str"] = df_clean["auteurs"].apply(lambda authors: ", ".join(authors))

    df_clean.to_parquet(SILVER_FILE, index=False)

    print(f"[+] Success! Silver layer rebuilt with {len(df_clean)} articles ready for vectorization.")


if __name__ == "__main__":
    process_incremental_batch()
