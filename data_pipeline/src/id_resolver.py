import time
import random
from scholarly import scholarly


def fuzzy_find_scholar_id(raw_name: str, affiliation_keywords: list) -> str:
    # 1. Split "FIRST.LAST" into parts
    parts = raw_name.split('.')
    if len(parts) < 2:
        return None

    first_name_pdf = parts[0].lower()
    last_name_pdf = parts[-1].lower()

    print(f"[*] Searching Google Scholar broadly for last name: '{last_name_pdf.upper()}'...")

    try:
        # 2. Search ONLY by the last name to bypass exact-match formatting issues
        search_query = scholarly.search_author(last_name_pdf)

        # 3. Iterate through the first 15 results looking for our researcher
        for _ in range(15):
            try:
                author = next(search_query)
            except StopIteration:
                break  # No more results

            fetched_name = author.get('name', '').lower()
            affiliation = author.get('affiliation', '').lower()

            # 4. Filter 1: Does the affiliation match FSBM / Casablanca?
            if any(keyword in affiliation for keyword in affiliation_keywords):

                # 5. Filter 2: Does the first name roughly match?
                # (e.g., check if 'habib' is in 'elhabib' or vice-versa)
                first_name_fetched = fetched_name.split()[0]

                if first_name_fetched in first_name_pdf or first_name_pdf in first_name_fetched:
                    print(f"    [+] MATCH FOUND! PDF Name: '{raw_name}' -> Scholar Name: '{author['name']}'")
                    print(f"        -> Scholar ID: {author['scholar_id']}")
                    return author['scholar_id']

        print(f"    [!] No match found for {raw_name} after filtering results.")
        return None

    except Exception as e:
        print(f"    [!] Error during search: {e}")
        return None


if __name__ == "__main__":
    # Test names exactly as they appear in the PDF
    test_names = [
        "ELHABIB.BENLAHMAR",  # From PDF Line 202
        "ABDELHAK.CHAKLI",  # From PDF Line 1
        "AHMED.EDDAOUI"  # From PDF Line 5
    ]

    # Keywords to prove they belong to the university
    fsbm_keywords = ["casablanca", "hassan", "m'sik", "fsbm", "uh2c"]

    mapping_results = {}

    for name in test_names:
        scholar_id = fuzzy_find_scholar_id(name, fsbm_keywords)
        if scholar_id:
            mapping_results[name] = scholar_id

        # Rate limit to avoid blocks
        sleep_time = random.uniform(3.0, 6.0)
        time.sleep(sleep_time)

    print("\n[*] Final Mapping Result:")
    import json

    print(json.dumps(mapping_results, indent=4))