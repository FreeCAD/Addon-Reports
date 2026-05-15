# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
Fetch and get all stats from matomo and github.
"""

from __future__ import annotations

import datetime
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

import httpx

from .config import Config
from .models import Analysis
from .utils import thread_safe_cache

_matomo_label_pattern = re.compile(
    r"/CatalogCache/(?P<addon>.*?)/\d+-(?P<branch>.*?)\.zip"
)


class _Count:
    def __init__(self) -> None:
        self.value = 0

    def add(self, value: int) -> None:
        self.value += value


def _get_data(url: str, **params) -> Any:
    with httpx.Client() as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def _date_range(days: int = 30) -> str:
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    date_range = f"{start.strftime('%Y-%m-%d')},{end.strftime('%Y-%m-%d')}"
    return date_range


@thread_safe_cache
def _get_download_stats(days: int) -> dict[tuple[str, str], _Count]:
    data = cast(
        list[dict[str, Any]],
        _get_data(
            Config.matomo_stats_endpoint,
            period="range",
            date=_date_range(days),
            module="API",
            format="JSON",
            idSite="1",
            method="Actions.getDownloads",
            expanded="1",
            showMetadata="0",
            filter_limit="-1",
        ),
    )

    stats: dict[tuple[str, str], _Count] = defaultdict(_Count)

    for item in data[0].get("subtable", []):
        label = item.get("label")
        if not label:
            continue
        if match := _matomo_label_pattern.match(label):
            addon = match.group("addon")
            branch = match.group("branch")
            stats[(addon, branch)].add(cast(int, item.get("nb_hits", 0)))

    return stats


@thread_safe_cache
def _get_github_stats() -> dict[str, dict[str, int]]:
    return cast(
        dict[str, dict[str, int]], _get_data(Config.github_stats_endpoint)
    )


def check_stats(analysis: Analysis, repo: Path) -> None:
    downloads_365d = _get_download_stats(365)
    downloads_30d = _get_download_stats(30)
    github_data = _get_github_stats()

    if count_365d := downloads_365d.get((analysis.name, analysis.git_branch_display)):
        analysis.stats.downloads_365d = count_365d.value
    elif count_365d := downloads_365d.get((analysis.name, analysis.git_ref)):
        analysis.stats.downloads_365d = count_365d.value

    if count_30d := downloads_30d.get((analysis.name, analysis.git_branch_display)):
        analysis.stats.downloads_30d = count_30d.value
    elif count_30d := downloads_30d.get((analysis.name, analysis.git_ref)):
        analysis.stats.downloads_30d = count_30d.value

    github = github_data.get(analysis.git_repo)
    if not github:
        if analysis.git_repo.endswith(".git"):
            repo_url = analysis.git_repo[0:-4]
            github = github_data.get(repo_url)
        else:
            repo_url = f"{analysis.git_repo}.git"
            github= github_data.get(repo_url)

    if github:
        analysis.stats.direct_forks = github.get("forks_count", 0)
        analysis.stats.total_forks = github.get("network_count", 0)
        analysis.stats.stargazers = github.get("stargazers_count", 0)
        analysis.stats.open_issues = github.get("open_issues_count", 0)
        analysis.stats.subscribers = github.get("subscribers_count", 0)
        analysis.stats.created_at = github.get("created_at", '')
