# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
Fetch and get all stats from matomo and github.
"""

from __future__ import annotations

import calendar
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any, cast

import httpx

from .config import Config
from .models import Analysis
from .utils import thread_safe_cache

_matomo_label_pattern = re.compile(
    r"/CatalogCache/(?P<addon>.*?)/\d+-(?P<branch>.*?)\.zip"
)


def _get_month_range(period: str = "current") -> tuple[str, str]:
    """
    Returns start and end dates in YYYY-MM-DD format.
    """
    today = date.today()

    if period == "last_month":
        # Calculate previous month and year
        prev_month = 12 if today.month == 1 else today.month - 1
        prev_year = today.year - 1 if today.month == 1 else today.year

        start_date = date(prev_year, prev_month, 1)
        end_date = date(
            prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1]
        )

    elif period == "last_12_months":
        # 12 full calendar months ending today's month (e.g., Sep 1, 2025 - Aug 31, 2026)
        start_month = (today.month % 12) + 1
        start_year = today.year if today.month == 12 else today.year - 1

        start_date = date(start_year, start_month, 1)
        end_date = date(
            today.year,
            today.month,
            calendar.monthrange(today.year, today.month)[1],
        )

    elif period == "last30":
        start_date = today - timedelta(days=30)
        end_date = today

    elif period == "last365":
        start_date = today - timedelta(days=365)
        end_date = today

    else:  # 'current'
        start_date = today.replace(day=1)
        end_date = today.replace(
            day=calendar.monthrange(today.year, today.month)[1]
        )

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def _get_data(url: str, **params) -> Any:
    with httpx.Client() as client:
        response = client.get(url, params=params, timeout=15.0)
        response.raise_for_status()
        return response.json()


def _get_addon_downloads(name: str, branch: str, start: str, end: str) -> int:
    try:
        data = _get_data(
            Config.matomo_stats_endpoint,
            period="month",
            date=f"{start},{end}",
            module="API",
            format="JSON",
            idSite="1",
            method="Actions.getDownloads",
            label=f"addons.freecad.org > /CatalogCache/{name}/0-{branch}.zip",
            format_metrics=0,
            expanded=1,
            showMetadata="0",
            filter_limit="-1",
            disable_generic_filters="1",
        )
    except Exception:
        return 0
    else:
        total = 0
        for period in data.values():
            for row in period:
                total += int(row["nb_hits"])
        return total


@thread_safe_cache
def _get_github_stats() -> dict[str, dict[str, int]]:
    return cast(
        dict[str, dict[str, int]], _get_data(Config.github_stats_endpoint)
    )


def check_stats(analysis: Analysis, repo: Path) -> None:
    start, end = _get_month_range("last30")
    last30 = _get_addon_downloads(
        analysis.name,
        analysis.git_ref,
        start,
        end,
    )
    if not last30:
        last30 = _get_addon_downloads(
            analysis.name,
            analysis.git_branch_display,
            start,
            end,
        )
    start, end = _get_month_range("last365")
    last365 = _get_addon_downloads(analysis.name, analysis.git_ref, start, end)
    if not last365:
        last365 = _get_addon_downloads(
            analysis.name,
            analysis.git_branch_display,
            start,
            end,
        )

    analysis.stats.downloads_30d = last30
    analysis.stats.downloads_365d = last365

    github_data = _get_github_stats()
    github = github_data.get(analysis.git_repo)
    if not github:
        if analysis.git_repo.endswith(".git"):
            repo_url = analysis.git_repo[0:-4]
            github = github_data.get(repo_url)
        else:
            repo_url = f"{analysis.git_repo}.git"
            github = github_data.get(repo_url)

    if github:
        analysis.stats.direct_forks = github.get("forks_count", 0)
        analysis.stats.total_forks = github.get("network_count", 0)
        analysis.stats.stargazers = github.get("stargazers_count", 0)
        analysis.stats.open_issues = github.get("open_issues_count", 0)
        analysis.stats.subscribers = github.get("subscribers_count", 0)
        analysis.stats.created_at = github.get("created_at", "")
