#!/usr/bin/env python3
""".github/scripts/sbom_generation_comparison.py - Report the SBOMs that sbom-generation.yml produced.

Used by .github/workflows/sbom-generation-comparison.yml
to download the SBOMs of one finished generation run
and write a plain-language report.

Commands:
  download   Download every output declared in .github/sbom-generators.toml.
             An output that is missing is reported, not treated as an error.
  report     Write comparison/summary.md, the evidence manifest, and the checksums.

The report reads one setting from .github/sbom-generators.toml:
  [report] purl_detail_max = N
  A group of 1 to N package URLs (PURLs) is listed in full with its records.

Runs locally with Python 3.11 or later.
"""

import hashlib
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import NamedTuple

import sbom_generate

OUT = Path("comparison").resolve()
LOGS = OUT / "logs"

FORMAT_NAME = {"cdx": "CycloneDX", "spdx": "SPDX"}
RECORD_KIND = {"cdx": "CycloneDX component", "spdx": "SPDX package"}
VERSION_KEY = {"cdx": "version", "spdx": "versionInfo"}
ID_KEY = {"cdx": "bom-ref", "spdx": "SPDXID"}
ID_LIMIT = 3  # Record identifiers shown per artifact before the rest are only counted.


class Record(NamedTuple):
    """What one component (CycloneDX) or package (SPDX) says about itself."""

    name: str
    version: str
    identifier: str


# ============================================================
# === A) DOWNLOAD: get each declared output from the generation run ===
# ============================================================


def download(outputs):
    for out in outputs:
        artifact = out["artifact"]
        with (
            tempfile.TemporaryDirectory() as temp,
            (LOGS / f"download-{artifact}.log").open("w") as log,
        ):
            result = subprocess.run(
                [
                    "gh",
                    "run",
                    "download",
                    os.environ["GENERATION_RUN_ID"],
                    "--name",
                    artifact,
                    "--dir",
                    temp,
                ],
                stdout=log,
                stderr=log,
                check=False,
            )
            files = [p for p in Path(temp).rglob("*") if p.is_file()]
            if result.returncode == 0 and len(files) == 1:
                shutil.copyfile(files[0], OUT / f"{artifact}.json")
            else:
                print(
                    f"Not downloaded: exit {result.returncode}, {len(files)} files",
                    file=log,
                )


# ============================================================
# === B) READ: turn each SBOM file into one row of facts ===
# ============================================================


def report_setting(name):
    """Return a value from the [report] table of the generators file."""
    with sbom_generate.CONFIG.open("rb") as handle:
        value = tomllib.load(handle).get("report", {}).get(name)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"{sbom_generate.CONFIG}: [report] {name} must be a whole number, 0 or more"
        )
    return value


def reported_tools(document, fmt):
    """Return the tool names and versions that the SBOM says produced it."""
    if fmt == "cdx":
        tools = document.get("metadata", {}).get("tools", [])
        items = tools if isinstance(tools, list) else tools.get("components", [])
        return [f"{item.get('name')} {item.get('version')}" for item in items]
    found = []
    for creator in document.get("creationInfo", {}).get("creators", []):
        if creator.startswith("Tool:"):
            tool = creator.removeprefix("Tool:").strip()
            name, _, version = tool.rpartition("-")
            found.append(
                f"{name} {version}" if name and version[:1].isdigit() else tool
            )
    return found


def make_record(item, fmt):
    return Record(
        name=str(item.get("name") or "unnamed"),
        version=str(item.get(VERSION_KEY[fmt]) or ""),
        identifier=str(item.get(ID_KEY[fmt]) or ""),
    )


def package_records(document, fmt):
    """Return (package record count, records by PURL). Files are not packages."""
    if fmt == "cdx":
        pending = list(document.get("components", []))
        root = document.get("metadata", {}).get("component")
        if root:
            pending.append(root)
        items = []
        while pending:
            component = pending.pop()
            pending.extend(component.get("components", []))
            if component.get("type") != "file":
                items.append(component)
        purls = lambda item: [item["purl"]] if item.get("purl") else []
    else:
        items = document.get("packages", [])
        purls = lambda item: [
            ref["referenceLocator"]
            for ref in item.get("externalRefs", [])
            if ref.get("referenceType") == "purl"
        ]

    by_purl = {}
    for item in items:
        for purl in purls(item):
            by_purl.setdefault(purl, []).append(make_record(item, fmt))
    return len(items), by_purl


def declared_version(gen):
    if gen["install"] == "node-builtin":
        return f"npm bundled with Node {gen['node']}"
    return gen["revision"]


def inspect_output(out, gen):
    """Describe one declared output from its downloaded file.

    row["found"] maps each PURL to the records that carry it.
    It is None when the file is missing or unreadable.
    """
    fmt = out["format"]
    shown = out["version"].removeprefix("SPDX-")
    row = {
        "artifact": out["artifact"],
        "generator": out["generator"],
        "format": fmt,
        "declared": declared_version(gen),
        "reported": "—",
        "output_format": f"{FORMAT_NAME[fmt]} {shown}",
        "packages": "—",
        "with_purl": "—",
        "found": None,
    }
    optional = "" if gen.get("required", True) else " (optional generator)"
    path = OUT / f"{out['artifact']}.json"
    if not path.is_file():
        row["status"] = "Not generated" + optional
        return row
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        version = document.get(sbom_generate.VERSION_FIELD[fmt])
        tools = reported_tools(document, fmt)
        count, found = package_records(document, fmt)
    except (ValueError, AttributeError, TypeError):
        row["status"] = "Unreadable file" + optional
        return row

    row["output_format"] = f"{FORMAT_NAME[fmt]} {str(version).removeprefix('SPDX-')}"
    row["reported"] = ", ".join(tools) or "not reported"
    row["packages"] = count
    row["with_purl"] = sum(len(records) for records in found.values())
    row["found"] = found
    if version != out["version"]:
        row["status"] = f"Format version differs from the declared {shown}" + optional
    elif gen["install"] == "github-release" and not any(
        tool.rsplit(" ", 1)[-1] == gen["revision"].removeprefix("v") for tool in tools
    ):
        row["status"] = "Generated; tool version differs from declared" + optional
    else:
        row["status"] = "Generated" + optional
    return row


# ============================================================
# === C) REPORT: write each section of the summary ===
# ============================================================


def cell(values):
    """Join distinct values for one table cell, or show a dash if there are none."""
    text = ", ".join(sorted({v for v in values if v}))
    return text.replace("|", "\\|") or "—"


def comparisons(rows):
    """Return (format, SBOM A, SBOM B) for every two generated SBOMs of one format."""
    pairs = []
    for fmt in FORMAT_NAME:
        ready = [r for r in rows if r["format"] == fmt and r["found"] is not None]
        pairs.extend((fmt, a, b) for a, b in itertools.combinations(ready, 2))
    return pairs


def introduction(source_run):
    return [
        "## SBOM generation report",
        "",
        (
            f"Source: [SBOM generation run {source_run['id']}]({source_run['html_url']}) "
            f"at `{source_run['head_sha']}`."
        ),
        "",
        (
            "An SBOM (software bill of materials) lists the packages found in a repository. "
            "Each row below is one SBOM file written by one generator in one format."
        ),
        "",
        "- **Generator**: the program that inspects the repository and writes the SBOM.",
        (
            "- **Generator version declared**: the version chosen in "
            "`.github/sbom-generators.toml`."
        ),
        (
            "- **Generator version in the SBOM**: the version that the SBOM file itself says "
            "made it."
        ),
        (
            "- **Output format**: the layout of the SBOM file, CycloneDX or SPDX, with its "
            "format version. One generator can write both."
        ),
        (
            "- **Package records**: the software packages listed in the SBOM, including the "
            "repository itself. CycloneDX calls them components and SPDX calls them packages. "
            "Files are not counted."
        ),
        (
            "- **Records with a PURL**: package records that carry a PURL (package URL). A PURL "
            "is a text identifier stored on a record, such as `pkg:npm/lodash@4.17.21`. It is "
            "not the component or package itself, and several records can carry the same PURL."
        ),
        (
            "- **Artifact**: the name of the downloadable file, written as the generator and a "
            "format code (`cdx` is CycloneDX, `spdx` is SPDX)."
        ),
        "",
    ]


def generator_table(rows):
    lines = [
        (
            "| Generator | Generator version declared | Generator version in the SBOM | "
            "Output format | Package records | Records with a PURL | Artifact | Status |"
        ),
        "|---|---|---|---|---:|---:|---|---|",
    ]
    lines.extend(
        f"| {row['generator']} | {row['declared']} | {row['reported']} | "
        f"{row['output_format']} | {row['packages']} | {row['with_purl']} | "
        f"{row['artifact']} | {row['status']} |"
        for row in rows
    )
    return lines


def overlap_table(rows):
    """Count the PURLs that two generators share or do not share, per output format."""
    lines = ["", "### Do the generators list the same package URLs?", ""]
    pairs = comparisons(rows)
    if not pairs:
        lines.append(
            "Fewer than two SBOMs of one format were generated, "
            "so there is nothing to compare."
        )
        return lines
    lines.extend(
        [
            (
                "| Output format | Generator A | Generator B | Distinct PURLs in A | "
                "Distinct PURLs in B | In both | Only in A | Only in B |"
            ),
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for fmt, a, b in pairs:
        in_a, in_b = set(a["found"]), set(b["found"])
        lines.append(
            f"| {FORMAT_NAME[fmt]} | {a['generator']} | {b['generator']} | "
            f"{len(in_a)} | {len(in_b)} | {len(in_a & in_b)} | "
            f"{len(in_a - in_b)} | {len(in_b - in_a)} |"
        )
    lines.extend(
        [
            "",
            (
                "This compares exact PURL text only. It does not show that two records "
                "describe the same package, and a difference can come from what each "
                "generator was configured to scan as well as from the generator itself."
            ),
            "",
            (
                "A generator may list the repository's own package as a record with a PURL, "
                "or describe the scanned directory and give it no PURL. "
                "That may account for one PURL that only some generators list."
                "For example, "
                "Trivy may describe the scanned directory and lockfile as records without a PURL."
                "It may not list the repository's own package, which npm and Syft list with a PURL."
            ),
        ]
    )
    return lines


def reasons_by_purl(rows, limit):
    """Return {PURL: {reason: [format names]}} for PURLs in small comparison groups.

    A comparison group is the PURLs found in both of two SBOMs, or in only one of them.
    A group with 1 to `limit` PURLs is small enough to list in full.
    """
    reasons = {}
    for fmt, a, b in comparisons(rows):
        in_a, in_b = set(a["found"]), set(b["found"])
        x, y = a["generator"], b["generator"]
        groups = {
            f"In both {x} and {y}": in_a & in_b,
            f"In {x} but not in {y}": in_a - in_b,
            f"In {y} but not in {x}": in_b - in_a,
        }
        for reason, purls in groups.items():
            if 1 <= len(purls) <= limit:
                for purl in purls:
                    formats = reasons.setdefault(purl, {}).setdefault(reason, [])
                    formats.append(FORMAT_NAME[fmt])
    return reasons


def identifier_cell(records):
    ids = sorted(r.identifier for r in records if r.identifier)
    shown = [f"`{ident}`" for ident in ids[:ID_LIMIT]]
    if len(ids) > ID_LIMIT:
        shown.append(f"and {len(ids) - ID_LIMIT} more")
    return "<br>".join(shown) or "—"


def purl_tables(rows, limit):
    """Show each PURL from a small group once, with every SBOM that does or does not carry it."""
    lines = [
        "",
        "### Which package URLs explain the differences?",
        "",
        (
            f"A group of 1 to {limit} distinct PURLs is listed here in full. "
            "Larger groups are counted only. "
            "Each PURL appears once, followed by every SBOM and the record, if any, "
            "that carries it. A record is a component (CycloneDX) or a package (SPDX)."
        ),
    ]
    reasons = reasons_by_purl(rows, limit)
    if not reasons:
        lines.extend(["", "No group was small enough to list."])
        return lines

    for purl in sorted(reasons):
        lines.extend(["", f"#### `{purl}`", "", "Listed because it is:", ""])
        for reason, formats in reasons[purl].items():
            lines.append(f"- {reason} ({', '.join(formats)})")
        lines.extend(
            [
                "",
                (
                    "| Artifact | Where the PURL appears | Name recorded | Version recorded | "
                    "Records | Record identifier (`bom-ref` in CycloneDX, `SPDXID` in SPDX) |"
                ),
                "|---|---|---|---|---:|---|",
            ]
        )
        for row in rows:
            records = (row["found"] or {}).get(purl, [])
            if row["found"] is None:
                where = "SBOM not generated"
            elif records:
                where = RECORD_KIND[row["format"]]
            else:
                where = "No record carries this PURL"
            lines.append(
                f"| {row['artifact']} | {where} | {cell(r.name for r in records)} | "
                f"{cell(r.version for r in records)} | {len(records) or '—'} | "
                f"{identifier_cell(records)} |"
            )

    lines.extend(
        [
            "",
            (
                "To find a record, open the SBOM file named in the Artifact column "
                "(the downloadable artifact holds `<artifact>.json`) and search for the "
                "PURL text or for a record identifier."
            ),
        ]
    )
    return lines


def missing_section(rows):
    missing = [
        r["artifact"]
        for r in rows
        if r["status"].startswith(("Not generated", "Unreadable"))
    ]
    if not missing:
        return []
    return ["", "### Not available", "", *(f"- {name}" for name in missing)]


def write_evidence(outputs):
    """Keep the generators file and a checksum for every SBOM that was compared."""
    shutil.copyfile(sbom_generate.CONFIG, OUT / sbom_generate.CONFIG.name)
    with (OUT / "SHA256SUMS").open("w") as manifest:
        for out in sorted(outputs, key=lambda item: item["artifact"]):
            path = OUT / f"{out['artifact']}.json"
            if path.is_file():
                print(
                    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}",
                    file=manifest,
                )


def report(generators, outputs):
    limit = report_setting("purl_detail_max")
    rows = [
        inspect_output(out, generators[out["generator"]])
        for out in sorted(outputs, key=lambda item: item["artifact"])
    ]
    source_run = json.loads((OUT / "source-run.json").read_bytes())

    lines = introduction(source_run)
    lines += generator_table(rows)
    lines += overlap_table(rows)
    lines += purl_tables(rows, limit)
    lines += missing_section(rows)

    # WHY: A maintainer's interpretation applies to one generation run.
    #      The source run ID associates the note with the artifacts it describes.
    note_path = (
        Path(".github/notes/sbom-generation-comparison") / f"{source_run['id']}.md"
    )
    if note_path.is_file():
        lines.extend(
            [
                "",
                "<details>",
                "<summary>Maintainer's interpretation of this generation run</summary>",
                "",
                note_path.read_text(encoding="utf-8").strip(),
                "",
                "</details>",
            ]
        )

    (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_evidence(outputs)


def main(argv):
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        generators, _, outputs = sbom_generate.config()
        if argv == ["download"]:
            download(outputs)
        elif argv == ["report"]:
            report(generators, outputs)
        else:
            print(__doc__)
            return 2
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"::error::{error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
