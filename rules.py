# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
Custom rules.
"""

from __future__ import annotations

from pathlib import Path

from check_layout import ISSUE_CODE_INIT_IN_FREECAD, ISSUE_CODE_INIT_ON_EXEC
from models import Analysis


def rule_AddonManager(analysis: Analysis, repo: Path) -> None:
    """
    Addon Manager can run standalone outside of FreeCAD, some init checking rules does not apply.
    """

    if analysis.name != "AddonManager":
        return

    print(f"Applying Rule rule_AddonManager on {analysis.name}")
    high = analysis.issues["HIGH"]
    remove_codes = (ISSUE_CODE_INIT_IN_FREECAD, ISSUE_CODE_INIT_ON_EXEC)
    indexes = (i for i, v in enumerate(high) if v.code in remove_codes)
    for i in indexes:
        del high[i]
