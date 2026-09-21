import pandas as pd
import json
import os
import re
import unicodedata

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRONZE_FILE = os.path.join(BASE_DIR, "data", "raw", "fsbm_researchers_raw.json")
SILVER_FILE = os.path.join(BASE_DIR, "data", "processed", "fsbm_researchers_clean.parquet")
REF_FILE = os.path.join(BASE_DIR, "data", "references", "fsbm_departments.csv")
ENRICHMENT_FILE = os.path.join(BASE_DIR, "data", "raw", "openalex_enrichment.json") # <-- NEW PATH


def clean_text(text):
    """Basic NLP text normalization for abstracts."""
    if not isinstance(text, str) or not text.strip():
        return ""
    text = text.lower()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^\w\s\.,;-]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def normalize_name_for_join(name):
    """
    Creates a universal matching key immune to First/Last name swapping,
    accents, and punctuation.
    """
    if not isinstance(name, str):
        return ""

    # 1. Remove accents (é -> e)
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')

    # 2. Replace anything that isn't a letter with a space
    name = re.sub(r'[^a-zA-Z\s]', ' ', name)

    # 3. Lowercase, split into words, sort alphabetically, and join
    words = name.lower().split()
    words.sort()

    return "".join(words)


def process_incremental_batch():
    print("[*] Starting Cleaning Process (Bronze -> Silver)...")

    # 1. Safely load the Bronze data (Raw JSON)
    try:
        with open(BRONZE_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[!] Cannot read raw data. Try again in a few seconds.\nError: {e}")
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

    df_bronze = df_bronze.drop_duplicates(subset=["article_id"], keep="last")

    # 2. Clean the complete Bronze dataset
    os.makedirs(os.path.dirname(SILVER_FILE), exist_ok=True)
    print(f"[*] Processing {len(df_bronze)} scraped articles...")

    df_bronze["abstract_raw"] = df_bronze["abstract_raw"].fillna("").astype(str)
    df_clean = df_bronze[df_bronze["abstract_raw"].str.strip() != ""].copy()
    df_clean["abstract_clean"] = df_clean["abstract_raw"].apply(clean_text)

    df_clean["auteurs"] = df_clean["auteurs"].apply(lambda x: x if isinstance(x, list) else [])
    df_clean["auteurs_str"] = df_clean["auteurs"].apply(lambda x: ", ".join(x))

    # ---------------------------------------------------------
    # Merge with Reference Data (Departments)
    # ---------------------------------------------------------
    if os.path.exists(REF_FILE):
        print("[*] Merging with reference department data...")
        df_ref = pd.read_csv(REF_FILE)

        df_clean['join_key'] = df_clean['nom_complet'].apply(normalize_name_for_join)
        df_ref['join_key'] = df_ref['Enseignant Chercheur'].apply(normalize_name_for_join)

        df_ref_subset = df_ref[['join_key', 'Etablissement', 'Laboratoire', 'Equipe']].drop_duplicates(
            subset=['join_key'])

        df_clean = df_clean.merge(df_ref_subset, on='join_key', how='left')

        df_clean['Etablissement'] = df_clean['Etablissement'].fillna("Unknown")
        df_clean['Laboratoire'] = df_clean['Laboratoire'].fillna("Unknown")
        df_clean['Equipe'] = df_clean['Equipe'].fillna("Unknown")
        df_clean = df_clean.drop(columns=['join_key'])
    else:
        print(f"[!] Warning: Reference file not found at {REF_FILE}. Department columns will be missing.")

    # ---------------------------------------------------------
    # NEW LOGIC: Merge with OpenAlex Enrichment Data
    # ---------------------------------------------------------
    if os.path.exists(ENRICHMENT_FILE):
        print("[*] Merging with OpenAlex enrichment data (PDF URLs and References)...")
        try:
            with open(ENRICHMENT_FILE, "r", encoding="utf-8") as f:
                enrich_data = json.load(f)

            # Convert JSON dict to Pandas DataFrame
            if isinstance(enrich_data, dict):
                df_enrich = pd.DataFrame.from_dict(enrich_data, orient='index')
            elif isinstance(enrich_data, list):
                df_enrich = pd.DataFrame(enrich_data)
            else:
                df_enrich = pd.DataFrame()

            if not df_enrich.empty and 'article_id' in df_enrich.columns:
                # Isolate target columns to avoid overlapping duplicates
                cols_to_keep = ['article_id']
                if 'pdf_url' in df_enrich.columns: cols_to_keep.append('pdf_url')
                if 'references' in df_enrich.columns: cols_to_keep.append('references')

                df_enrich_subset = df_enrich[cols_to_keep].drop_duplicates(subset=['article_id'])

                # Perform Left Join mapping on article_id
                df_clean = df_clean.merge(df_enrich_subset, on='article_id', how='left')

                # Clean missing data (NaN) gracefully
                if 'pdf_url' in df_clean.columns:
                    df_clean['pdf_url'] = df_clean['pdf_url'].fillna("")
                if 'references' in df_clean.columns:
                    df_clean['references'] = df_clean['references'].apply(lambda x: x if isinstance(x, list) else [])

        except Exception as e:
            print(f"[!] Failed to merge enrichment data: {e}")
    else:
        print(f"[*] Enrichment file not found at {ENRICHMENT_FILE}. Initializing empty schema columns.")
        # Ensure schema consistency for downstream processing if enrichment hasn't run yet
        df_clean['pdf_url'] = ""
        df_clean['references'] = [[] for _ in range(len(df_clean))]
    # ---------------------------------------------------------

    df_clean.to_parquet(SILVER_FILE, index=False)
    print(f"[+] Success! Silver layer rebuilt with {len(df_clean)} articles ready for vectorization.")


if __name__ == "__main__":
    process_incremental_batch()