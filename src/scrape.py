"""
scrape.py  ──────────────────────────────────────────────────────────────
fetches the release notes and converts the html table
into two assets:

  1. csv -> quick human inspection / spreadsheet use
  2. json -> downstream embedding + qa pipeline

all rows (≈1 271 as of 2025-08) are captured in one request; no js
execution is required because DataTables renders every <tr> server-side.
"""

# ── Imports ────────────────────────────────────────────────────────────
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
from typing import Dict, List

import bs4
import requests

# configs
ROOT_URL: str = (
    "https://help.relativity.com/RelativityOne/Content/What_s_New/Release_notes.htm"
)
USER_AGENT: str = "Mozilla/5.0 (X11; Linux) FAQ-Bot (+https://github.com/yourorg)"

DATA_DIR: pathlib.Path = pathlib.Path("../data")
HTML_PATH: pathlib.Path = DATA_DIR / "release_notes.html"
CSV_PATH: pathlib.Path = DATA_DIR / "release_notes.csv"
JSON_PATH: pathlib.Path = DATA_DIR / "chunks.json"

DATA_DIR.mkdir(exist_ok=True)

# helpers


def _slugify(text: str) -> str:
    """
    generates a url-safe slug from an arbitrary string.
    used only for human-readable IDs; collisions are fine.
    """
    return re.sub(r"\W+", "-", text.lower()).strip("-")[:80]


def _md5(text: str) -> str:
    """deterministic unique id for each chunk."""
    return hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest()


# core scraper logic


def fetch_html() -> None:
    """downloads the raw HTML page once and stores it on disk."""
    resp = requests.get(ROOT_URL, headers={"user agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    HTML_PATH.write_text(resp.text, encoding="utf-8")
    print(f"downloaded page -> {HTML_PATH}")


def parse_table() -> List[Dict]:
    """
    parses the first <table> element into a list of dicts.
    skips the header and filter rows (first two <tr>).
    """
    html: str = HTML_PATH.read_text(encoding="utf-8")
    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        sys.exit(" rrror: <table> not found – structure must have changed.")

    rows = table.find_all("tr")[2:]
    chunks: List[Dict] = []

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(
            ["relone_date", "gov_date", "type", "feature", "description"]
        )

        for tr in rows:
            cols = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
            # defensive check – malformed rows are simply skipped
            if len(cols) < 5:
                continue

            rel_date, gov_date, typ, feat, desc = cols[:5]
            writer.writerow([rel_date, gov_date, typ, feat, desc])

            content = (
                f"date: {rel_date} | type: {typ} | feature: {feat}\n"
                f"description: {desc}"
            )

            chunks.append(
                {
                    "id": _md5(content),
                    "title": f"{feat} ({rel_date})",
                    "url": ROOT_URL,
                    "content": content,
                    "relone_date": rel_date,
                    "gov_date": gov_date,
                    "type": typ,
                    "feature": feat,
                    "scraped_at": dt.date.today().isoformat(),
                }
            )

    JSON_PATH.write_text(json.dumps(chunks, indent=2), encoding="utf-8")
    print(f"parsed {len(chunks)} rows -> {CSV_PATH} & {JSON_PATH}")
    return chunks


# public entrypoint 
if __name__ == "__main__":
    """
    call sequence:
        $ python src/scrape.py        # downloads + parses everything
    """
    fetch_html()
    parse_table()
    print("scraping complete.")