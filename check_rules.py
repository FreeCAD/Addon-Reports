# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
Apply custom rules defined in rules.py
"""

from __future__ import annotations

from pathlib import Path
from models import Analysis

import rules

RULES = [
    rule
    for name, rule in rules.__dict__.items()
    if name.startswith("rule_") and callable(rule)
]


def check_rules(analysis: Analysis, repo: Path) -> None:
    for rule in RULES:
        rule(analysis, repo)
