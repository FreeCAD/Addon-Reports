# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
Main process pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
from pathlib import Path
from threading import Thread

import format as fmt
import gitcmd
from check_bandit import check_bandit
from check_layout import check_layout
from check_package import check_package
from check_rules import check_rules
from check_stats import check_stats
from extract_deps import repo_requirements
from models import Analysis, Issue
from config import Config


def search_files(base: Path, name: str, *, regex: bool = False) -> list[Path]:
    if not base.is_dir():
        raise ValueError(f"{base} is not a valid directory")

    base = base.resolve()
    if not regex:
        if (path := base / name).exists():
            return [path]
        return []

    pattern = re.compile(name, re.IGNORECASE)

    return [
        p
        for p in base.rglob("*")
        if pattern.fullmatch(str(p.relative_to(base)))
    ]


def check_file_present(
    analysis: Analysis,
    base: Path,
    name: str,
    severity: str = "HIGH",
    message: str = "File not found.",
    *,
    regex: bool = False,
) -> None:
    files = search_files(base, name, regex=regex)
    if not files:
        name = name.replace(r"\.", ".") if regex else name
        if level := analysis.issues.get(severity):
            level.append(Issue(name, 0, message))
        else:
            analysis.issues[severity] = [Issue(name, 0, message)]


def repo_task(repo: Path, analysis: Analysis, dep_tasks: list[Thread]) -> None:
    check_bandit(analysis, repo)
    check_stats(analysis, repo)

    deps = Thread(target=repo_requirements, args=(analysis, repo))
    dep_tasks.append(deps)
    deps.start()

    check_file_present(analysis, repo, r"package\.xml", "HIGH", regex=True)
    check_file_present(analysis, repo, r"license.*", "LOW", regex=True)
    check_file_present(analysis, repo, r"readme\.md", "HIGH", regex=True)
    check_package(analysis, repo)
    check_layout(analysis, repo)
    check_rules(analysis, repo)


def start():
    if not Config.skip_clone:
        gitcmd.clone_repos()

    target_path = Path(__file__).parent / Config.repositories_dir
    if not target_path.exists():
        target_path.mkdir(parents=True)

    tasks: list[Thread] = []
    dep_tasks: list[Thread] = []
    reports: list[Analysis] = []
    j_idx = 0

    for path in target_path.iterdir():
        if path.is_dir():
            name, _, branch_display = path.name.rpartition("_")
            analysis = Analysis(
                name,
                git_ref=gitcmd.get_branch(path),
                git_branch_display=branch_display,
            )
            reports.append(analysis)
            thread = Thread(target=repo_task, args=(path, analysis, dep_tasks))
            j_idx += 1
            tasks.append(thread)
            thread.start()
            if Config.max_repos > 0 and j_idx >= Config.max_repos:
                break

    # Synchronize
    for t in tasks:
        if t is not None:
            t.join()

    for t in dep_tasks:
        if t is not None:
            t.join()

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    date = datetime.strftime(datetime.now(timezone.utc), "%Y-%m-%d")
    reports.sort(key=lambda x: (-x.score, -x.stats.downloads_365d, x.name))
    (output_dir / f"report-{date}.html").write_text(fmt.report(reports))
