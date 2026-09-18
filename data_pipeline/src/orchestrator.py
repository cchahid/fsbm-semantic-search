import json
import os
import time
import random
from scholarly import scholarly, ProxyGenerator
from scraper import scrape_scholar_profile

# Define paths relative to the src folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, "data", "target_researchers.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "raw", "fsbm_researchers_raw.json")


def setup_proxies():
    print("[*] Fetching and configuring free proxies... (This may take a minute)")
    pg = ProxyGenerator()
    # Scrapes free proxy lists and tests them
    success = pg.FreeProxies()
    if success:
        scholarly.use_proxy(pg)
        print("[*] Proxy configured successfully! Hiding real IP.")
    else:
        print("[!] Warning: Could not find working free proxies. Proceeding with real IP.")


def main():
    # 1. Setup Proxies (Optional: comment this out if using your real IP with long delays)
    setup_proxies()

    if not os.path.exists(INPUT_FILE):
        print(f"[!] Input file not found at {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        researchers = json.load(f)

    print(f"[*] Loaded {len(researchers)} target profiles.")

    all_scraped_data = []
    scraped_ids = set()

    # --- UPDATED: RESUME CAPABILITY USING ID ---
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as out_f:
                all_scraped_data = json.load(out_f)
                # Extract the unique IDs instead of the names
                scraped_ids = {str(item.get("chercheur_id", "")) for item in all_scraped_data}
            print(f"[*] Found {len(all_scraped_data)} profiles already scraped. Resuming...")
        except Exception as e:
            print(f"[*] No valid existing output found or error parsing: {e}")
            all_scraped_data = []
    # --------------------------------

    for index, researcher in enumerate(researchers):
        raw_name = researcher.get("nom_complet")
        author_id = researcher.get("chercheur_id")

        print(f"\n==================================================")
        print(f"[*] Processing Profile {index + 1}/{len(researchers)}: {raw_name}")
        print(f"==================================================")

        # --- UPDATED: SKIP LOGIC USING ID ---
        # Simply check if the unique ID is already in our saved list
        if author_id in scraped_ids:
            print(f"[*] Skipping {raw_name} - Already successfully scraped.")
            continue
        # -------------------------

        # Scrape the profile
        profile_data = scrape_scholar_profile(author_name=raw_name, author_id=author_id, max_articles=15)

        if profile_data:
            all_scraped_data.append(profile_data)

            # Add the newly scraped ID to the set
            scraped_ids.add(author_id)

            with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
                json.dump(all_scraped_data, out_f, indent=2, ensure_ascii=False)

            print(f"[*] Saved data for {raw_name} to raw/ folder.")

        if index < len(researchers) - 1:
            pause = random.uniform(5.0, 10.0)
            print(f"[*] Sleeping for {pause:.2f} seconds before next profile...")
            time.sleep(pause)


if __name__ == "__main__":
    main()