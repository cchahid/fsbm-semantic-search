import os
import time
import requests
import json
import urllib.parse
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "fsbm_researchers_clean.parquet")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "raw", "openalex_enrichment.json")


def run_openalex_enrichment():
    print(f"[*] Loading data from {INPUT_FILE}...")
    df = pd.read_parquet(INPUT_FILE)

    # Safely load existing progress to prevent duplicate API calls
    existing_data = {}
    if os.path.exists(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    existing_data = {str(item["article_id"]): item for item in data if "article_id" in item}
                elif isinstance(data, dict):
                    existing_data = data
            except json.JSONDecodeError:
                print("[!] Cache file corrupted. Starting fresh.")

    print(f"[*] Found {len(existing_data)} previously processed articles in cache.")

    new_records_count = 0
    total_articles = len(df)

    if total_articles == 0:
        print("[!] No articles found in the Parquet file. Exiting.")
        return

    print(f"[*] Starting OpenAlex queries for {total_articles} total articles across all faculty...\n")

    for i, (index, row) in enumerate(df.iterrows(), start=1):
        title = str(row.get("titre", "")).strip()
        article_id = str(row.get("article_id", ""))
        chercheur_id = str(row.get("chercheur_id", ""))

        if not title or title.lower() == "nan":
            continue

        if article_id in existing_data:
            continue

        safe_title = urllib.parse.quote(title)
        api_url = f"https://api.openalex.org/works?search={safe_title}&api_key={os.getenv('OPENALEX_API_KEY')}"

        try:
            print(f"[{i}/{total_articles}] Searching: {title[:75]}...")
            response = requests.get(api_url, timeout=(5, 10))

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                pdf_url = None
                references = []

                if results:
                    best_match = results[0]
                    references = best_match.get("referenced_works", [])
                    oa_info = best_match.get("open_access", {})

                    if oa_info.get("is_oa") and oa_info.get("oa_url"):
                        pdf_url = oa_info["oa_url"]
                        print(f"    [+] Found PDF URL: {pdf_url}")
                    else:
                        print(f"    [-] Found paper, but no Open Access PDF available.")
                else:
                    print(f"    [-] No match found in OpenAlex.")

                existing_data[article_id] = {
                    "chercheur_id": chercheur_id,
                    "article_id": article_id,
                    "titre": title,
                    "pdf_url": pdf_url,
                    "references": references
                }
                new_records_count += 1

                # Save incrementally after each successful lookup
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, indent=4, ensure_ascii=False)

            else:
                print(f"    [!] API Error {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            print(f"    [!] Timeout. Will retry on next run.")
        except Exception as e:
            print(f"    [!] Request error: {e}")

        time.sleep(0.15)

    print(f"\n[+] Enrichment complete! Added {new_records_count} new records.")
    print(f"[+] Total cached records: {len(existing_data)}")


if __name__ == "__main__":
    run_openalex_enrichment()