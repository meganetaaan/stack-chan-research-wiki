#!/usr/bin/env python3
"""Collect literature candidates into sources/inbox.

This is intentionally conservative: it only stores metadata candidates and never edits wiki claims.
Review the current API terms and authentication requirements before production use.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
QUERY_FILE = ROOT / "sources" / "queries.yaml"
INBOX = ROOT / "sources" / "inbox"
API_URL = os.environ.get("OPENALEX_API_URL", "https://api.openalex.org/works")
API_KEY = os.environ.get("OPENALEX_API_KEY")
MAILTO = os.environ.get("OPENALEX_MAILTO")


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value[:80] or "untitled"


def fetch(query: str, per_page: int) -> list[dict]:
    params = {"search": query, "per-page": per_page, "sort": "publication_date:desc"}
    if API_KEY:
        params["api_key"] = API_KEY
    if MAILTO:
        params["mailto"] = MAILTO
    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("results", [])


def main() -> None:
    config = yaml.safe_load(QUERY_FILE.read_text(encoding="utf-8"))
    max_candidates = config["filters"].get("max_candidates_per_query", 20)
    today = dt.date.today().isoformat()
    INBOX.mkdir(parents=True, exist_ok=True)

    seen_ids: set[str] = set()
    candidates: list[dict] = []
    for theme, queries in config["themes"].items():
        for query in queries:
            for work in fetch(query, max_candidates):
                work_id = work.get("id") or work.get("doi") or work.get("title")
                if not work_id or work_id in seen_ids:
                    continue
                seen_ids.add(work_id)
                candidates.append({
                    "theme": theme,
                    "query": query,
                    "id": work.get("id"),
                    "doi": work.get("doi"),
                    "title": work.get("display_name") or work.get("title"),
                    "publication_date": work.get("publication_date"),
                    "type": work.get("type"),
                    "cited_by_count": work.get("cited_by_count"),
                    "primary_location": work.get("primary_location"),
                    "open_access": work.get("open_access"),
                    "collected_at": today,
                    "status": "candidate",
                })
            time.sleep(0.2)

    output = INBOX / f"openalex-{today}.json"
    output.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(candidates)} candidates to {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
