import pandas as pd
import json
import os
import re
import unicodedata


# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRONZE_FILE = os.path.join(BASE_DIR, "data", "raw", "fsbm_researchers_raw.json")
SILVER_FILE = os.path.join(BASE_DIR, "data", "processed", "fsbm_researchers_clean.parquet")
REF_FILE = os.path.join(BASE_DIR, "data", "references", "fsbm_departments.csv")  # <-- NEW PATH


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
    # Example: "Chakli Abdelhak" -> ['abdelhak', 'chakli'] -> "abdelhakchakli"
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
    # NEW LOGIC: Merge with Reference Data (PDF Extraction)
    # ---------------------------------------------------------
    if os.path.exists(REF_FILE):
        print("[*] Merging with reference department data...")
        df_ref = pd.read_csv(REF_FILE)

        # --- OVERRIDE EDGE CASES ---
        # Map the exact Google Scholar name to the exact PDF name
        manual_name_fixes = {
            "Habib BEN LAHMAR": "ELHABIB.BENLAHMAR",
            "Aziza ElBakali Kassimi": "AZIZA.ELBAKALI",
        }

        # Apply the mapping to the 'nom_complet' column
        df_clean['nom_complet'] = df_clean['nom_complet'].replace(manual_name_fixes)
        # ---------------------------

        # Create matching keys
        df_clean['join_key'] = df_clean['nom_complet'].apply(normalize_name_for_join)
        df_ref['join_key'] = df_ref['Enseignant Chercheur'].apply(normalize_name_for_join)

        # Keep only necessary columns from the reference file
        df_ref_subset = df_ref[['join_key', 'Etablissement', 'Laboratoire', 'Equipe']].drop_duplicates(
            subset=['join_key'])

        # Perform Left Join
        df_clean = df_clean.merge(df_ref_subset, on='join_key', how='left')

        # Handle missing matches
        df_clean['Etablissement'] = df_clean['Etablissement'].fillna("Unknown")
        df_clean['Laboratoire'] = df_clean['Laboratoire'].fillna("Unknown")
        df_clean['Equipe'] = df_clean['Equipe'].fillna("Unknown")

        # Drop the temporary join key
        df_clean = df_clean.drop(columns=['join_key'])
    else:
        print(f"[!] Warning: Reference file not found at {REF_FILE}. Department columns will be missing.")
    # ---------------------------------------------------------

    df_clean.to_parquet(SILVER_FILE, index=False)
    print(f"[+] Success! Silver layer rebuilt with {len(df_clean)} articles ready for vectorization.")


if __name__ == "__main__":
    process_incremental_batch()