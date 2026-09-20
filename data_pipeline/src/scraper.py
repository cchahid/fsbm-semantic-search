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

            bib = {}
            abstract_text = ""

            try:
                # Attempt 1: Standard extraction from the author's profile modal
                pub_filled = scholarly.fill(pub)
                bib = pub_filled.get("bib", {})
                abstract_text = bib.get("abstract", "")

            except AttributeError as pub_err:
                # This specifically catches the 'NoneType' object has no attribute 'text' error
                print(f"    [*] DOM Error on profile. Attempting fallback global search for abstract...")

                try:
                    # Attempt 2: Fallback to global search
                    title = pub.get("bib", {}).get("title", "")
                    if title:
                        search_iterator = scholarly.search_pubs(title)
                        fallback_pub = next(search_iterator)  # Get the first search result
                        bib = fallback_pub.get("bib", {})
                        abstract_text = bib.get("abstract", "")

                        # Apply a small delay since we made an extra request
                        time.sleep(random.uniform(1.5, 3.0))
                    else:
                        print("    [!] Fallback failed: No title available to search.")
                        bib = pub.get("bib", {})

                except StopIteration:
                    print("    [!] Fallback failed: Article not found in global search.")
                    bib = pub.get("bib", {})
                except Exception as fallback_err:
                    print(f"    [!] Fallback failed with error: {fallback_err}")
                    bib = pub.get("bib", {})

            except Exception as pub_error:
                print(f"    [!] Skipping article due to critical error: {pub_error}")
                continue  # Skip to the next article if it's a completely different error

            # Extract authors safely
            author_string = bib.get("author", "")
            auteurs_list = [a.strip() for a in author_string.split(" and ") if a.strip()] if author_string else []

            # Build the article dictionary safely using fallback data if necessary
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
                "embedding_zembed1": []
            }

            researcher_data["articles"].append(article_data)

            # CRITICAL: Rate Limiting (Polite scraping to avoid IP Ban)
            time.sleep(random.uniform(2.5, 5.5))

        return researcher_data

    except Exception as e:
        print(f"[!] An error occurred fetching profile {author_id}: {e}")
        return {}