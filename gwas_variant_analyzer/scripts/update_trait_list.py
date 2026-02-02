#!/usr/bin/env python3
"""
update_trait_list.py — Fetch all EFO traits from GWAS Catalog and save locally.

B_spec Block 1: Trait List Management
- Fetches all traits via GET /efoTraits?size=500 with pagination
- Saves to data/trait_list.json
- Saves metadata to data/trait_list.meta.json
"""

import json
import os
import sys
import time
import logging
import requests
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Config from B_spec
API_BASE_URL = "https://www.ebi.ac.uk/gwas/rest/api"
ENDPOINT = "/efoTraits"
PAGE_SIZE = 500
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2
REQUEST_TIMEOUT_SECONDS = 30

# Output paths relative to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # up two levels from scripts/
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "trait_list.json")
META_FILE = os.path.join(OUTPUT_DIR, "trait_list.meta.json")


def fetch_all_traits() -> list:
    """Fetch all EFO traits from GWAS Catalog API with pagination."""
    all_traits = []
    page = 0
    has_next = True
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})

    while has_next:
        url = f"{API_BASE_URL}{ENDPOINT}"
        params = {"size": PAGE_SIZE, "page": page}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Fetching page {page} (attempt {attempt})...")
                resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
                resp.raise_for_status()
                data = resp.json()

                traits_page = data.get("_embedded", {}).get("efoTraits", [])
                for t in traits_page:
                    all_traits.append({
                        "trait": t.get("trait", ""),
                        "shortForm": t.get("shortForm", ""),
                        "uri": t.get("uri", ""),
                    })

                logger.info(f"  Page {page}: {len(traits_page)} traits (total so far: {len(all_traits)})")

                # Check for next page
                links = data.get("_links", {})
                page_info = data.get("page", {})
                total_pages = page_info.get("totalPages", 0)

                if page + 1 < total_pages:
                    page += 1
                else:
                    has_next = False
                break  # success, exit retry loop

            except requests.exceptions.RequestException as e:
                logger.warning(f"  Request failed (attempt {attempt}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    logger.error(f"Failed to fetch page {page} after {MAX_RETRIES} attempts.")
                    raise

        # Be polite between pages
        if has_next:
            time.sleep(0.5)

    return all_traits


def save_trait_list(traits: list):
    """Save trait list and metadata to disk."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save trait list
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(traits, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(traits)} traits to {OUTPUT_FILE}")

    # Save metadata
    meta = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_traits": len(traits),
    }
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved metadata to {META_FILE}")


def main():
    logger.info("=== GWAS Catalog Trait List Updater ===")
    logger.info(f"API: {API_BASE_URL}{ENDPOINT}")
    logger.info(f"Output: {OUTPUT_FILE}")

    try:
        traits = fetch_all_traits()
    except Exception as e:
        logger.error(f"Fatal: could not fetch traits: {e}")
        sys.exit(1)

    if not traits:
        logger.error("Fatal: fetched 0 traits. Aborting save to prevent empty file.")
        sys.exit(1)

    save_trait_list(traits)
    logger.info(f"Done. {len(traits)} traits saved.")


if __name__ == "__main__":
    main()
