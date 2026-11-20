#!/usr/bin/env python3
""".github/scripts/sbom_generation_comparison.py - Report the SBOMs that sbom-generation.yml produced.

Used by .github/workflows/sbom-generation-comparison.yml
to download the SBOMs of one finished generation run
and write a plain-language report.

Commands:
  download   Download every output declared in .github/sbom-generators.toml.
             An output that is missing is reported, not treated as an error.
  report     Write comparison/summary.md, the evidence manifest, and the checksums.

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
from pathlib import Path

import sbom_generate

OUT = Path("comparison").resolve()
LOGS = OUT / "logs"
FORMAT_NAME = {"cdx": "CycloneDX", "spdx": "SPDX"}


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


def package_records(document, fmt):
    """Return (package record count, sorted distinct PURLs). Files are not packages."""
    if fmt == "cdx":
        pending = list(document.get("components", []))
        root = document.get("metadata", {}).get("component")
        if root:
            pending.append(root)
        records = []
        while pending:
            component = pending.pop()
            pending.extend(component.get("components", []))
            if component.get("type") != "file":
                records.append(component)
        purls = [c["purl"] for c in records if c.get("purl")]
    else:
        records = document.get("packages", [])
        purls = [
            ref["referenceLocator"]
            for p in records
            for ref in p.get("externalRefs", [])
            if ref.get("referenceType") == "purl"
        ]
    return len(records), purls


def declared_version(gen):
    if gen["install"] == "node-builtin":
        return f"npm bundled with Node {gen['node']}"
    return gen["revision"]


def inspect_output(out, gen):
    """Describe one declared output from its downloaded file."""
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
        "purls": None,
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
        count, purls = package_records(document, fmt)
    except (ValueError, AttributeError, TypeError):
        row["status"] = "Unreadable file" + optional
        return row

    row["output_format"] = f"{FORMAT_NAME[fmt]} {str(version).removeprefix('SPDX-')}"
    row["reported"] = ", ".join(tools) or "not reported"
    row["packages"], row["with_purl"], row["purls"] = count, len(purls), set(purls)
    if version != out["version"]:
        row["status"] = f"Format version differs from the declared {shown}" + optional
    elif gen["install"] == "github-release" and not any(
        tool.rsplit(" ", 1)[-1] == gen["revision"].removeprefix("v") for tool in tools
    ):
        row["status"] = "Generated; tool version differs from declared" + optional
    else:
        row["status"] = "Generated" + optional
    return row


def report(generators, outputs):
    rows = [
        inspect_output(out, generators[out["generator"]])
        for out in sorted(outputs, key=lambda item: item["artifact"])
    ]
    source_run = json.loads((OUT / "source-run.json").read_bytes())
    lines = [
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
        (
            "| Generator | Generator version declared | Generator version in the SBOM | "
            "Output format | Package records | Records with a PURL | Artifact | Status |"
        ),
        "|---|---|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['generator']} | {row['declared']} | {row['reported']} | "
            f"{row['output_format']} | {row['packages']} | {row['with_purl']} | "
            f"{row['artifact']} | {row['status']} |"
        )

    lines.extend(["", "### Do the generators list the same package URLs?", ""])
    pair_rows = []
    for fmt, format_name in FORMAT_NAME.items():
        ready = [r for r in rows if r["format"] == fmt and r["purls"] is not None]
        for a, b in itertools.combinations(ready, 2):
            pair_rows.append(
                f"| {format_name} | {a['generator']} | {b['generator']} | "
                f"{len(a['purls'])} | {len(b['purls'])} | {len(a['purls'] & b['purls'])} | "
                f"{len(a['purls'] - b['purls'])} | {len(b['purls'] - a['purls'])} |"
            )
    if pair_rows:
        lines.extend(
            [
                (
                    "| Output format | Generator A | Generator B | Distinct PURLs in A | "
                    "Distinct PURLs in B | In both | Only in A | Only in B |"
                ),
                "|---|---|---|---:|---:|---:|---:|---:|",
                *pair_rows,
                "",
                (
                    "This compares exact PURL text only. It does not show that two records "
                    "describe the same package, and a difference can come from what each "
                    "generator was configured to scan as well as from the generator itself."
                ),
            ]
        )
    else:
        lines.append(
            "Fewer than two SBOMs of one format were generated, so there is "
            "nothing to compare."
        )

    missing = [
        r["artifact"]
        for r in rows
        if r["status"].startswith(("Not generated", "Unreadable"))
    ]
    if missing:
        lines.extend(["", "### Not available", ""])
        lines.extend(f"- {name}" for name in missing)

    (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    shutil.copyfile(sbom_generate.CONFIG, OUT / sbom_generate.CONFIG.name)
    with (OUT / "SHA256SUMS").open("w") as manifest:
        for out in sorted(outputs, key=lambda item: item["artifact"]):
            path = OUT / f"{out['artifact']}.json"
            if path.is_file():
                print(
                    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}",
                    file=manifest,
                )


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
