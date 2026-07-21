#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import frontmatter

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"

SECTIONS = [
    "papers",
    "topics",
    "robots",
    "researchers",
    "datasets",
    "methods",
    "metrics",
    "venues",
    "projects",
    "synthesis",
]


def build_section(section: str) -> None:
    directory = WIKI / section
    rows = []
    for path in sorted(directory.glob("*.md")):
        if path.name == "index.md":
            continue
        post = frontmatter.load(path)
        title = post.metadata.get("title", path.stem)
        year = post.metadata.get("year", "")
        status = post.metadata.get("verification_status", "")
        rows.append((title, path.name, year, status))

    lines = [
        "---",
        "type: index",
        f"id: {section}-index",
        f'title: "{section}"',
        "---",
        "",
        f"# {section}",
        "",
        "| ページ | 年 | 状態 |",
        "|---|---:|---|",
    ]
    for title, filename, year, status in rows:
        lines.append(f"| [{title}]({filename}) | {year} | {status} |")
    lines.append("")
    (directory / "index.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    for section in SECTIONS:
        build_section(section)
    print("Indexes updated")


if __name__ == "__main__":
    main()
