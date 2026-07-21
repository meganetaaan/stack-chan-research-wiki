#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
WIKI = ROOT / "wiki"

TYPE_TO_DIR = {
    "paper": "papers",
    "topic": "topics",
    "robot": "robots",
    "synthesis": "synthesis",
}

TEMPLATE_IDS = {
    "paper": "doi-10-0000-example",
    "topic": "topic-id",
    "robot": "robot-id",
    "synthesis": "synthesis-id",
}

TEMPLATE_HEADINGS = {
    "paper": "# 論文タイトル",
    "topic": "# トピック名",
    "robot": "# ロボット名",
    "synthesis": "# 横断レビューの題名",
}

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def create_page(page_type: str, page_id: str, title: str) -> Path:
    if not ID_RE.fullmatch(page_id):
        raise ValueError("id must be a lowercase kebab-case slug")

    template_path = TEMPLATES / f"{page_type}.md"
    template = template_path.read_text(encoding="utf-8")
    template_id = TEMPLATE_IDS[page_type]
    title_yaml = json.dumps(title, ensure_ascii=False)

    template = template.replace(f'id: "{template_id}"', f'id: "{page_id}"', 1)
    template = template.replace('title: ""', f"title: {title_yaml}", 1)
    template = template.replace(TEMPLATE_HEADINGS[page_type], f"# {title}", 1)

    destination = WIKI / TYPE_TO_DIR[page_type] / f"{page_id}.md"
    if destination.exists():
        raise FileExistsError(f"Already exists: {destination}")
    destination.write_text(template, encoding="utf-8")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("page_type", choices=TYPE_TO_DIR)
    parser.add_argument("--id", required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    try:
        destination = create_page(args.page_type, args.id, args.title)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    print(destination.relative_to(ROOT))


if __name__ == "__main__":
    main()
