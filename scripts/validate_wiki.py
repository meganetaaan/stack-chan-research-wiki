#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import frontmatter
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
TAXONOMY_PATH = ROOT / "schemas" / "taxonomy.yaml"
PAPER_SCHEMA_PATH = ROOT / "schemas" / "paper.schema.json"
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
TAXONOMY_FIELDS = {
    "domains": "domains",
    "topics": "topics",
    "methods": "methods",
    "contexts": "contexts",
    "populations": "populations",
    "modalities": "modalities",
}


def load_taxonomy() -> dict:
    return yaml.safe_load(TAXONOMY_PATH.read_text(encoding="utf-8"))


def target_exists(source: Path, target: str) -> bool:
    target = target.strip()
    candidates = []
    if target.startswith("/"):
        candidates.append(WIKI / target.lstrip("/"))
    else:
        candidates.append(source.parent / target)
        candidates.append(WIKI / target)
        candidates.append(WIKI / "topics" / target)
        candidates.append(WIKI / "papers" / target)
    expanded = []
    for candidate in candidates:
        expanded.extend([candidate, candidate.with_suffix(".md"), candidate / "index.md"])
    return any(path.exists() for path in expanded)


def main() -> int:
    taxonomy = load_taxonomy()
    allowed_status = set(taxonomy["verification_status"])
    paper_schema = json.loads(PAPER_SCHEMA_PATH.read_text(encoding="utf-8"))
    paper_validator = Draft202012Validator(paper_schema)

    errors: list[str] = []
    ids: dict[str, Path] = {}
    dois: dict[str, Path] = {}

    for path in sorted(WIKI.rglob("*.md")):
        post = frontmatter.load(path)
        meta = post.metadata

        page_id = meta.get("id")
        if not page_id:
            errors.append(f"{path.relative_to(ROOT)}: frontmatter id is required")
        elif page_id in ids:
            first_path = ids[page_id].relative_to(ROOT)
            errors.append(
                f"{path.relative_to(ROOT)}: duplicate id '{page_id}' also used by {first_path}"
            )
        else:
            ids[page_id] = path

        status = meta.get("verification_status")
        if status and status not in allowed_status:
            errors.append(f"{path.relative_to(ROOT)}: unknown verification_status '{status}'")

        for field, taxonomy_key in TAXONOMY_FIELDS.items():
            allowed_values = set(taxonomy[taxonomy_key])
            for value in meta.get(field, []) or []:
                if value not in allowed_values:
                    errors.append(f"{path.relative_to(ROOT)}: unknown {field} value '{value}'")

        relevance = meta.get("stackchan_relevance") or {}
        for value in relevance.get("applicability", []) or []:
            if value not in taxonomy["applicability"]:
                errors.append(
                    f"{path.relative_to(ROOT)}: unknown applicability value '{value}'"
                )
        for value in relevance.get("components", []) or []:
            if value not in taxonomy["stackchan_components"]:
                errors.append(
                    f"{path.relative_to(ROOT)}: unknown stackchan component '{value}'"
                )

        if meta.get("type") == "paper":
            for error in paper_validator.iter_errors(meta):
                errors.append(f"{path.relative_to(ROOT)}: schema error: {error.message}")
            doi = (meta.get("doi") or "").strip().lower()
            if doi:
                if doi in dois:
                    first_path = dois[doi].relative_to(ROOT)
                    errors.append(
                        f"{path.relative_to(ROOT)}: duplicate DOI '{doi}' also used by {first_path}"
                    )
                else:
                    dois[doi] = path

        for target in LINK_RE.findall(post.content):
            if not target_exists(path, target):
                errors.append(f"{path.relative_to(ROOT)}: broken wiki link [[{target}]]")

    if errors:
        print("Validation failed:\n")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validation passed: {len(ids)} pages, {len(dois)} DOI records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
