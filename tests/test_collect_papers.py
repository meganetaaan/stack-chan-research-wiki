import datetime as dt
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import requests

from scripts import collect_papers


def work(
    identifier: str,
    title: str = "Example",
    doi: str | None = "https://doi.org/10.0000/example",
    citations: int = 0,
) -> dict:
    return {
        "id": identifier,
        "doi": doi,
        "display_name": title,
        "publication_date": "2026-07-20",
        "type": "article",
        "cited_by_count": citations,
        "primary_location": {},
        "locations": [],
        "authorships": [{"author": {"display_name": "Sample Author"}}],
    }


class DateWindowTests(TestCase):
    def test_uses_inclusive_thirty_day_window(self) -> None:
        start, end = collect_papers.date_window(dt.date(2026, 7, 22), 30)

        self.assertEqual(start, dt.date(2026, 6, 23))
        self.assertEqual(end, dt.date(2026, 7, 22))

    def test_rejects_non_positive_window(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 1"):
            collect_papers.date_window(dt.date(2026, 7, 22), 0)


class CandidateTests(TestCase):
    def test_deduplicates_by_doi_and_accumulates_queries(self) -> None:
        candidates = {}
        first = work("https://openalex.org/W1")
        duplicate = work("https://openalex.org/W2")

        collect_papers.merge_work(candidates, first, "hri", "social robot")
        collect_papers.merge_work(candidates, duplicate, "care", "companion robot")

        self.assertEqual(list(candidates), ["doi:10.0000/example"])
        candidate = candidates["doi:10.0000/example"]
        self.assertEqual(candidate["themes"], ["hri", "care"])
        self.assertEqual(candidate["metrics"]["query_match_count"], 2)

    def test_extracts_arxiv_identifier_from_location(self) -> None:
        item = work("https://openalex.org/W1", doi=None)
        item["locations"] = [{"landing_page_url": "https://arxiv.org/abs/2607.15156"}]

        self.assertEqual(collect_papers.extract_arxiv_id(item), "2607.15156")
        self.assertEqual(collect_papers.candidate_key(item), "arxiv:2607.15156")


class RankingTests(TestCase):
    thresholds = {
        "min_citations": 1,
        "min_reddit_mentions": 1,
        "min_x_original_posts": 3,
    }

    def candidate(self, identifier: str, citations: int = 0) -> dict:
        return collect_papers.new_candidate(
            work(identifier, title=identifier, doi=f"10.0000/{identifier}", citations=citations),
            "hri",
            "social robot",
        )

    def test_attention_gate_records_each_quantitative_reason(self) -> None:
        candidate = self.candidate("signal", citations=1)
        candidate["metrics"]["reddit_mentions_30d"] = 2
        candidate["metrics"]["x_original_posts_rolling_30d"] = 3

        collect_papers.evaluate_attention(candidate, self.thresholds)

        self.assertTrue(candidate["attention_gate"]["passed"])
        self.assertEqual(
            candidate["attention_gate"]["reasons"],
            ["citations>=1", "reddit_mentions>=1", "x_original_posts>=3"],
        )

    def test_queue_prioritizes_attention_and_keeps_relevance_reserve(self) -> None:
        cited = self.candidate("cited", citations=1)
        quiet = self.candidate("quiet")
        other_quiet = self.candidate("other-quiet")
        for candidate in (cited, quiet, other_quiet):
            collect_papers.evaluate_attention(candidate, self.thresholds)

        queue = collect_papers.select_review_queue(
            [quiet, cited, other_quiet], max_candidates=2, relevance_reserve=1
        )

        self.assertEqual(queue[0]["key"], "doi:10.0000/cited")
        self.assertEqual(queue[0]["selection_reason"], "attention_gate")
        self.assertEqual(queue[1]["selection_reason"], "relevance_reserve")


class ReviewReportTests(TestCase):
    def test_renders_only_review_queue_as_human_readable_markdown(self) -> None:
        candidate = collect_papers.new_candidate(
            work(
                "https://openalex.org/W1",
                title="A Small Social Robot",
                citations=2,
            ),
            "hri",
            "social robot",
        )
        candidate["selected_for_review"] = True
        candidate["selection_reason"] = "attention_gate"
        collect_papers.evaluate_attention(candidate, RankingTests.thresholds)

        report = collect_papers.render_review_report(
            collected_at=dt.date(2026, 7, 22),
            start=dt.date(2026, 6, 23),
            end=dt.date(2026, 7, 22),
            candidate_count=365,
            review_queue=[candidate],
            warnings=["Reddit unavailable"],
        )

        self.assertIn(
            "## 1. [A Small Social Robot](https://doi.org/10.0000/example)",
            report,
        )
        self.assertIn("- 著者：Sample Author", report)
        self.assertIn("- 全候補：365件", report)
        self.assertIn("- 外部指標の取得警告：1件", report)
        self.assertIn("- 選定理由：定量指標を通過", report)


class XHistoryTests(TestCase):
    def test_aggregates_recent_weekly_snapshots(self) -> None:
        with TemporaryDirectory() as directory:
            inbox = Path(directory)
            payload = {
                "collected_at": "2026-07-15",
                "candidates": [
                    {
                        "key": "doi:10.0000/example",
                        "metrics": {"x_original_posts_7d": 2},
                    }
                ],
            }
            (inbox / "literature-2026-07-15.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )

            totals = collect_papers.load_x_history(inbox, dt.date(2026, 7, 22), 30)

        self.assertEqual(totals, {"doi:10.0000/example": 2})


class EnrichmentFailureTests(TestCase):
    def test_reddit_stops_after_source_error(self) -> None:
        candidates = [
            collect_papers.new_candidate(
                work(f"W{index}", doi=f"10.0000/example-{index}"),
                "hri",
                "social robot",
            )
            for index in range(2)
        ]
        warnings = []

        with patch.object(
            collect_papers.requests,
            "get",
            side_effect=requests.ConnectTimeout("unavailable"),
        ) as request:
            collect_papers.enrich_reddit(
                candidates,
                dt.date(2026, 6, 23),
                dt.date(2026, 7, 22),
                warnings,
                0,
            )

        self.assertEqual(request.call_count, 1)
        self.assertEqual(candidates[0]["metric_status"]["crossref_reddit"], "error")
        self.assertEqual(
            candidates[1]["metric_status"]["crossref_reddit"],
            "skipped_after_source_error",
        )
        self.assertEqual(len(warnings), 1)
