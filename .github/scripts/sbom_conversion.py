""".github/scripts/sbom_conversion.py - Inspect configured SBOM conversion routes and record PURL correspondence.

Used by .github/workflows/sbom-conversion.yml
to download original SBOM artifacts,
prepare converters, and inspect conversion routes.

Runs locally with Python 3.11 or later.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from collections import Counter, defaultdict
from pathlib import Path

CONFIG = Path(".github")
OUT = Path("inspection").resolve()
LOGS = OUT / "logs"
ROUTES_FILE = CONFIG / "sbom-routes.toml"
POLICIES_FILE = CONFIG / "sbom-correspondence.toml"

OUTCOMES = (
    "preserved",
    "changed",
    "missing_source_evidence",
    "no_target_match",
    "ambiguous",
)


class ConverterFailure(Exception):
    """A converter could not be prepared, could not run, or wrote an unusable SBOM.

    This is a recorded outcome for the route, not an inspection error.
    """


def config(path):
    with path.open("rb") as stream:
        return tomllib.load(stream)


def read_document(path, fmt, expected):
    doc = json.loads(path.read_bytes())
    actual = doc.get("specVersion") if fmt == "cdx" else doc.get("spdxVersion")
    if fmt == "cdx" and doc.get("bomFormat") != "CycloneDX":
        raise ValueError(f"{path.name}: expected CycloneDX")
    if actual != expected:
        raise ValueError(f"{path.name}: expected {expected}, received {actual!r}")
    return doc


def original(fmt):
    return OUT / f"sbom.{fmt}.original.json"


def download(routes):
    for fmt, source in routes["source"].items():
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run(
                ["gh", "run", "download", os.environ["SBOM_RUN_ID"],
                 "--name", source["artifact"], "--dir", temp],
                check=True,
            )
            files = [p for p in Path(temp).rglob("*") if p.is_file()]
            if len(files) != 1:
                raise ValueError(f"{source['artifact']}: expected one file, found {len(files)}")
            read_document(files[0], fmt, source["version"])
            shutil.copyfile(files[0], original(fmt))


def prepare(tool, revision, work, log):
    """Prepare one converter. Both directions reuse the same executable."""
    folder = work / tool
    folder.mkdir()

    def run(*args, cwd=folder):
        subprocess.run(args, cwd=cwd, stdout=log, stderr=log, check=True)

    if tool == "cyclonedx-cli":
        binary = folder / "cyclonedx-linux-x64"
        url = f"https://github.com/CycloneDX/cyclonedx-cli/releases/download/{revision}"
        run("curl", "-fsSL", "--retry", "3", "-o", binary, f"{url}/{binary.name}")
        binary.chmod(0o755)
        return [str(binary)]

    if tool == "syft":
        archive = f"syft_{revision.removeprefix('v')}_linux_amd64.tar.gz"
        url = f"https://github.com/anchore/syft/releases/download/{revision}/{archive}"
        run("curl", "-fsSL", "--retry", "3", "-o", folder / archive, url)
        binary = folder / "syft"
        with tarfile.open(folder / archive) as bundle:
            member = next(
                m for m in bundle.getmembers()
                if m.isfile() and Path(m.name).name == "syft"
            )
            src = bundle.extractfile(member)
            if src is None:
                raise ValueError(f"Cannot read {member.name!r} from {archive}")
            with src, binary.open("wb") as dst:
                shutil.copyfileobj(src, dst)
        binary.chmod(0o755)
        return [str(binary)]

    repos = {"cdx2spdx": "spdx/cdx2spdx", "protobom": "protobom/sbom-convert"}
    run("git", "init", "-q")
    run("git", "fetch", "--depth=1", f"https://github.com/{repos[tool]}.git", revision)
    run("git", "checkout", "--detach", "FETCH_HEAD")
    run("git", "rev-parse", "HEAD")

    if tool == "protobom":
        binary = folder / "sbom-convert"
        run("go", "build", "-o", binary, ".")
        return [str(binary)]

    run("git", "submodule", "update", "--init", "--recursive", "--depth=1")
    run("mvn", "-B", "-DskipTests", "package")
    jars = list((folder / "target").glob("*-jar-with-dependencies.jar"))
    if len(jars) != 1:
        raise ValueError(f"Expected one cdx2spdx executable JAR, found {len(jars)}")
    return ["java", "-jar", str(jars[0])]


def ecosystem(record, fmt, rules):
    values = set()
    for rule in rules:
        if rule["format"] != fmt:
            continue
        if "property" in rule:
            matches = any(
                p.get("name") == rule["property"] and p.get("value") == rule["equals"]
                for p in record.get("properties", [])
            )
        else:
            matches = record.get(rule["field"], "").startswith(rule["starts_with"])
        if matches:
            values.add(rule["ecosystem"])
    return next(iter(values)) if len(values) == 1 else None


def cdx_components(doc):
    """Include the described component and nested inventory components."""
    pending = list(doc.get("components", []))
    root = doc.get("metadata", {}).get("component")
    if root:
        pending.append(root)
    while pending:
        component = pending.pop()
        pending.extend(component.get("components", []))
        if component.get("type") != "file":
            yield component


def records(doc, fmt, rules):
    result = []
    items = cdx_components(doc) if fmt == "cdx" else doc.get("packages", [])
    for index, item in enumerate(items):
        if fmt == "cdx":
            identifier = item.get("bom-ref")
            purls = {item["purl"]} if item.get("purl") else set()
            hashes = [(h["alg"], h["content"]) for h in item.get("hashes", [])]
            version = item.get("version")
        else:
            identifier = item.get("SPDXID")
            purls = {
                ref["referenceLocator"] for ref in item.get("externalRefs", [])
                if ref.get("referenceCategory") == "PACKAGE-MANAGER"
                and ref.get("referenceType") == "purl"
            }
            hashes = [
                (h["algorithm"], h["checksumValue"]) for h in item.get("checksums", [])
            ]
            version = item.get("versionInfo")
        result.append({
            "id": identifier or f"{fmt}-record-{index}",
            "name": item.get("name"),
            "version": version,
            "ecosystem": ecosystem(item, fmt, rules),
            "purls": purls,
            "hashes": hashes,
        })
    return result


def keys(record, policy):
    if policy["method"] == "exact-fields":
        key = tuple(record[field] for field in policy["fields"])
        return {key} if all(v and v not in {"NONE", "NOASSERTION"} for v in key) else set()

    if policy["method"] != "shared-package-digest":
        raise ValueError(f"Unknown correspondence method: {policy['method']}")

    lengths = {"SHA1": 40, "SHA256": 64, "SHA512": 128}
    admitted = {alg.replace("-", "").upper() for alg in policy["algorithms"]}
    result = set()
    for algorithm, digest in record["hashes"]:
        alg = algorithm.replace("-", "").upper()
        if alg in admitted and re.fullmatch(rf"[0-9a-fA-F]{{{lengths[alg]}}}", digest):
            result.add((alg, digest.lower()))
    return result


def evaluate(source, target, policy):
    """Authorize one-to-one matches before consulting either PURL set."""
    target_index = defaultdict(set)
    for j, record in enumerate(target):
        for key in keys(record, policy):
            target_index[key].add(j)

    candidates = []
    claims = Counter()
    for record in source:
        evidence = keys(record, policy)
        matches = set()
        for key in evidence:
            matches.update(target_index.get(key, ()))
        candidates.append((evidence, matches))
        # WHY: Even a source without a PURL can compete for the same target.
        claims.update(matches)

    details = []
    for record, (evidence, matches) in zip(source, candidates, strict=True):
        if not record["purls"]:
            continue
        target_purls = None
        if not evidence:
            outcome = "missing_source_evidence"
        elif not matches:
            outcome = "no_target_match"
        elif len(matches) > 1 or claims[next(iter(matches))] > 1:
            outcome = "ambiguous"
        else:
            target_purls = target[next(iter(matches))]["purls"]
            outcome = "preserved" if record["purls"] == target_purls else "changed"

        details.append({
            "source_record": record["id"],
            "candidate_targets": [target[j]["id"] for j in sorted(matches)],
            "source_purls": sorted(record["purls"]),
            "target_purls": sorted(target_purls) if target_purls is not None else None,
            "outcome": outcome,
        })
    return details


def unevaluated(label, policies, status):
    return [
        f"| {label} | {policy['id']} | — | — | — | — | — | {status} |"
        for policy in policies["policy"]
    ]


def inspect(routes, policies):
    sources = {}
    for fmt, spec in routes["source"].items():
        doc = read_document(original(fmt), fmt, spec["version"])
        sources[fmt] = records(doc, fmt, policies.get("ecosystem_rule", []))

    source_run = json.loads((OUT / "source-run.json").read_bytes())
    report = [
        "## SBOM conversion inspection",
        "",
        (
            f"Source: [SBOM run {source_run['id']}]({source_run['html_url']}) "
            f"at `{source_run['head_sha']}`."
        ),
        "",
        (
            "| Route | Policy | Preserved | Changed | Missing source evidence | "
            "No target match | Ambiguous | Status |"
        ),
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    evidence = []
    failures = []  # converter outcomes: reported, but do not affect the exit code
    inspection_errors = []  # config, evaluator, or output-writing faults
    completed = 0
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        commands = {}
        for tool, spec in routes["tool"].items():
            with (LOGS / f"prepare-{tool}.log").open("w") as log:
                try:
                    commands[tool] = prepare(tool, spec["revision"], work, log)
                except (OSError, ValueError, subprocess.SubprocessError, StopIteration) as exc:
                    print(f"Preparation failed: {exc}", file=log)

        for route in routes["route"]:
            src, dst, tool = (route[k] for k in ("source", "target", "tool"))
            label = f"{src} → {dst} ({tool})"
            stem = f"sbom.{src}.to.{dst}.{tool}"
            output = OUT / f"{stem}.json"
            pending = work / f"{stem}.json"
            try:
                args = [
                    arg.format(input=original(src), output=pending)
                    for arg in route["args"]
                ]
                expected = routes["source"][dst]["version"]
                try:
                    if tool not in commands:
                        raise ValueError(f"Tool setup failed; see logs/prepare-{tool}.log")
                    with (LOGS / f"{stem}.log").open("wb") as log:
                        if route.get("stdout"):
                            with pending.open("wb") as stream:
                                subprocess.run(commands[tool] + args, stdout=stream,
                                               stderr=log, check=True, timeout=180)
                        else:
                            subprocess.run(commands[tool] + args, stdout=log,
                                           stderr=log, check=True, timeout=180)
                    doc = read_document(pending, dst, expected)
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    raise ConverterFailure(str(exc)) from exc
                target = records(doc, dst, policies.get("ecosystem_rule", []))
                rows = []
                for policy in policies["policy"]:
                    details = evaluate(sources[src], target, policy)
                    counts = Counter(row["outcome"] for row in details)
                    cells = " | ".join(str(counts[k]) for k in OUTCOMES)
                    rows.append((
                        f"| {label} | {policy['id']} | {cells} | Evaluated |",
                        {"route": stem, "policy": policy["id"], "records": details},
                    ))
                shutil.copyfile(pending, output)
                for line, detail in rows:
                    report.append(line)
                    evidence.append(detail)
                completed += 1
            except ConverterFailure as exc:
                failures.append(f"{label}: {exc}")
                report.extend(unevaluated(label, policies, "Converter failed"))
            except (OSError, ValueError, KeyError, IndexError) as exc:
                inspection_errors.append(f"{label}: {type(exc).__name__}: {exc}")
                report.extend(unevaluated(label, policies, "Inspection error"))

    report.extend([
        "",
        (
            f"**{completed}/{len(routes['route'])} routes completed. "
            f"{len(evidence)} route-policy evaluations completed.**"
        ),
        "",
        (
            "Counts represent source package records carrying a PURL. "
            "A dash indicates that evaluation could not run."
        ),
    ])
    if failures:
        report.extend(["", "### Converter failures", ""])
        report.extend(f"- {message}" for message in failures)
    if inspection_errors:
        report.extend(["", "### Inspection errors", ""])
        report.extend(f"- {message}" for message in inspection_errors)

    (OUT / "summary.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "records.json").write_text(json.dumps(evidence, indent=2) + "\n")
    for path in (ROUTES_FILE, POLICIES_FILE):
        shutil.copyfile(path, OUT / path.name)
    with (OUT / "SHA256SUMS").open("w") as manifest:
        for path in sorted(OUT.glob("sbom.*.json")):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            print(f"{digest}  {path.name}", file=manifest)
    # Converter failures are recorded evidence. Only inspection errors fail the run.
    return int(bool(inspection_errors))


if __name__ == "__main__":
    LOGS.mkdir(parents=True, exist_ok=True)
    routes = config(ROUTES_FILE)
    if sys.argv[1:] == ["download"]:
        download(routes)
    elif sys.argv[1:] == ["inspect"]:
        sys.exit(inspect(routes, config(POLICIES_FILE)))
    else:
        sys.exit("Usage: sbom_conversion.py download|inspect")
