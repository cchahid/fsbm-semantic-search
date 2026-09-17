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
    # 1. Setup Proxies before doing anything else
    setup_proxies()

    # 2. Load the target researchers
    if not os.path.exists(INPUT_FILE):
        print(f"[!] Input file not found at {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        researchers = json.load(f)

    print(f"[*] Loaded {len(researchers)} target profiles.")

    all_scraped_data = []

    # 3. Loop through each researcher
    for index, researcher in enumerate(researchers):
        name = researcher.get("nom_complet")
        author_id = researcher.get("chercheur_id")

        print(f"\n==================================================")
        print(f"[*] Processing Profile {index + 1}/{len(researchers)}: {name}")
        print(f"==================================================")

        # Scrape the profile
        profile_data = scrape_scholar_profile(author_name=name, author_id=author_id, max_articles=15)

        if profile_data:
            all_scraped_data.append(profile_data)

            with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
                json.dump(all_scraped_data, out_f, indent=2, ensure_ascii=False)

            print(f"[*] Saved data for {name} to raw/ folder.")

        if index < len(researchers) - 1:
            pause = random.uniform(5.0, 10.0)
            print(f"[*] Sleeping for {pause:.2f} seconds before next profile...")
            time.sleep(pause)


if __name__ == "__main__":
    main()