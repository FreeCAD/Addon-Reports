# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
FreeCAD Addon Analysis Report — Tabler Dashboard Generator.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from itertools import groupby

from . import template
from .models import Analysis


def serialize(data: object) -> object:
    if is_dataclass(data):
        return {f.name: serialize(getattr(data, f.name)) for f in fields(data)}
    match data:
        case str() | int() | float():
            return data
        case list() | tuple():
            return [serialize(v) for v in data]
        case dict() | defaultdict():
            return {k: serialize(v) for k, v in data.items()}
        case datetime():
            return data.isoformat()
        case _:
            return str(data)


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


def report_json(reports: list[Analysis]) -> str:
    """Dump report data as json"""
    reports.sort(key=lambda x: x.name)
    data = {
        "date": datetime.strftime(datetime.now(timezone.utc), "%Y-%m-%d"),
        "addons": {
            name: list(items) for name, items in groupby(reports, lambda r: r.name)
        },
    }
    return json.dumps(serialize(data), indent=2)
