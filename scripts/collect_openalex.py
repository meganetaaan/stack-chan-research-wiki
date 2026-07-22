#!/usr/bin/env python3
"""Backward-compatible entry point for the multi-source paper collector."""

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("collect_papers.py")), run_name="__main__")
