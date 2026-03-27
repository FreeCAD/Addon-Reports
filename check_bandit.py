# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
Static analysis using bandit.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import gitcmd
from models import Analysis, Issue


def _collect_python_files(path: str):
    """
    Collect all Python files recursively from a directory.
    """
    py_files = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith(".py"):
                py_files.append(os.path.join(root, f))
    return py_files


def _run_bandit(path: str) -> dict:
    """
    Run bandit security analysis on the given path and return parsed results.
    """
    try:
        config = Path(__file__).parent / "bandit.yaml"
    except NameError:
        config = Path.cwd() / "bandit.yaml"
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

    py_files = _collect_python_files(str_path)
    print(f"Analyzing {len(py_files)} Python files in {path!s}...\n")

    levels: defaultdict[str, list[Issue]] = defaultdict()
    levels.update({
        "HIGH": [],
        "MEDIUM": [],
        "LOW": [],
        "INFO": [],
    })

    analysis.files = len(py_files)
    analysis.issues = levels
    analysis.git_repo = origin
    analysis.updated = updated
    analysis.tag = tag

    if not py_files:
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
