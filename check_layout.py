# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
Static check of addon file structure.
"""

from __future__ import annotations

from pathlib import Path

from models import Analysis, Issue

ISSUE_CODE_INIT_ON_EXEC = "L001"
ISSUE_CODE_INIT_IN_FREECAD = "L002"


def check_layout(analysis: Analysis, repo: Path) -> None:
    dir_layout = {"Init.py", "InitGui.py"}
    info = analysis.issues["INFO"]
    high = analysis.issues["HIGH"]

    is_dir = False
    is_ext = False

    for name in dir_layout:
        if (repo / name).exists():
            info.append(Issue("Layout", 0, "Uses exec based layout"))
            is_dir = True
            break

    pkg = repo / "freecad"
    if pkg.exists() and pkg.is_dir():
        info.append(Issue("Layout", 0, "Uses extension based layout"))
        is_ext = True
        if (pkg / "__init__.py").exists():
            high.append(
                Issue(
                    "Layout",
                    0,
                    "Invalid __init__.py file in freecad package root.",
                    code=ISSUE_CODE_INIT_IN_FREECAD,
                )
            )

    if (repo / "__init__.py").exists():
        msg = "Change to Init.py" if is_dir else ""
        high.append(
            Issue(
                "Layout",
                0,
                f"Invalid __init__.py file in root. {msg}",
                code=ISSUE_CODE_INIT_ON_EXEC,
            )
        )

    if not any((is_ext, is_dir)):
        info.append(Issue("Layout", 0, "No Mod init scripts found"))
