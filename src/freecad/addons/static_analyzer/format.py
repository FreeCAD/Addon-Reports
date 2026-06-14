# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
FreeCAD Addon Analysis Report — Tabler Dashboard Generator.
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import template
from .models import Analysis


def report(reports: list[Analysis]) -> str:
    """Assemble the final standalone HTML page."""

    title = "FreeCAD Addons Report"
    time_str = datetime.strftime(datetime.now(timezone.utc), "%Y-%m-%d %H:%M:%S %Z")

    total = len(reports)
    avg_score = sum(r.score for r in reports) / total if total else 0
    total_base_addons = len(set(r.name for r in reports))

    data = {
        "title": title,
        "reports": reports,
        "time": time_str,
        "max_items_per_group": 20,
        "avg_score": avg_score,
        "total_files": sum(r.files for r in reports),
        "total_addons": total_base_addons,
        "total_high": sum(r.high for r in reports),
        "total_medium": sum(r.medium for r in reports),
        "total_dl_y": sum(r.stats.downloads_365d for r in reports),
        "total_dl_m": sum(r.stats.downloads_30d for r in reports),
    }

    return template.page_html.render(data)
