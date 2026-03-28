# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
Base Data models.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Issue:
    subject: str
    line: int
    text: str
    source: str = ""
    code: str = ""


@dataclass
class Stats:
    downloads_365d: int = 0
    downloads_30d: int = 0
    stargazers: int = 0
    direct_forks: int = 0
    open_issues: int = 0
    total_forks: int = 0
    subscribers: int = 0


@dataclass
class Analysis:
    name: str
    files: int = 0
    issues: defaultdict[str, list[Issue]] = field(default_factory=defaultdict)
    git_repo: str = ""
    git_ref: str = ""
    git_branch_display: str = ""
    updated: datetime | None = None
    requirements: list[str] = field(default_factory=list)
    tag: str = ""
    pkg_version: str = ""
    pkg_branch: str = ""
    pkg_license: str = ""
    pkg_description: str = ""
    pkg_people: list[str] = field(default_factory=list)
    stats: Stats = field(default_factory=Stats)

    @property
    def high(self) -> int:
        return len(self.issues.get("HIGH", ()))

    @property
    def medium(self) -> int:
        return len(self.issues.get("MEDIUM", ()))

    @property
    def low(self) -> int:
        return len(self.issues.get("LOW", ()))

    @property
    def score(self) -> float:
        raw = 100 - (self.high * 3 + self.medium * 1 + self.low * 0.1)
        return max(0, raw)

    @property
    def total_issues(self) -> int:
        return self.high + self.medium + self.low
