#!/usr/bin/env python3

from config import Config
import typer
from typing import Annotated


def main(
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
    max: Annotated[int, typer.Option(help="Maximum number of repos to analyze (for debugging)")] = -1,
):
    if repositories:
        Config.repositories_dir = repositories
    Config.skip_clone = skip_clone
    Config.max_repos = max

    import pipeline

    pipeline.start()


if __name__ == "__main__":
    typer.run(main)
