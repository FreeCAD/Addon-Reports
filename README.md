# FreeCAD Addon Analyzer

Static quality analysis tool for all registered [FreeCAD](https://www.freecad.org/) addons. It clones every addon from the official catalog, runs a battery of checks, and produces a ranked HTML report.

## Reports

A fresh report is generated automatically on the **1st of each month** via GitHub Actions and published as a [GitHub Release](../../releases/latest). You can also trigger a report manually from the Actions tab.

## What gets checked

| Check | Description |
|---|---|
| **Bandit** | Python security-oriented static analysis |
| **Dependencies** | Python package requirements extracted with pipreqs |
| **package.xml** | Validates presence and content of the addon metadata file |
| **Layout** | Verifies required files (`README`, `LICENSE`, `package.xml`) and init-module conventions |
| **GitHub stats** | Stars, forks, subscribers, open issues |
| **Matomo stats** | Download counts from the FreeCAD Addon Manager |

## Scoring

Every addon starts at **100 points** and loses points for each issue found:

| Severity | Penalty |
|---|---|
| HIGH | **−3** per issue |
| MEDIUM | **−1** per issue |
| LOW | **−0.1** per issue |

The final score is clamped to a minimum of **0**. Addons are ranked by score (descending), then by downloads.

## Running locally

**Requirements:** Python ≥ 3.11, [uv](https://github.com/astral-sh/uv), and git.

```bash
# Full run — clones all addons and generates the report
uv run analyze

# Skip cloning, reuse already cloned repos
uv run analyze --skip-clone

# Analyze only the first N addons (useful for debugging)
uv run analyze --max 10
```

The report is written to the `output/` directory as a standalone HTML file (styled with [Tabler](https://tabler.io/) via CDN).

## Contributing

- PRs that follow **PEP 8** and maintain good code quality are welcome.
- AI-generated slop is generally not accepted.
