# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
General configuration.
"""

class _Config:
    matomo_stats_endpoint = "https://addons.freecad.org/stats/index.php"
    github_stats_endpoint = "https://www.freecad.org/addon_stats.json"

    # Old Catalog
    # catalog_repo = "https://github.com/FreeCAD/FreeCAD-addons"
    # catalog_ref = "master"
    # catalog_path = "AddonCatalog.json"

    catalog_repo = "https://github.com/FreeCAD/Addons"
    catalog_ref = "main"
    catalog_path = "Data/Index.json"

    excluded_addons = {
        "FreeCAD-Documentation-html",
        "offline-documentation",
        "parts_library",
    }

    repositories_dir = "repos"
    skip_clone: bool = False
    max_repos: int = -1
    base_dir = "."


Config = _Config()
