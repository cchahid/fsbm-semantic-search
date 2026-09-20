import os
import json
import time
import random
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENRICHMENT_FILE = os.path.join(BASE_DIR, "data", "raw", "openalex_enrichment.json")
PDF_DIR = os.path.join(BASE_DIR, "data", "raw", "pdf's")
MANIFEST_FILE = os.path.join(BASE_DIR, "data", "raw", "download_status.json")

os.makedirs(PDF_DIR, exist_ok=True)

# Polite user-agent specifying an academic / text-mining intent (as encouraged in open science guidelines)
HEADERS = {
    "User-Agent": "FSBM-Academic-Research-Bot/1.0 (Text and Data Mining project; contact: student@univ.ma)",
    "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters for Windows/Linux file systems."""
    return "".join(c for c in filename if c.isalnum() or c in (" ", "_", "-")).rstrip()


def load_manifest() -> dict:
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return {}


def save_manifest(manifest: dict):
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)


def download_pdfs():
    if not os.path.exists(ENRICHMENT_FILE):
        print(f"[!] Enrichment file not found at {ENRICHMENT_FILE}")
        return

    with open(ENRICHMENT_FILE, "r", encoding="utf-8") as f:
        enrichment_data = json.load(f)

    # Filter records containing open-access PDF links
    targets = [
        item for item in enrichment_data.values()
        if item.get("pdf_url") and str(item["pdf_url"]).strip()
    ]

    manifest = load_manifest()
    print(f"[*] Found {len(targets)} articles with available Open Access URLs.")

    downloaded_count = 0
    skipped_count = 0
    restricted_count = 0

    for idx, item in enumerate(targets, start=1):
        article_id = item.get("article_id", f"article_{idx}")
        safe_id = sanitize_filename(article_id.replace(":", "_"))
        pdf_path = os.path.join(PDF_DIR, f"{safe_id}.pdf")
        pdf_url = item["pdf_url"]

        # IDEMPOTENCY CHECK: Skip if already marked success or file exists on disk
        if manifest.get(article_id) == "success" or (os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1024):
            if manifest.get(article_id) != "success":
                manifest[article_id] = "success"
                save_manifest(manifest)
            skipped_count += 1
            continue

        print(f"[{idx}/{len(targets)}] Processing Open Access URL: {item.get('titre', '')[:60]}...")

        try:
            # Using stream=True to efficiently evaluate headers before loading full data chunks
            response = requests.get(pdf_url, headers=HEADERS, timeout=20, stream=True, allow_redirects=True)

            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "").lower()

                # Verify it is genuinely a PDF stream and not a HTML paywall landing page
                if "application/pdf" in content_type or response.raw.read(4) == b"%PDF":
                    # Reset pointer if raw.read(4) was evaluated
                    response.raw.seek(0)

                    with open(pdf_path, "wb") as pdf_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                pdf_file.write(chunk)

                    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1024:
                        print(f"    [+] Successfully downloaded Open Access PDF: {safe_id}.pdf")
                        manifest[article_id] = "success"
                        downloaded_count += 1
                    else:
                        print("    [-] File saved but appears corrupted or empty.")
                        manifest[article_id] = "failed_corrupted"
                else:
                    print("    [-] Skipped: Target link returned an HTML landing page / paywall wrapper.")
                    manifest[article_id] = "skipped_paywall_html"
                    restricted_count += 1
            elif response.status_code == 403:
                print(f"    [!] HTTP 403 Forbidden (Publisher restriction/CDN block)")
                manifest[article_id] = "failed_403_forbidden"
                restricted_count += 1
            else:
                print(f"    [!] HTTP {response.status_code}")
                manifest[article_id] = f"failed_http_{response.status_code}"

        except requests.exceptions.RequestException as e:
            print(f"    [!] Download network error: {e}")
            manifest[article_id] = "failed_network_exception"

        # Save progress dynamically to the state manifest after each item
        save_manifest(manifest)

        # Polite throttling interval to comply with open repository guidelines
        time.sleep(random.uniform(1.0, 2.0))

    print(f"\n[+] Open Access PDF download process finished.")
    print(f"    - Newly downloaded: {downloaded_count}")
    print(f"    - Skipped (cached/already present): {skipped_count}")
    print(f"    - Restricted / Paywalled (handled gracefully): {restricted_count}")


if __name__ == "__main__":
    download_pdfs()