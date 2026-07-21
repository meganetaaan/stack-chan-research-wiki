#!/usr/bin/env python3
"""Collect and rank recent literature candidates without editing wiki claims."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
QUERY_FILE = ROOT / "sources" / "queries.yaml"
INBOX = ROOT / "sources" / "inbox"
OPENALEX_API_URL = os.environ.get("OPENALEX_API_URL", "https://api.openalex.org/works")
SEMANTIC_SCHOLAR_API_URL = os.environ.get(
    "SEMANTIC_SCHOLAR_API_URL",
    "https://api.semanticscholar.org/graph/v1/paper/batch",
)
EVENT_DATA_API_URL = os.environ.get(
    "EVENT_DATA_API_URL", "https://api.eventdata.crossref.org/v1/events"
)
X_COUNTS_API_URL = os.environ.get(
    "X_COUNTS_API_URL", "https://api.x.com/2/tweets/counts/recent"
)
ENRICHMENT_TIMEOUT = float(os.environ.get("ENRICHMENT_TIMEOUT_SECONDS", "10"))
ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([^/?#]+)", re.IGNORECASE)


def date_window(today: dt.date, lookback_days: int) -> tuple[dt.date, dt.date]:
    if lookback_days < 1:
        raise ValueError("lookback_days must be at least 1")
    return today - dt.timedelta(days=lookback_days - 1), today


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    normalized = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value.strip(), flags=re.I)
    return normalized.lower() or None


def extract_arxiv_id(work: dict[str, Any]) -> str | None:
    arxiv_id = (work.get("ids") or {}).get("arxiv")
    if arxiv_id:
        return re.sub(r"^https?://arxiv\.org/abs/", "", arxiv_id, flags=re.I)
    for location in work.get("locations") or [work.get("primary_location") or {}]:
        for key in ("landing_page_url", "pdf_url"):
            match = ARXIV_RE.search(location.get(key) or "")
            if match:
                return match.group(1).removesuffix(".pdf")
    return None


def candidate_key(work: dict[str, Any]) -> str:
    doi = normalize_doi(work.get("doi"))
    if doi:
        return f"doi:{doi}"
    arxiv_id = extract_arxiv_id(work)
    if arxiv_id:
        return f"arxiv:{arxiv_id.lower()}"
    if work.get("id"):
        return str(work["id"])
    title = work.get("display_name") or work.get("title") or "untitled"
    return f"title:{title.casefold()}"


def openalex_filter(start: dt.date, end: dt.date, languages: list[str]) -> str:
    filters = [f"from_publication_date:{start}", f"to_publication_date:{end}"]
    if languages:
        filters.append(f"language:{'|'.join(languages)}")
    return ",".join(filters)


def fetch_openalex(
    query: str,
    start: dt.date,
    end: dt.date,
    languages: list[str],
    per_page: int,
) -> list[dict[str, Any]]:
    params = {
        "search": query,
        "filter": openalex_filter(start, end, languages),
        "per-page": per_page,
        "sort": "relevance_score:desc",
    }
    if api_key := os.environ.get("OPENALEX_API_KEY"):
        params["api_key"] = api_key
    if mailto := os.environ.get("OPENALEX_MAILTO"):
        params["mailto"] = mailto
    response = requests.get(OPENALEX_API_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("results", [])


def new_candidate(work: dict[str, Any], theme: str, query: str) -> dict[str, Any]:
    doi = normalize_doi(work.get("doi"))
    arxiv_id = extract_arxiv_id(work)
    return {
        "key": candidate_key(work),
        "themes": [theme],
        "queries": [query],
        "id": work.get("id"),
        "doi": doi,
        "arxiv_id": arxiv_id,
        "title": work.get("display_name") or work.get("title"),
        "publication_date": work.get("publication_date"),
        "type": work.get("type"),
        "primary_location": work.get("primary_location"),
        "open_access": work.get("open_access"),
        "metrics": {
            "query_match_count": 1,
            "openalex_cited_by_count": work.get("cited_by_count") or 0,
            "semantic_scholar_citation_count": None,
            "semantic_scholar_influential_citation_count": None,
            "reddit_mentions_30d": None,
            "x_original_posts_7d": None,
            "x_original_posts_rolling_30d": None,
        },
        "metric_status": {
            "semantic_scholar": "not_checked",
            "crossref_reddit": "not_checked",
            "x": "not_checked",
        },
        "attention_gate": {"passed": False, "reasons": []},
        "selected_for_review": False,
        "selection_reason": None,
        "status": "candidate",
    }


def merge_work(
    candidates: dict[str, dict[str, Any]],
    work: dict[str, Any],
    theme: str,
    query: str,
) -> None:
    key = candidate_key(work)
    if key not in candidates:
        candidates[key] = new_candidate(work, theme, query)
        return
    candidate = candidates[key]
    if theme not in candidate["themes"]:
        candidate["themes"].append(theme)
    if query not in candidate["queries"]:
        candidate["queries"].append(query)
    candidate["metrics"]["query_match_count"] = len(candidate["queries"])


def semantic_scholar_id(candidate: dict[str, Any]) -> str | None:
    if candidate.get("doi"):
        return f"DOI:{candidate['doi']}"
    if candidate.get("arxiv_id"):
        return f"ARXIV:{candidate['arxiv_id']}"
    return None


def enrich_semantic_scholar(
    candidates: list[dict[str, Any]], warnings: list[str], delay: float
) -> None:
    indexed = [(candidate, semantic_scholar_id(candidate)) for candidate in candidates]
    indexed = [(candidate, paper_id) for candidate, paper_id in indexed if paper_id]
    headers = {}
    if api_key := os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
        headers["x-api-key"] = api_key
    for offset in range(0, len(indexed), 500):
        batch = indexed[offset : offset + 500]
        try:
            response = requests.post(
                SEMANTIC_SCHOLAR_API_URL,
                params={
                    "fields": "paperId,citationCount,influentialCitationCount,externalIds"
                },
                json={"ids": [paper_id for _, paper_id in batch]},
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            results = response.json()
        except (requests.RequestException, ValueError) as error:
            warnings.append(f"Semantic Scholar enrichment failed: {error}")
            for candidate, _ in batch:
                candidate["metric_status"]["semantic_scholar"] = "error"
            continue
        for (candidate, _), result in zip(batch, results, strict=True):
            if result is None:
                candidate["metric_status"]["semantic_scholar"] = "not_found"
                continue
            candidate["metrics"]["semantic_scholar_citation_count"] = (
                result.get("citationCount") or 0
            )
            candidate["metrics"]["semantic_scholar_influential_citation_count"] = (
                result.get("influentialCitationCount") or 0
            )
            candidate["metric_status"]["semantic_scholar"] = "ok"
        if delay:
            time.sleep(delay)


def preliminary_priority(candidate: dict[str, Any]) -> tuple[int, int, str]:
    metrics = candidate["metrics"]
    return (
        citation_count(candidate),
        int(metrics["query_match_count"] or 0),
        candidate.get("publication_date") or "",
    )


def enrich_reddit(
    candidates: list[dict[str, Any]],
    start: dt.date,
    end: dt.date,
    warnings: list[str],
    delay: float,
) -> None:
    for index, candidate in enumerate(candidates):
        doi = candidate.get("doi")
        if not doi:
            candidate["metric_status"]["crossref_reddit"] = "unavailable_without_doi"
            continue
        params = {
            "obj-id": f"https://doi.org/{doi}",
            "source": "reddit",
            "from-occurred-date": start.isoformat(),
            "until-occurred-date": end.isoformat(),
            "rows": 0,
        }
        if mailto := os.environ.get("OPENALEX_MAILTO"):
            params["mailto"] = mailto
        try:
            response = requests.get(EVENT_DATA_API_URL, params=params, timeout=ENRICHMENT_TIMEOUT)
            response.raise_for_status()
            total = response.json().get("message", {}).get("total-results", 0)
        except (requests.RequestException, ValueError) as error:
            candidate["metric_status"]["crossref_reddit"] = "error"
            warnings.append(f"Reddit enrichment failed for {doi}: {error}")
            for remaining in candidates[index + 1 :]:
                if remaining["metric_status"]["crossref_reddit"] == "not_checked":
                    remaining["metric_status"]["crossref_reddit"] = (
                        "skipped_after_source_error"
                    )
            break
        candidate["metrics"]["reddit_mentions_30d"] = int(total or 0)
        candidate["metric_status"]["crossref_reddit"] = "ok"
        if delay:
            time.sleep(delay)


def x_query(candidate: dict[str, Any]) -> str | None:
    if candidate.get("doi"):
        return f'url:"https://doi.org/{candidate["doi"]}" -is:retweet'
    if candidate.get("arxiv_id"):
        return f'url:"https://arxiv.org/abs/{candidate["arxiv_id"]}" -is:retweet'
    return None


def enrich_x(candidates: list[dict[str, Any]], warnings: list[str], delay: float) -> bool:
    token = os.environ.get("X_BEARER_TOKEN")
    if not token:
        for candidate in candidates:
            candidate["metric_status"]["x"] = "disabled_missing_token"
        return False
    for index, candidate in enumerate(candidates):
        query = x_query(candidate)
        if not query:
            candidate["metric_status"]["x"] = "unavailable_without_identifier"
            continue
        try:
            response = requests.get(
                X_COUNTS_API_URL,
                params={"query": query, "granularity": "day"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=ENRICHMENT_TIMEOUT,
            )
            response.raise_for_status()
            count = sum(item.get("tweet_count", 0) for item in response.json().get("data", []))
        except (requests.RequestException, ValueError) as error:
            candidate["metric_status"]["x"] = "error"
            warnings.append(f"X enrichment failed for {candidate['key']}: {error}")
            for remaining in candidates[index + 1 :]:
                if remaining["metric_status"]["x"] == "not_checked":
                    remaining["metric_status"]["x"] = "skipped_after_source_error"
            break
        candidate["metrics"]["x_original_posts_7d"] = int(count)
        candidate["metric_status"]["x"] = "ok"
        if delay:
            time.sleep(delay)
    return True


def load_x_history(inbox: Path, today: dt.date, lookback_days: int) -> dict[str, int]:
    start, _ = date_window(today, lookback_days)
    totals: dict[str, int] = {}
    for path in sorted(inbox.glob("literature-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            collected_at = dt.date.fromisoformat(payload["collected_at"])
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            continue
        if not start <= collected_at < today:
            continue
        for candidate in payload.get("candidates", []):
            count = candidate.get("metrics", {}).get("x_original_posts_7d")
            if count is not None:
                totals[candidate["key"]] = totals.get(candidate["key"], 0) + int(count)
    return totals


def apply_x_history(candidates: list[dict[str, Any]], history: dict[str, int]) -> None:
    for candidate in candidates:
        current = candidate["metrics"]["x_original_posts_7d"]
        previous = history.get(candidate["key"])
        if current is None and previous is None:
            continue
        candidate["metrics"]["x_original_posts_rolling_30d"] = int(current or 0) + int(
            previous or 0
        )


def citation_count(candidate: dict[str, Any]) -> int:
    metrics = candidate["metrics"]
    return max(
        int(metrics["openalex_cited_by_count"] or 0),
        int(metrics["semantic_scholar_citation_count"] or 0),
    )


def evaluate_attention(candidate: dict[str, Any], thresholds: dict[str, int]) -> None:
    metrics = candidate["metrics"]
    reasons = []
    citations = citation_count(candidate)
    reddit = int(metrics["reddit_mentions_30d"] or 0)
    x_posts = int(metrics["x_original_posts_rolling_30d"] or 0)
    if citations >= thresholds["min_citations"]:
        reasons.append(f"citations>={thresholds['min_citations']}")
    if reddit >= thresholds["min_reddit_mentions"]:
        reasons.append(f"reddit_mentions>={thresholds['min_reddit_mentions']}")
    if x_posts >= thresholds["min_x_original_posts"]:
        reasons.append(f"x_original_posts>={thresholds['min_x_original_posts']}")
    candidate["attention_gate"] = {"passed": bool(reasons), "reasons": reasons}


def ranking_key(candidate: dict[str, Any]) -> tuple[int, int, int, int, int, str]:
    metrics = candidate["metrics"]
    return (
        int(candidate["attention_gate"]["passed"]),
        citation_count(candidate),
        int(metrics["reddit_mentions_30d"] or 0),
        int(metrics["x_original_posts_rolling_30d"] or 0),
        int(metrics["query_match_count"] or 0),
        candidate.get("publication_date") or "",
    )


def select_review_queue(
    candidates: list[dict[str, Any]], max_candidates: int, relevance_reserve: int
) -> list[dict[str, Any]]:
    ranked = sorted(candidates, key=ranking_key, reverse=True)
    selected = [candidate for candidate in ranked if candidate["attention_gate"]["passed"]][
        :max_candidates
    ]
    remaining_slots = max_candidates - len(selected)
    reserve_count = min(remaining_slots, relevance_reserve)
    reserve = [candidate for candidate in ranked if not candidate["attention_gate"]["passed"]][
        :reserve_count
    ]
    for candidate in selected:
        candidate["selected_for_review"] = True
        candidate["selection_reason"] = "attention_gate"
    for candidate in reserve:
        candidate["selected_for_review"] = True
        candidate["selection_reason"] = "relevance_reserve"
    return selected + reserve


def review_summary(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": candidate["key"],
        "title": candidate["title"],
        "publication_date": candidate["publication_date"],
        "selection_reason": candidate["selection_reason"],
        "attention_gate": candidate["attention_gate"],
        "metrics": candidate["metrics"],
    }


def main() -> None:
    config = yaml.safe_load(QUERY_FILE.read_text(encoding="utf-8"))
    filters = config["filters"]
    enrichment = config["enrichment"]
    thresholds = config["attention_thresholds"]
    today = dt.date.today()
    start, end = date_window(today, filters["lookback_days"])
    warnings: list[str] = []
    candidates_by_key: dict[str, dict[str, Any]] = {}

    for theme, queries in config["themes"].items():
        for query in queries:
            works = fetch_openalex(
                query,
                start,
                end,
                filters.get("languages", []),
                filters["max_candidates_per_query"],
            )
            for work in works:
                merge_work(candidates_by_key, work, theme, query)
            if enrichment["request_delay_seconds"]:
                time.sleep(enrichment["request_delay_seconds"])

    candidates = list(candidates_by_key.values())
    if enrichment["semantic_scholar"]:
        enrich_semantic_scholar(candidates, warnings, enrichment["request_delay_seconds"])

    enrichment_candidates = sorted(candidates, key=preliminary_priority, reverse=True)[
        : enrichment["max_candidates"]
    ]
    if enrichment["crossref_reddit"]:
        enrich_reddit(
            enrichment_candidates,
            start,
            end,
            warnings,
            enrichment["request_delay_seconds"],
        )
    x_enabled = enrichment["x"]
    x_queried = False
    if x_enabled:
        x_queried = enrich_x(
            enrichment_candidates, warnings, enrichment["request_delay_seconds"]
        )
    else:
        for candidate in candidates:
            candidate["metric_status"]["x"] = "disabled_by_config"

    history = load_x_history(INBOX, today, filters["lookback_days"])
    apply_x_history(candidates, history)
    for candidate in candidates:
        evaluate_attention(candidate, thresholds)
    review_queue = select_review_queue(
        candidates,
        filters["max_review_candidates"],
        filters["relevance_reserve"],
    )
    candidates.sort(key=ranking_key, reverse=True)

    payload = {
        "collected_at": today.isoformat(),
        "window": {"days": filters["lookback_days"], "start": str(start), "end": str(end)},
        "sources": {
            "openalex": "required",
            "semantic_scholar": "enabled" if enrichment["semantic_scholar"] else "disabled",
            "crossref_reddit": "enabled" if enrichment["crossref_reddit"] else "disabled",
            "x": "queried" if x_queried else "disabled_or_unavailable",
        },
        "attention_thresholds": thresholds,
        "warnings": warnings,
        "candidate_count": len(candidates),
        "review_queue": [review_summary(candidate) for candidate in review_queue],
        "candidates": candidates,
    }
    INBOX.mkdir(parents=True, exist_ok=True)
    output = INBOX / f"literature-{today.isoformat()}.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        display_path = output.relative_to(ROOT)
    except ValueError:
        display_path = output
    print(
        f"Wrote {len(candidates)} candidates and {len(review_queue)} review items "
        f"to {display_path}"
    )
    if warnings:
        print(f"Completed with {len(warnings)} enrichment warning(s)")


if __name__ == "__main__":
    main()
