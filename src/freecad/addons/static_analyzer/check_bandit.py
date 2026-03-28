# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
Static analysis using bandit.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from . import gitcmd
from .models import Analysis, Issue
from .config import Config


def _count_py_files(path: str) -> int:
    """
    Count all Python files recursively from a directory.
    """
    return sum(1 for _ in Path(path).rglob("*.[pP][yY]"))


def _run_bandit(path: str) -> dict:
    """
    Run bandit security analysis on the given path and return parsed results.
    """
    config = Path(Config.base_dir) / "bandit.yaml"
    if not config.exists():
        config = Path(__file__).parent / "bandit.yaml"

    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "bandit",
                "-r",
                "-f",
                "json",
                "-q",
                "-c",
                str(config.resolve()),
                path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return json.loads(result.stdout) if result.stdout else {}
    except FileNotFoundError:
        print(
            "Error: bandit is not installed. Install it with `pip install bandit`."
        )
        sys.exit(1)


def check_bandit(analysis: Analysis, repo: Path) -> None:
    path = repo.resolve()
    str_path = str(path)
    origin = gitcmd.get_origin(path)
    updated = gitcmd.get_updated(path)
    tag = gitcmd.get_tag(path)

    py_files_count = _count_py_files(str_path)
    print(f"Analyzing {py_files_count} Python files in {path!s}...\n")

    levels: defaultdict[str, list[Issue]] = defaultdict()
    levels.update({
        "HIGH": [],
        "MEDIUM": [],
        "LOW": [],
        "INFO": [],
    })

    analysis.files = py_files_count
    analysis.issues = levels
    analysis.git_repo = origin
    analysis.updated = updated
    analysis.tag = tag

    if not py_files_count:
        return

    bandit_results = _run_bandit(str_path)
    for issue in bandit_results.get("results", []):
        file = Path(issue["filename"]).relative_to(path)
        levels[issue["issue_severity"]].append(
            Issue(
                str(file),
                issue["line_number"],
                issue["issue_text"],
            )
        )
