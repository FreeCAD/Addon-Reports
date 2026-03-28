# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
HTML Renderer.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import re
import html
from ..models import Analysis

_loader = FileSystemLoader(Path(__file__).parent)
_env = Environment(loader=_loader)
_id_pattern = re.compile(r"\W+")

_severity_config: dict[str, dict] = {
    "HIGH": {"icon": "alert-triangle", "color": "danger", "open": True},
    "MEDIUM": {"icon": "alert-circle", "color": "warning", "open": False},
    "LOW": {"icon": "info-circle", "color": "info", "open": False},
    "INFO": {"icon": "message-circle", "color": "success", "open": False},
}


def _year() -> str:
    return str(datetime.now().year)


def _format_float_filter(value):
    if value is None:
        return ""
    try:
        formatted = "{:,.2f}".format(float(value))
        return formatted.rstrip("0").rstrip(".")
    except (ValueError, TypeError):
        return value


def _rpt_id_filter(rpt) -> str:
    raw = f"addon-{rpt.name}-{rpt.git_ref}"
    return _id_pattern.sub("-", raw)


def _score_color_filter(score: float) -> str:
    """Map a 0-100 score to a Tabler colour name."""
    if score >= 90:
        return "success"
    if score >= 70:
        return "primary"
    if score >= 50:
        return "warning"
    return "danger"


def _time_ago_filter(past_datetime: datetime | None) -> str:
    """Human-readable relative time string (days, months, years)."""
    if not past_datetime:
        return ""
    now = datetime.now(past_datetime.tzinfo)
    total_days = int((now - past_datetime).total_seconds()) // 86400
    years = total_days // 365
    remaining_days = total_days % 365
    months = remaining_days // 30
    days = remaining_days % 30
    if years > 0:
        return f"{round(total_days/365)} yr"
    if months > 0:
        return f"{round(remaining_days / 30)} mo"
    if days > 0:
        return f"{days} d"
    return "today"


def _severity_badge(count: int, color: str) -> str:
    if count:
        return f'<span class="badge bg-{color} text-{color}-fg">{count}</span>'
    return '<span class="text-secondary">0</span>'


def _ellipsis(text: str, max: int = 140, default: str = "") -> str:
    text = (text or "").strip()
    if not text:
        return default
    if len(text) <= max:
        return text
    return f"{text[0:max]}..."


def _issues_section(item: Analysis, max_items_per_group: int) -> str:
    sections: list[str] = []
    for level in ("HIGH", "MEDIUM", "LOW", "INFO"):
        data = item.issues.get(level, [])
        if not data:
            continue
        cfg = _severity_config.get(level, _severity_config["LOW"])

        files: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for issue in data:
            files[issue.subject].append((issue.line, issue.text))

        file_items: list[str] = []
        total = 0
        for filepath, items in files.items():
            issue_lines: list[str] = []
            for row, (line, text) in enumerate(items):
                total += 1
                if row == max_items_per_group:
                    remaining = len(items) - max_items_per_group
                    issue_lines.append(
                        f'<li class="text-secondary fst-italic">'
                        f"… {remaining} more issues</li>"
                    )
                    break
                line_pfx = (
                    f'<span class="text-secondary">line {line}:</span> '
                    if line
                    else ""
                )
                issue_lines.append(
                    f"<li>{line_pfx}{html.escape(str(text))}</li>"
                )

            ul = "\n".join(issue_lines)
            file_items.append(
                f'<div class="issue-file">'
                f'<code class="file-path">{filepath!s}</code>'
                f'<span class="badge bg-secondary-lt ms-1">{len(items)}</span>'
                f'<ul class="mt-1 mb-2">{ul}</ul>'
                f"</div>"
            )

        open_attr = "open" if cfg["open"] else ""
        body = "\n".join(file_items)
        sections.append(
            f'<details class="issue-group severity-{level.lower()}" {open_attr}>'
            f"<summary>"
            f'<i class="ti ti-{cfg["icon"]} me-1"></i> {level} '
            f'<span class="badge bg-{cfg["color"]} text-{cfg["color"]}-fg ms-2">{total}</span>'
            f"</summary>"
            f'<div class="issue-content">{body}</div>'
            f"</details>"
        )

    if not sections:
        return (
            '<div class="text-success py-2">'
            '<i class="ti ti-circle-check me-1"></i>No issues found</div>'
        )
    return "\n".join(sections)


_env.filters["fmt_float"] = _format_float_filter
_env.filters["rpt_id"] = _rpt_id_filter
_env.filters["score_color"] = _score_color_filter
_env.filters["time_ago"] = _time_ago_filter

_env.globals["severity_badge"] = _severity_badge
_env.globals["ellipsis"] = _ellipsis
_env.globals["issues_section"] = _issues_section
_env.globals["year"] = _year

page_html = _env.get_template("page.html")
