# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
Git API.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from threading import Thread

from .config import Config


def clone_repo(repo_url: str, clone_path: str, branch: str) -> None:
    if not os.path.exists(clone_path):
        print(f"Cloning {repo_url} into {clone_path}")
        cmd = [
            "git",
            "clone",
            "--depth=1",
            "-b",
            branch,
            "--single-branch",
            repo_url,
            clone_path,
        ]
        subprocess.run(cmd)
    else:
        print(f"Synching {repo_url} in {clone_path}")
        subprocess.run(
            [
                "git",
                "fetch",
                "--depth=1",
                "--force",
                "origin",
                branch,
            ],
            cwd=clone_path,
        )
        subprocess.run(
            [
                "git",
                "reset",
                "--hard",
                f"origin/{branch}",
            ],
            cwd=clone_path,
        )
        subprocess.run(["git", "clean", "-fdx"], cwd=clone_path)


def clone_catalog() -> None:
    base = Path(Config.base_dir)
    cat = base / "catalog"
    clone_repo(Config.catalog_repo, str(cat.resolve()), Config.catalog_ref)


def clone_repos() -> None:
    """
    Reads repository URLs from AddonCatalog.json and clones them into the ./repos directory.
    """
    clone_catalog()
    cat = Path(Config.base_dir) / "catalog" / Config.catalog_path
    data: dict[str, object] = json.loads(cat.read_text())

    repos = Path(Config.base_dir) / Config.repositories_dir
    if not repos.exists():
        repos.mkdir(parents=True)

    tasks: list[Thread] = []
    j_idx = 0
    for addon_name, addon_versions in data.items():
        if addon_name in Config.excluded_addons:
            continue
        if isinstance(addon_versions, list):
            for version in addon_versions:
                if "repository" in version:
                    repo_url = version["repository"]
                    repo_branch = version["git_ref"]
                    repo_suffix = version.get(
                        "branch_display_name", repo_branch
                    )
                    clone_path = repos / f"{addon_name}_{repo_suffix}"
                    thread = Thread(
                        target=clone_repo,
                        args=(repo_url, str(clone_path), repo_branch),
                    )
                    tasks.append(thread)
                    thread.start()
                    j_idx += 1
            if Config.max_repos > 0 and j_idx >= Config.max_repos:
                break

    for task in tasks:
        task.join()


def get_origin(repo: Path) -> str:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(repo),
    )
    return result.stdout.strip()


def get_branch(repo: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(repo),
    )
    return result.stdout.strip()


def get_tag(repo: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(repo),
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_updated(repo: Path) -> datetime:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ad", "--date=iso"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=True,
    )
    return datetime.strptime(result.stdout.strip(), "%Y-%m-%d %H:%M:%S %z")
