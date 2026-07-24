#!/usr/bin/env python3
"""Collect and rank recent literature candidates without editing wiki claims."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
import xml.etree.ElementTree as ET
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
CROSSREF_WORKS_API_URL = os.environ.get(
    "CROSSREF_WORKS_API_URL", "https://api.crossref.org/works"
)
X_COUNTS_API_URL = os.environ.get(
    "X_COUNTS_API_URL", "https://api.x.com/2/tweets/counts/recent"
)
ARXIV_API_URL = os.environ.get("ARXIV_API_URL", "https://export.arxiv.org/api/query")
ACL_ANTHOLOGY_DATA_URL = os.environ.get(
    "ACL_ANTHOLOGY_DATA_URL",
    "https://raw.githubusercontent.com/acl-org/acl-anthology/master/data/xml",
)
ENRICHMENT_TIMEOUT = float(os.environ.get("ENRICHMENT_TIMEOUT_SECONDS", "10"))
ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([^/?#]+)", re.IGNORECASE)
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


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
    response = requests.get(OPENALEX_API_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("results", [])


def compact_text(value: str | None) -> str:
    return " ".join((value or "").split())


def parse_arxiv_feed(content: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(content)
    works = []
    for entry in root.findall("atom:entry", ATOM_NS):
        identifier = compact_text(entry.findtext("atom:id", namespaces=ATOM_NS))
        arxiv_id = re.sub(r"^https?://arxiv\.org/abs/", "", identifier, flags=re.I)
        arxiv_id = re.sub(r"v\d+$", "", arxiv_id)
        doi = entry.findtext("arxiv:doi", namespaces=ATOM_NS)
        authors = [
            compact_text(author.findtext("atom:name", namespaces=ATOM_NS))
            for author in entry.findall("atom:author", ATOM_NS)
        ]
        published = compact_text(entry.findtext("atom:published", namespaces=ATOM_NS))
        updated = compact_text(entry.findtext("atom:updated", namespaces=ATOM_NS))
        categories = [item.get("term") for item in entry.findall("atom:category", ATOM_NS)]
        works.append(
            {
                "id": f"https://arxiv.org/abs/{arxiv_id}",
                "ids": {"arxiv": f"https://arxiv.org/abs/{arxiv_id}"},
                "doi": doi,
                "display_name": compact_text(
                    entry.findtext("atom:title", namespaces=ATOM_NS)
                ),
                "abstract": compact_text(
                    entry.findtext("atom:summary", namespaces=ATOM_NS)
                ),
                "publication_date": published[:10],
                "updated_date": updated[:10],
                "type": "preprint",
                "cited_by_count": 0,
                "primary_location": {
                    "landing_page_url": f"https://arxiv.org/abs/{arxiv_id}",
                    "source": {"display_name": "arXiv"},
                },
                "locations": [
                    {"landing_page_url": f"https://arxiv.org/abs/{arxiv_id}"}
                ],
                "authorships": [
                    {"author": {"display_name": author}} for author in authors if author
                ],
                "categories": [category for category in categories if category],
                "_discovery_source": "arxiv",
            }
        )
    return works


def fetch_arxiv(
    query: str,
    categories: list[str],
    start: dt.date,
    end: dt.date,
    max_results: int,
) -> list[dict[str, Any]]:
    category_query = " OR ".join(f"cat:{category}" for category in categories)
    date_query = (
        f"submittedDate:[{start.strftime('%Y%m%d')}0000 TO "
        f"{end.strftime('%Y%m%d')}2359]"
    )
    response = requests.get(
        ARXIV_API_URL,
        params={
            "search_query": f"({category_query}) AND ({query}) AND {date_query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        },
        timeout=30,
    )
    response.raise_for_status()
    return parse_arxiv_feed(response.content)


def xml_text(element: ET.Element | None) -> str:
    return compact_text("".join(element.itertext()) if element is not None else "")


def parse_acl_anthology(
    content: bytes,
    venue: dict[str, str],
    start: dt.date,
    end: dt.date,
    focus_terms: list[str],
) -> list[tuple[dict[str, Any], list[str]]]:
    root = ET.fromstring(content)
    results = []
    for volume in root.findall("volume"):
        ingest_value = volume.get("ingest-date")
        if not ingest_value:
            continue
        ingest_date = dt.date.fromisoformat(ingest_value)
        if not start <= ingest_date <= end:
            continue
        meta = volume.find("meta")
        month = xml_text(meta.find("month") if meta is not None else None)
        year = xml_text(meta.find("year") if meta is not None else None)
        publication_date = f"{year}-{month_to_number(month):02d}-01" if year else ingest_value
        booktitle = xml_text(meta.find("booktitle") if meta is not None else None)
        for paper in volume.findall("paper"):
            title = xml_text(paper.find("title"))
            abstract = xml_text(paper.find("abstract"))
            haystack = f"{title} {abstract}".casefold()
            matches = [term for term in focus_terms if term.casefold() in haystack]
            if not matches:
                continue
            anthology_id = xml_text(paper.find("url"))
            doi = xml_text(paper.find("doi")) or None
            authors = []
            for author in paper.findall("author"):
                name = " ".join(
                    value
                    for value in (
                        xml_text(author.find("first")),
                        xml_text(author.find("last")),
                    )
                    if value
                )
                if name:
                    authors.append(name)
            work = {
                "id": f"https://aclanthology.org/{anthology_id}/",
                "doi": doi,
                "display_name": title,
                "abstract": abstract,
                "publication_date": publication_date,
                "ingested_at": ingest_value,
                "type": "proceedings-article",
                "cited_by_count": 0,
                "primary_location": {
                    "landing_page_url": f"https://aclanthology.org/{anthology_id}/",
                    "source": {"display_name": f"{venue['name']} / ACL Anthology"},
                },
                "locations": [
                    {"landing_page_url": f"https://aclanthology.org/{anthology_id}/"}
                ],
                "authorships": [
                    {"author": {"display_name": author}} for author in authors
                ],
                "booktitle": booktitle,
                "_discovery_source": "acl_anthology",
            }
            results.append((work, matches))
    return results


def month_to_number(value: str) -> int:
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    return months.get(value.casefold(), 1)


def fetch_acl_anthology(
    venue: dict[str, str],
    year: int,
    start: dt.date,
    end: dt.date,
    focus_terms: list[str],
) -> list[tuple[dict[str, Any], list[str]]]:
    response = requests.get(
        f"{ACL_ANTHOLOGY_DATA_URL}/{year}.{venue['id']}.xml", timeout=30
    )
    if response.status_code == 404:
        return []
    response.raise_for_status()
    return parse_acl_anthology(response.content, venue, start, end, focus_terms)


def crossref_date(item: dict[str, Any]) -> str | None:
    for field in ("published-online", "published-print", "published", "created"):
        parts = (item.get(field) or {}).get("date-parts") or []
        if not parts or not parts[0]:
            continue
        values = list(parts[0]) + [1, 1]
        try:
            return dt.date(int(values[0]), int(values[1]), int(values[2])).isoformat()
        except (TypeError, ValueError):
            continue
    return None


def crossref_item_to_work(
    item: dict[str, Any], venue: dict[str, Any]
) -> dict[str, Any]:
    doi = normalize_doi(item.get("DOI"))
    title = compact_text((item.get("title") or [""])[0])
    authors = []
    for author in item.get("author") or []:
        name = " ".join(
            value
            for value in (author.get("given"), author.get("family"))
            if value
        )
        if name:
            authors.append(name)
    container = compact_text((item.get("container-title") or [venue["name"]])[0])
    url = f"https://doi.org/{doi}" if doi else item.get("URL")
    return {
        "id": url,
        "doi": doi,
        "display_name": title,
        "abstract": compact_text(re.sub(r"<[^>]+>", " ", item.get("abstract") or "")),
        "publication_date": crossref_date(item),
        "type": item.get("type") or "proceedings-article",
        "cited_by_count": item.get("is-referenced-by-count") or 0,
        "primary_location": {
            "landing_page_url": url,
            "source": {"display_name": container},
        },
        "locations": [{"landing_page_url": url}] if url else [],
        "authorships": [
            {"author": {"display_name": author}} for author in authors
        ],
        "_discovery_source": "crossref_conference",
    }


def crossref_venue_matches(item: dict[str, Any], venue: dict[str, Any]) -> bool:
    containers = " ".join(item.get("container-title") or []).casefold()
    return any(
        pattern.casefold() in containers
        for pattern in venue.get("container_patterns", [])
    )


def fetch_crossref_conference(
    venue: dict[str, Any],
    start: dt.date,
    end: dt.date,
    focus_terms: list[str],
    max_results: int,
) -> list[tuple[dict[str, Any], list[str]]]:
    params = {
        "query.container-title": venue["query"],
        "filter": (
            f"from-update-date:{start.isoformat()},"
            f"until-update-date:{end.isoformat()},type:proceedings-article"
        ),
        "rows": max_results,
    }
    if mailto := os.environ.get("API_CONTACT_EMAIL"):
        params["mailto"] = mailto
    response = requests.get(CROSSREF_WORKS_API_URL, params=params, timeout=30)
    response.raise_for_status()
    results = []
    for item in response.json().get("message", {}).get("items", []):
        if not crossref_venue_matches(item, venue):
            continue
        work = crossref_item_to_work(item, venue)
        haystack = f"{work['display_name']} {work['abstract']}".casefold()
        matches = [term for term in focus_terms if term.casefold() in haystack]
        if venue.get("accept_all"):
            matches = matches or ["venue_scope"]
        if matches:
            results.append((work, matches))
    return results


def new_candidate(work: dict[str, Any], theme: str, query: str) -> dict[str, Any]:
    doi = normalize_doi(work.get("doi"))
    arxiv_id = extract_arxiv_id(work)
    authors = [
        authorship.get("author", {}).get("display_name")
        for authorship in work.get("authorships") or []
        if authorship.get("author", {}).get("display_name")
    ]
    return {
        "key": candidate_key(work),
        "themes": [theme],
        "queries": [query],
        "discovery_sources": [work.get("_discovery_source", "openalex")],
        "id": work.get("id"),
        "doi": doi,
        "arxiv_id": arxiv_id,
        "title": work.get("display_name") or work.get("title"),
        "authors": authors,
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
    source = work.get("_discovery_source", "openalex")
    if source not in candidate["discovery_sources"]:
        candidate["discovery_sources"].append(source)
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
        int(metrics["query_match_count"] or 0),
        citation_count(candidate),
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
        if mailto := os.environ.get("API_CONTACT_EMAIL"):
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
        int(metrics["query_match_count"] or 0),
        citation_count(candidate),
        int(metrics["reddit_mentions_30d"] or 0),
        int(metrics["x_original_posts_rolling_30d"] or 0),
        candidate.get("publication_date") or "",
    )


def select_review_queue(
    candidates: list[dict[str, Any]], max_candidates: int, relevance_reserve: int
) -> list[dict[str, Any]]:
    ranked = sorted(candidates, key=ranking_key, reverse=True)
    reserve_count = min(max_candidates, relevance_reserve)
    attention_slots = max_candidates - reserve_count
    attention_candidates = [
        candidate for candidate in ranked if candidate["attention_gate"]["passed"]
    ]
    selected = attention_candidates[:attention_slots]
    reserve = [candidate for candidate in ranked if not candidate["attention_gate"]["passed"]][
        :reserve_count
    ]
    remaining_slots = max_candidates - len(selected) - len(reserve)
    if remaining_slots:
        selected.extend(attention_candidates[attention_slots : attention_slots + remaining_slots])
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


def candidate_url(candidate: dict[str, Any]) -> str | None:
    if candidate.get("doi"):
        return f"https://doi.org/{candidate['doi']}"
    if candidate.get("arxiv_id"):
        return f"https://arxiv.org/abs/{candidate['arxiv_id']}"
    primary_location = candidate.get("primary_location") or {}
    return primary_location.get("landing_page_url") or candidate.get("id")


def metric_value(value: int | None, status: str) -> str:
    if value is not None:
        return str(value)
    status_labels = {
        "disabled_by_config": "未使用",
        "disabled_missing_token": "未設定",
        "unavailable_without_doi": "DOIなし",
        "unavailable_without_identifier": "識別子なし",
        "skipped_after_source_error": "取得障害により省略",
        "error": "取得失敗",
        "not_checked": "未確認",
    }
    return status_labels.get(status, "データなし")


def render_review_report(
    *,
    collected_at: dt.date,
    start: dt.date,
    end: dt.date,
    candidate_count: int,
    review_queue: list[dict[str, Any]],
    warnings: list[str],
) -> str:
    lines = [
        f"# 文献候補レビュー {collected_at.isoformat()}",
        "",
        "> 自動収集した候補です。Wiki本文と検証状態は変更していません。",
        "",
        "## 収集概要",
        "",
        f"- 対象期間：{start.isoformat()}から{end.isoformat()}",
        f"- 全候補：{candidate_count}件",
        f"- 優先レビュー候補：{len(review_queue)}件",
        f"- 外部指標の取得警告：{len(warnings)}件",
        "",
        "## レビュー手順",
        "",
        "1. タイトルのリンクから一次情報を開く",
        "2. ｽﾀｯｸﾁｬﾝとの関連性を高、中、低で判断する",
        "3. 採用する候補だけ書誌情報と内容を確認し、Wikiページを作成する",
        "",
        "定量指標は注目度の補助情報であり、研究の妥当性を示すものではありません。",
    ]
    selection_labels = {
        "attention_gate": "定量指標を通過",
        "relevance_reserve": "関連性確認枠",
    }
    for index, candidate in enumerate(review_queue, start=1):
        metrics = candidate["metrics"]
        metric_status = candidate["metric_status"]
        url = candidate_url(candidate)
        title = candidate.get("title") or "無題"
        heading = f"## {index}. [{title}]({url})" if url else f"## {index}. {title}"
        authors = ", ".join(candidate.get("authors") or []) or "取得できず"
        location = candidate.get("primary_location") or {}
        venue = (location.get("source") or {}).get("display_name") or "取得できず"
        identifier = candidate.get("doi") or candidate.get("arxiv_id") or candidate["key"]
        reasons = ", ".join(candidate["attention_gate"]["reasons"]) or "なし"
        themes = ", ".join(candidate.get("themes") or [])
        queries = ", ".join(candidate.get("queries") or [])
        discovery_sources = ", ".join(candidate.get("discovery_sources") or [])
        selection = selection_labels.get(
            candidate.get("selection_reason"),
            candidate.get("selection_reason") or "不明",
        )
        influential = metric_value(
            metrics["semantic_scholar_influential_citation_count"],
            metric_status["semantic_scholar"],
        )
        reddit = metric_value(
            metrics["reddit_mentions_30d"], metric_status["crossref_reddit"]
        )
        x_posts = metric_value(
            metrics["x_original_posts_rolling_30d"], metric_status["x"]
        )
        lines.extend(
            [
                "",
                heading,
                "",
                f"- 著者：{authors}",
                f"- 公開日：{candidate.get('publication_date') or '取得できず'}",
                f"- 種別：{candidate.get('type') or '取得できず'}",
                f"- 掲載先：{venue}",
                f"- 識別子：`{identifier}`",
                f"- 収集元：{discovery_sources}",
                f"- 選定理由：{selection}（{reasons}）",
                "- 指標："
                f"被引用 {citation_count(candidate)}、"
                f"影響力の高い引用 {influential}、"
                f"Reddit {reddit}、"
                f"X 30日近似 {x_posts}",
                f"- 検索テーマ：{themes}",
                f"- 一致した検索語：{queries}",
            ]
        )
    lines.extend(
        [
            "",
            "## 機械可読データ",
            "",
            "全候補と取得状態は "
            f"`sources/inbox/literature-{collected_at.isoformat()}.json` "
            "に保存しています。",
            "",
        ]
    )
    return "\n".join(lines)


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

    arxiv_config = config.get("arxiv", {})
    if arxiv_config.get("enabled"):
        for query_config in arxiv_config.get("queries", []):
            query = query_config["query"]
            try:
                works = fetch_arxiv(
                    query,
                    arxiv_config.get("categories", []),
                    start,
                    end,
                    arxiv_config["max_results_per_query"],
                )
            except (requests.RequestException, ValueError, ET.ParseError) as error:
                warnings.append(f"arXiv collection failed for {query}: {error}")
                continue
            for work in works:
                merge_work(candidates_by_key, work, query_config["theme"], f"arXiv:{query}")
            if arxiv_config.get("request_delay_seconds"):
                time.sleep(arxiv_config["request_delay_seconds"])

    acl_config = config.get("acl_anthology", {})
    if acl_config.get("enabled"):
        for venue in acl_config.get("venues", []):
            for year in range(start.year, end.year + 1):
                try:
                    works_with_matches = fetch_acl_anthology(
                        venue,
                        year,
                        start,
                        end,
                        acl_config.get("focus_terms", []),
                    )
                except (requests.RequestException, ValueError, ET.ParseError) as error:
                    warnings.append(
                        f"ACL Anthology collection failed for {venue['name']} {year}: {error}"
                    )
                    continue
                for work, matches in works_with_matches:
                    for match in matches:
                        merge_work(
                            candidates_by_key,
                            work,
                            venue["theme"],
                            f"{venue['name']}:{match}",
                        )

    conference_config = config.get("crossref_conferences", {})
    if conference_config.get("enabled"):
        for venue in conference_config.get("venues", []):
            try:
                works_with_matches = fetch_crossref_conference(
                    venue,
                    start,
                    end,
                    conference_config.get("focus_terms", []),
                    conference_config["max_results_per_venue"],
                )
            except (requests.RequestException, ValueError) as error:
                warnings.append(
                    f"Crossref conference collection failed for {venue['name']}: {error}"
                )
                continue
            for work, matches in works_with_matches:
                for match in matches:
                    merge_work(
                        candidates_by_key,
                        work,
                        venue["theme"],
                        f"{venue['name']}:{match}",
                    )

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
            "arxiv": "enabled" if arxiv_config.get("enabled") else "disabled",
            "acl_anthology": "enabled" if acl_config.get("enabled") else "disabled",
            "crossref_conferences": (
                "enabled" if conference_config.get("enabled") else "disabled"
            ),
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
    report = INBOX / f"literature-{today.isoformat()}.md"
    report.write_text(
        render_review_report(
            collected_at=today,
            start=start,
            end=end,
            candidate_count=len(candidates),
            review_queue=review_queue,
            warnings=warnings,
        ),
        encoding="utf-8",
    )
    try:
        display_path = output.relative_to(ROOT)
    except ValueError:
        display_path = output
    print(
        f"Wrote {len(candidates)} candidates and {len(review_queue)} review items "
        f"to {display_path} and {report.relative_to(ROOT)}"
    )
    if warnings:
        print(f"Completed with {len(warnings)} enrichment warning(s)")
        for warning in warnings:
            print(f"WARNING: {warning}")


if __name__ == "__main__":
    main()
