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
        author_raw = scholarly.search_author_id(author_id)

        if not author_raw:
            print(f"    [!] Blocked by Google (CAPTCHA) or profile not found for ID: {author_id}")
            return {}

        print(f"[*] Found profile: {author_raw.get('name', author_name)}. Fetching detailed metrics...")

        author = scholarly.fill(author_raw, sections=['basics', 'indices', 'publications'])

        # Hardened check against NoneType returns
        if not author:
            print(f"    [!] Google returned empty data for {author_id}. Likely rate limited.")
            return {}

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

        pubs_to_fetch = author.get('publications', [])[:max_articles]
        total_pubs = len(pubs_to_fetch)

        print(f"[*] Fetching top {total_pubs} articles (with rate limiting)...")

        for i, pub in enumerate(pubs_to_fetch):
            print(f"    -> [{i + 1}/{total_pubs}] Fetching article: {pub.get('bib', {}).get('title')}")

            bib = pub.get("bib", {})  # Fallback base
            abstract_text = ""
            eprint_url = None  # Initialize at the top

            try:
                # 1. Fill the publication ONCE
                pub_filled = scholarly.fill(pub)
                bib = pub_filled.get("bib", {})
                abstract_text = bib.get("abstract", "")

                # Extract eprint_url immediately while we have the filled object
                eprint_url = pub_filled.get("eprint_url", None)

            except AttributeError as pub_err:
                print(f"    [*] DOM Error on profile. Attempting fallback global search for abstract...")
                try:
                    title = pub.get("bib", {}).get("title", "")
                    if title:
                        search_iterator = scholarly.search_pubs(title)
                        fallback_pub = next(search_iterator)
                        bib = fallback_pub.get("bib", {})
                        abstract_text = bib.get("abstract", "")
                        # Note: We usually don't get the eprint_url reliably from a global search fallback,
                        # so we leave it as None and let OpenAlex handle it later.
                        time.sleep(random.uniform(1.5, 3.0))
                except Exception as fallback_err:
                    print(f"    [!] Fallback failed with error: {fallback_err}")
            except Exception as pub_error:
                print(f"    [!] Skipping article due to critical error: {pub_error}")
                continue

            # Hardened Author Extraction
            raw_authors = bib.get("author", "")
            if isinstance(raw_authors, list):
                auteurs_list = [str(a).strip() for a in raw_authors]
            elif isinstance(raw_authors, str) and raw_authors:
                auteurs_list = [a.strip() for a in raw_authors.split(" and ") if a.strip()]
            else:
                auteurs_list = []

            # Build the dictionary using the variables we safely extracted above
            article_data = {
                "article_id": pub.get("author_pub_id", f"art_{uuid.uuid4().hex[:8]}"),
                "titre": bib.get("title", pub.get("bib", {}).get("title", "No Title")),
                "auteurs": auteurs_list,
                "date_publication": str(bib.get("pub_year", pub.get("bib", {}).get("pub_year", "Unknown"))),
                "journal": bib.get("journal",
                                   bib.get("citation", pub.get("bib", {}).get("citation", "Unknown Source"))),
                "citations": pub.get("num_citations", 0),
                "abstract": abstract_text,
                "abstract_clean": "",
                "embedding_zembed1": [],
                "eprint_url": eprint_url  # Added cleanly here
            }

            researcher_data["articles"].append(article_data)
            time.sleep(random.uniform(2.5, 5.5))

        return researcher_data

    except Exception as e:
        print(f"[!] An error occurred fetching profile {author_id}: {e}")
        return {}