import time
import random
import uuid
from scholarly import scholarly


def scrape_scholar_profile(author_name: str, author_id: str, max_articles: int = 15) -> dict:
    """
    Scrapes a Google Scholar profile and its top publications.
    """
    print(f"[*] Fetching Google Scholar profile directly for ID: {author_id}")

    try:
        # 1. Fetch the author directly by their unique ID
        author_raw = scholarly.search_author_id(author_id)

        # ADD THIS SAFETY CHECK:
        if not author_raw:
            print(f"    [!] Blocked by Google (CAPTCHA) or profile not found for ID: {author_id}")
            return {}

        print(f"[*] Found profile: {author_raw.get('name', author_name)}. Fetching detailed metrics...")

        # 2. Fill the profile with metrics and publication list
        author = scholarly.fill(author_raw, sections=['basics', 'indices', 'publications'])

        # 3. Initialize the JSON structure
        researcher_data = {
            "chercheur_id": author_id,
            "nom_complet": author.get("name", author_name),
            "affiliation": author.get("affiliation", "Unknown"),
            "metriques": {
                "citations_totales": author.get("citedby", 0),
                "h_index": author.get("hindex", 0),
                "i10_index": author.get("i10index", 0)
            },
            "articles": []
        }

        # Handle cases where the author has fewer articles than max_articles
        pubs_to_fetch = author.get('publications', [])[:max_articles]
        total_pubs = len(pubs_to_fetch)

        print(f"[*] Fetching top {total_pubs} articles (with rate limiting)...")

        # 4. Loop through publications and extract abstracts
        for i, pub in enumerate(pubs_to_fetch):
            print(f"    -> [{i + 1}/{total_pubs}] Fetching article: {pub['bib'].get('title')}")

            try:
                # Fill the publication to get the abstract
                pub_filled = scholarly.fill(pub)
                bib = pub_filled.get("bib", {})

                # Extract authors safely
                author_string = bib.get("author", "")
                auteurs_list = [a.strip() for a in author_string.split(" and ") if a.strip()] if author_string else []

                # Build the article dictionary
                article_data = {
                    "article_id": pub_filled.get("author_pub_id", f"art_{uuid.uuid4().hex[:8]}"),
                    "titre": bib.get("title", "No Title"),
                    "auteurs": auteurs_list,
                    "date_publication": str(bib.get("pub_year", "Unknown")),
                    "journal": bib.get("journal", bib.get("citation", "Unknown Source")),
                    "citations": pub_filled.get("num_citations", 0),
                    "abstract": bib.get("abstract", ""),
                    "abstract_clean": "",
                    "embedding_zembed1": []
                }

                researcher_data["articles"].append(article_data)

            except Exception as pub_error:
                print(f"    [!] Skipping article due to error: {pub_error}")

            # CRITICAL: Rate Limiting (Polite scraping to avoid IP Ban)
            time.sleep(random.uniform(2.5, 5.5))

        return researcher_data

    except Exception as e:
        print(f"[!] An error occurred fetching profile {author_id}: {e}")
        return {}