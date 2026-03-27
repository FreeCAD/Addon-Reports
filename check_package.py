# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2026 Frank David Martínez Muñoz <mnesarco>
# SPDX-FileNotice: Part of FreeCAD.

"""
Static analysis of package.xml data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lxml import etree  # type: ignore

from models import Analysis, Issue

SCHEMA = "https://wiki.freecad.org/Package_Metadata"


@dataclass
class Meta:
    branch: str = ""
    version: str = ""
    license: str = ""
    description: str = ""


def _xpath(doc, query: str, namespaces: dict[str, str] | None = None):
    if not namespaces:
        return doc.xpath(query)
    for prefix, ns in namespaces.items():
        result = doc.xpath(
            query.replace("%:", f"{prefix}:"), namespaces=namespaces
        )
        if result:
            return result
    return doc.xpath(query.replace("%:", ""), namespaces=namespaces)


def _check_repository(
    package,
    name: str,
    issues: list[Issue],
    repo: Path,
) -> str:
    namespaces = {"fcp": SCHEMA}
    repository = _xpath(
        package, "/%:package/%:url[@type='repository']", namespaces=namespaces
    )
    if not repository:
        issues.append(
            Issue(
                name,
                0,
                """Missing repository information (&lt;url type="repository"&gt;...&lt;url&gt;)""",
            )
        )
        return ""
    else:
        branch = ""
        for url in repository:
            branch = url.get("branch")
            if not url.get("branch"):
                print(str(repo), dir(url))
                issues.append(
                    Issue(
                        name,
                        0,
                        """Missing repository branch information (&lt;url type="repository" branch="..."&gt;...&lt;url&gt;)""",
                    )
                )
        return branch or ""


def _check_license(package, name: str, issues: list[Issue], repo: Path) -> str:
    namespaces = {"fcp": SCHEMA}
    licenses = _xpath(package, "/%:package/%:license", namespaces=namespaces)
    content = []
    for lic in licenses:
        content.append(lic.text)
        file = str(lic.get("file"))
        if not (repo / file).exists():
            issues.append(
                Issue(
                    name,
                    lic.sourceline,
                    f"""Missing license file '{file}'""",
                )
            )
    return ", ".join(content)


def _check_version(package, name: str, issues: list[Issue], repo: Path) -> str:
    namespaces = {"fcp": SCHEMA}
    version = _xpath(package, "/%:package/%:version", namespaces=namespaces)
    if not version:
        issues.append(
            Issue(
                name,
                0,
                """Missing version information in package.xml""",
            )
        )
        return ""
    return version[0].text


def _check_people(
    package, name: str, issues: list[Issue], repo: Path
) -> list[str]:
    namespaces = {"fcp": SCHEMA}
    people = []

    authors = _xpath(package, "/%:package/%:author", namespaces=namespaces)
    if not authors:
        issues.append(
            Issue(
                name,
                0,
                """Missing author information in package.xml""",
            )
        )
    else:
        people = [e.text for e in authors]

    maintainers = _xpath(
        package, "/%:package/%:maintainer", namespaces=namespaces
    )
    if not maintainers:
        issues.append(
            Issue(
                name,
                0,
                """Missing maintainers information in package.xml""",
            )
        )
    else:
        people.extend([e.text for e in maintainers])

    return list(set(map(str.strip, people)))


def _check_description(
    package,
    name: str,
    issues: list[Issue],
    repo: Path,
) -> str:
    namespaces = {"fcp": SCHEMA}
    descr = _xpath(package, "/%:package/%:description", namespaces=namespaces)
    if not descr:
        issues.append(
            Issue(
                name,
                0,
                """Missing description information in package.xml""",
            )
        )
        return ""
    return descr[0].text


def _check_schema(package, name: str, issues: list[Issue], repo: Path) -> None:
    schema_xml = Path(__file__).parent / "package-schema.rng.xml"
    schema = etree.RelaxNG(etree.XML(schema_xml.read_bytes()))
    if not schema.validate(package):
        for e in schema.error_log:
            issues.append(Issue(name, e.line, e.message))


def check_package(analysis: Analysis, repo: Path) -> Meta:
    package_xml = repo / "package.xml"
    if not package_xml.exists():
        return Meta()

    issues = analysis.issues["HIGH"]
    package = etree.XML(package_xml.read_bytes())

    _check_schema(
        package,
        package_xml.name,
        issues,
        repo,
    )

    branch = _check_repository(
        package,
        package_xml.name,
        issues,
        repo,
    )

    license = _check_license(
        package,
        package_xml.name,
        issues,
        repo,
    )

    version = _check_version(
        package,
        package_xml.name,
        issues,
        repo,
    )

    description = _check_description(
        package,
        package_xml.name,
        issues,
        repo,
    )

    people = _check_people(
        package,
        package_xml.name,
        analysis.issues["INFO"],
        repo,
    )

    analysis.pkg_branch = branch
    analysis.pkg_license = license
    analysis.pkg_version = version
    analysis.pkg_description = description
    analysis.pkg_people = people

    if analysis.git_ref != analysis.pkg_branch:
        issues.append(
            Issue(
                package_xml.name,
                0,
                f"Declared branch '{analysis.pkg_branch}' does not match git branch '{analysis.git_ref}'",
            )
        )

    return Meta(
        branch=branch, license=license, version=version, description=description
    )
