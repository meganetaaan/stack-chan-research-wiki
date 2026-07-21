.PHONY: setup lint test validate serve build collect

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements-dev.txt

lint:
	ruff check .

test:
	python -m unittest discover -s tests

validate:
	python scripts/validate_wiki.py

serve:
	mkdocs serve

build:
	mkdocs build --strict

collect:
	python scripts/collect_papers.py
