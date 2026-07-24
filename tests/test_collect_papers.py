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
    abstract: str = "",
) -> dict:
    return {
        "id": identifier,
        "doi": doi,
        "display_name": title,
        "abstract": abstract,
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

    def test_reconstructs_openalex_abstract(self) -> None:
        item = work("https://openalex.org/W1")
        item["abstract_inverted_index"] = {
            "robot": [2],
            "A": [0],
            "social": [1],
        }

        self.assertEqual(collect_papers.work_abstract(item), "A social robot")


class SourceParsingTests(TestCase):
    def test_parses_arxiv_atom_metadata(self) -> None:
        feed = b"""<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom"
              xmlns:arxiv="http://arxiv.org/schemas/atom">
          <entry>
            <id>https://arxiv.org/abs/2607.12345v2</id>
            <updated>2026-07-22T10:00:00Z</updated>
            <published>2026-07-20T10:00:00Z</published>
            <title>Embodied Dialogue</title>
            <summary>A social robot dialogue study.</summary>
            <author><name>Example Author</name></author>
            <category term="cs.RO" />
            <arxiv:doi>10.0000/arxiv-example</arxiv:doi>
          </entry>
        </feed>"""

        works = collect_papers.parse_arxiv_feed(feed)

        self.assertEqual(len(works), 1)
        self.assertEqual(works[0]["ids"]["arxiv"], "https://arxiv.org/abs/2607.12345")
        self.assertEqual(works[0]["publication_date"], "2026-07-20")
        self.assertEqual(works[0]["updated_date"], "2026-07-22")
        self.assertEqual(works[0]["authorships"][0]["author"]["display_name"], "Example Author")

    def test_filters_acl_anthology_by_ingest_date_and_focus_terms(self) -> None:
        anthology = b"""<?xml version="1.0" encoding="UTF-8"?>
        <collection id="2026.sigdial">
          <volume id="1" ingest-date="2026-07-21">
            <meta>
              <booktitle>SIGDIAL 2026</booktitle>
              <month>August</month><year>2026</year>
            </meta>
            <paper id="1">
              <title>Turn-Taking for a Social Robot</title>
              <author><first>Ada</first><last>Lovelace</last></author>
              <abstract>We study backchannel timing.</abstract>
              <url>2026.sigdial-1.1</url>
            </paper>
            <paper id="2">
              <title>Discourse Parsing</title>
              <abstract>No embodied interaction.</abstract>
              <url>2026.sigdial-1.2</url>
            </paper>
          </volume>
        </collection>"""

        results = collect_papers.parse_acl_anthology(
            anthology,
            {"id": "sigdial", "name": "SIGDIAL", "theme": "dialogue_language"},
            dt.date(2026, 6, 25),
            dt.date(2026, 7, 24),
            ["social robot", "turn-taking", "backchannel"],
        )

        self.assertEqual(len(results), 1)
        candidate, matches = results[0]
        self.assertEqual(candidate["id"], "https://aclanthology.org/2026.sigdial-1.1/")
        self.assertEqual(candidate["authorships"][0]["author"]["display_name"], "Ada Lovelace")
        self.assertEqual(matches, ["social robot", "turn-taking", "backchannel"])

    def test_normalizes_crossref_conference_metadata(self) -> None:
        venue = {
            "name": "ACM/IEEE HRI",
            "container_patterns": ["human-robot interaction"],
        }
        item = {
            "DOI": "10.0000/HRI-EXAMPLE",
            "title": ["Long-Term Interaction with a Social Robot"],
            "author": [{"given": "Ada", "family": "Lovelace"}],
            "container-title": [
                "Proceedings of the ACM/IEEE International Conference on Human-Robot Interaction"
            ],
            "published-online": {"date-parts": [[2026, 7, 20]]},
            "type": "proceedings-article",
            "is-referenced-by-count": 2,
        }

        work = collect_papers.crossref_item_to_work(item, venue)

        self.assertTrue(collect_papers.crossref_venue_matches(item, venue))
        self.assertEqual(work["doi"], "10.0000/hri-example")
        self.assertEqual(work["publication_date"], "2026-07-20")
        self.assertEqual(work["authorships"][0]["author"]["display_name"], "Ada Lovelace")
        self.assertEqual(work["_discovery_source"], "crossref_conference")

    def test_crossref_venue_match_rejects_similar_container(self) -> None:
        item = {"container-title": ["International Conference on Robotics"]}
        venue = {"container_patterns": ["human-robot interaction"]}

        self.assertFalse(collect_papers.crossref_venue_matches(item, venue))


class RankingTests(TestCase):
    thresholds = {
        "min_citations": 1,
        "min_reddit_mentions": 1,
        "min_x_original_posts": 3,
    }
    relevance = {
        "min_score": 30,
        "anchor_terms": ["social robot", "human-robot", "spoken dialogue system"],
        "topic_terms": ["dialogue", "interaction", "trust"],
        "trusted_venue_patterns": ["human-robot interaction", "sigdial"],
        "weights": {
            "title_anchor": 30,
            "abstract_anchor": 20,
            "additional_anchor": 5,
            "title_topic": 5,
            "abstract_topic": 2,
            "topic_cap": 20,
            "trusted_venue": 25,
            "source_diversity": 5,
            "source_diversity_cap": 10,
        },
    }

    def candidate(
        self, identifier: str, citations: int = 0, title: str | None = None
    ) -> dict:
        candidate = collect_papers.new_candidate(
            work(
                identifier,
                title=title or f"Social robot {identifier}",
                doi=f"10.0000/{identifier}",
                citations=citations,
            ),
            "hri",
            "social robot",
        )
        collect_papers.evaluate_relevance(candidate, self.relevance)
        return candidate

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

    def test_queue_keeps_relevant_emerging_reserve(self) -> None:
        cited = self.candidate("cited", citations=1)
        quiet = self.candidate("quiet")
        other_quiet = self.candidate("other-quiet")
        for candidate in (cited, quiet, other_quiet):
            collect_papers.evaluate_attention(candidate, self.thresholds)

        queue = collect_papers.select_review_queue(
            [quiet, cited, other_quiet], max_candidates=2, relevance_reserve=1
        )

        self.assertEqual(queue[0]["key"], "doi:10.0000/cited")
        self.assertEqual(queue[0]["selection_reason"], "relevance_and_attention")
        self.assertEqual(queue[1]["selection_reason"], "emerging_relevance")

    def test_attention_candidates_do_not_consume_relevance_reserve(self) -> None:
        cited = [self.candidate(f"cited-{index}", citations=1) for index in range(3)]
        quiet = self.candidate("quiet")
        quiet["metrics"]["query_match_count"] = 5
        for candidate in [*cited, quiet]:
            collect_papers.evaluate_attention(candidate, self.thresholds)

        queue = collect_papers.select_review_queue(
            [*cited, quiet], max_candidates=3, relevance_reserve=1
        )

        self.assertEqual(len(queue), 3)
        self.assertEqual(queue[-1]["key"], "doi:10.0000/quiet")
        self.assertEqual(queue[-1]["selection_reason"], "emerging_relevance")

    def test_irrelevant_cited_paper_does_not_outrank_relevant_new_paper(self) -> None:
        irrelevant = self.candidate(
            "governance",
            citations=20,
            title="A framework for university AI governance",
        )
        relevant = self.candidate(
            "bystander",
            title="The bystander effect in human-robot interaction",
        )
        for candidate in (irrelevant, relevant):
            collect_papers.evaluate_attention(candidate, self.thresholds)

        queue = collect_papers.select_review_queue(
            [irrelevant, relevant], max_candidates=2, relevance_reserve=1
        )

        self.assertFalse(irrelevant["relevance"]["passed"])
        self.assertEqual([candidate["key"] for candidate in queue], [relevant["key"]])


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
        candidate["selection_reason"] = "relevance_and_attention"
        collect_papers.evaluate_relevance(candidate, RankingTests.relevance)
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
        self.assertIn("- 収集元：openalex", report)
        self.assertIn("- 全候補：365件", report)
        self.assertIn("- 外部指標の取得警告：1件", report)
        self.assertIn("- 選定理由：関連性合格・定量指標を通過", report)
        self.assertIn("- 関連性：", report)


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
