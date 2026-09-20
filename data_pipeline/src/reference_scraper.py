import os
import time
import requests
import json
import urllib.parse
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "fsbm_researchers_clean.parquet")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "raw", "openalex_references.json")


def run_reference_scraper():
    print(f"[*] Loading data from {INPUT_FILE}...")
    if not os.path.exists(INPUT_FILE):
        print(f"[!] Input file not found at {INPUT_FILE}")
        return

    df = pd.read_parquet(INPUT_FILE)

    # Safely load existing progress to prevent duplicate API calls (handles both dict and list formats)
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

    print(f"[*] Found {len(existing_data)} previously processed articles in reference cache.")

    new_records_count = 0
    total_articles = len(df)

    if total_articles == 0:
        print("[!] No articles found in the Parquet file. Exiting.")
        return

    print(f"[*] Starting OpenAlex reference queries for {total_articles} total articles...\n")

    for i, (index, row) in enumerate(df.iterrows(), start=1):
        title = str(row.get("titre", "")).strip()
        article_id = str(row.get("article_id", ""))
        chercheur_id = str(row.get("chercheur_id", ""))

        if not title or title.lower() == "nan":
            continue

        if article_id in existing_data:
            continue

        safe_title = urllib.parse.quote(title)
        api_url = f"https://api.openalex.org/works?search={safe_title}&api_key=u0ze90oxjDOFOnxstk34yP"

        try:
            print(f"[{i}/{total_articles}] Fetching references for: {title[:70]}...")
            response = requests.get(api_url, timeout=(5, 10))

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                references = []
                openalex_id = None
                cited_by_count = 0

                if results:
                    best_match = results[0]
                    openalex_id = best_match.get("id")
                    cited_by_count = best_match.get("cited_by_count", 0)
                    references = best_match.get("referenced_works", [])
                    print(f"    [+] Found {len(references)} references (OpenAlex ID: {openalex_id})")
                else:
                    print(f"    [-] No match found in OpenAlex.")

                existing_data[article_id] = {
                    "chercheur_id": chercheur_id,
                    "article_id": article_id,
                    "titre": title,
                    "openalex_id": openalex_id,
                    "cited_by_count": cited_by_count,
                    "references": references,
                    "reference_count": len(references)
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

    print(f"\n[+] Reference scraping complete! Added {new_records_count} new records.")
    print(f"[+] Total cached records in {OUTPUT_FILE}: {len(existing_data)}")


if __name__ == "__main__":
    run_reference_scraper()