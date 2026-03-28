#!/usr/bin/env python3

from __future__ import annotations

from typing import Annotated

import typer

from .config import Config


def entry(
    repositories: Annotated[
        str,
        typer.Argument(
            help="Directory name where addons are cloned (relative path)",
        ),
    ] = "repos",
    skip_clone: Annotated[
        bool,
        typer.Option(help="Do not clone/sync repositories, use local state."),
    ] = False,
    max: Annotated[
        int,
        typer.Option(help="Maximum number of repos to analyze (for debugging)"),
    ] = -1,
):
    if repositories:
        Config.repositories_dir = repositories

    Config.skip_clone = skip_clone
    Config.max_repos = max

    from . import pipeline

    pipeline.start()


def main():
    typer.run(entry)


if __name__ == "__main__":
    main()
