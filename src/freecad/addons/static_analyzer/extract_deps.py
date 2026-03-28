# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
Dependencies analysis using pipreqs.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .models import Analysis
from .config import Config

INTERNALS = {
    mod.lower()
    for mod in (
        "Arch",
        "Assembly",
        "BIM",
        "CAM",
        "Draft",
        "Fem",
        "Import",
        "Material",
        "Mesh",
        "OpenSCAD",
        "Part",
        "PartDesign",
        "Plot",
        "Points",
        "ReverseEngineering",
        "Robot",
        "Sketcher",
        "Spreadsheet",
        "TechDraw",
        "Tux",
        "Web",
        "BOPTools",
        "pivy",
        "PySide",
        "TestApp",
        "FreeCAD",
        "FreeCADGui",
    )
}

COMPAT = {
    "pyside2",
    "pyside6",
    "shiboken6",
    "shiboken2",
}

KNOWN_MODS = {
    "curves",
    "render",
}

CONSTRAINTS_FILES = {
    "constraints/constraints-py310.txt",
    "constraints.txt",
    "ALLOWED_PYTHON_PACKAGES.txt",
}

SEP = re.compile(r"[^a-zA-Z0-9_-]")


def extend_allowed(path: Path, data: set[str]) -> None:
    if not path.exists():
        return
    content = path.read_text()
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            data.add(SEP.split(line)[0].lower())


def allowed() -> set[str]:
    data = set()
    base = Path(Config.base_dir) / "catalog"
    for file in CONSTRAINTS_FILES:
        extend_allowed(base / file, data)
    return data


def repo_requirements(analysis: Analysis, repo: Path) -> None:
    ALLOWED = allowed()
    print(f"** Analyzing requirements of {repo!s}")
    tmp = Path(Config.base_dir) / ".tmp"
    if not tmp.exists():
        tmp.mkdir()
    file = tmp / f"{repo.stem}.txt"
    if not file.exists():
        print(f"** Generating {repo.stem}.txt")
        subprocess.run(
            [
                "uv",
                "run",
                "pipreqs",
                "--ignore-errors",
                "--no-follow-links",
                "--mode",
                "no-pin",
                "--savepath",
                str(file),
                str(repo.resolve()),
            ],
        )

    if file.exists():
        requirements = file.read_text(encoding="utf-8")
        out = []
        for line in requirements.splitlines():
            m = SEP.split(line)
            dep = m[0].strip()
            if not dep:
                continue
            if dep.lower() in INTERNALS:
                out.append(f"Internal: {line}")
            else:
                dep = dep.lower()
                if dep in COMPAT:
                    out.append(f"Compat: {line}")
                elif dep in KNOWN_MODS:
                    out.append(f"Mod: {line}")
                elif dep in ALLOWED:
                    out.append(f"Pip: {line}")
                else:
                    out.append(f"Warn: {line} (Not in AddonManager allowed packages)")

        out.sort()
        analysis.requirements = out
    else:
        analysis.requirements = [
            "Error: Analysis failed due to some "
            "invalid python files with syntax errors",
        ]
