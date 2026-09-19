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
    print("[*] Starting Incremental Cleaning Process (Bronze -> Silver)...")

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
                "date_publication": article.get("date_publication"),
                "abstract_raw": article.get("abstract")
            })

    df_bronze = pd.DataFrame(flattened_articles)
    if df_bronze.empty:
        print("[*] Bronze layer is empty. Nothing to process.")
        return

    # 2. Check the Silver layer to find the Delta (New data)
    os.makedirs(os.path.dirname(SILVER_FILE), exist_ok=True)

    if os.path.exists(SILVER_FILE):
        df_silver = pd.read_parquet(SILVER_FILE)
        existing_article_ids = set(df_silver["article_id"].dropna())

        # Isolate only the rows in Bronze that are NOT in Silver
        df_delta = df_bronze[~df_bronze["article_id"].isin(existing_article_ids)].copy()
        print(f"[*] Found {len(existing_article_ids)} articles in Silver layer.")
    else:
        df_delta = df_bronze.copy()
        df_silver = pd.DataFrame()
        print("[*] Silver layer not found. Creating a new one.")

    if df_delta.empty:
        print("[*] No new articles to clean. Silver layer is completely up to date.")
        return

    print(f"[*] Processing {len(df_delta)} NEW articles...")

    # 3. Clean the Delta Batch
    # Remove rows with absolutely no abstract (cannot be vectorized later)
    df_delta = df_delta[df_delta['abstract_raw'].str.strip() != ""]

    # Apply text normalization to abstracts
    df_delta['abstract_clean'] = df_delta['abstract_raw'].apply(clean_text)

    # 4. Append and Save to Silver (Parquet format)
    df_final = pd.concat([df_silver, df_delta], ignore_index=True)
    df_final.to_parquet(SILVER_FILE, index=False)

    print(f"[+] Success! Cleaned {len(df_delta)} new articles.")
    print(f"[+] Silver layer now contains {len(df_final)} total articles ready for vectorization.")


if __name__ == "__main__":
    process_incremental_batch()