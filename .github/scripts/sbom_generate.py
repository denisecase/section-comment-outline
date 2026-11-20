#!/usr/bin/env python3
""".github/scripts/sbom_generate.py - Generate the original SBOMs declared in .github/sbom-generators.toml.

Commands:
  plan            Print the job matrix: one entry per declared output.
  generate NAME   Install the generator that produces artifact NAME, write the
                  SBOM to generated/NAME.json, and check its document version.

REQ: Every package, version, command, signature rule, and artifact name
     comes from the TOML file.
WHY: The generator is a variable of the experiment, so it is declared as data.
"""

import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from pathlib import Path

CONFIG = Path(".github/sbom-generators.toml")
OUT = Path("generated")
VERSION_FIELD = {"cdx": "specVersion", "spdx": "spdxVersion"}
INSTALL_KEYS = {
    "github-release": ("package", "revision", "asset"),
    "node-builtin": ("node",),
}
VERIFY_KEYS = ("verifier", "signed", "bundle", "certificate_identity", "certificate_oidc_issuer")


def config(path=CONFIG):
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    generators = data.get("generator", {})
    verifiers = data.get("verifier", {})
    outputs = data.get("output", [])
    if not generators or not outputs:
        raise ValueError(f"{path}: declare at least one generator and one output")

    for name, spec in verifiers.items():
        missing = [k for k in ("package", "revision", "asset", "sha256") if k not in spec]
        if spec.get("archive", True) and "binary" not in spec:
            missing.append("binary")
        if missing:
            raise ValueError(f"verifier.{name}: missing {', '.join(missing)}")

    for name, gen in generators.items():
        kind = gen.get("install")
        if kind not in INSTALL_KEYS:
            raise ValueError(f"generator.{name}: install must be one of {sorted(INSTALL_KEYS)}")
        missing = [key for key in INSTALL_KEYS[kind] if key not in gen]
        if kind == "github-release" and "binary" not in gen:
            missing.append("binary")
        if missing:
            raise ValueError(f"generator.{name}: missing {', '.join(missing)}")
        if "verify" in gen:
            if kind != "github-release":
                raise ValueError(f"generator.{name}: verify applies only to github-release")
            missing = [key for key in VERIFY_KEYS if key not in gen["verify"]]
            if missing:
                raise ValueError(f"generator.{name}.verify: missing {', '.join(missing)}")
            if gen["verify"]["verifier"] not in verifiers:
                raise ValueError(
                    f"generator.{name}.verify: unknown verifier {gen['verify']['verifier']!r}"
                )

    seen = set()
    for out in outputs:
        label = out.get("artifact", "?")
        if out.get("generator") not in generators:
            raise ValueError(f"output {label}: unknown generator {out.get('generator')!r}")
        if out.get("format") not in VERSION_FIELD:
            raise ValueError(f"output {label}: format must be one of {sorted(VERSION_FIELD)}")
        if label != f"{out['generator']}.{out['format']}":
            raise ValueError(f"output {label}: artifact must be {out['generator']}.{out['format']}")
        if label in seen:
            raise ValueError(f"output {label}: declared twice")
        seen.add(label)
        if not out.get("version") or not out.get("args"):
            raise ValueError(f"output {label}: version and args are required")
    return generators, verifiers, outputs


def plan():
    generators, _, outputs = config()
    include = [
        {
            "artifact": out["artifact"],
            "generator": out["generator"],
            "format": out["format"],
            "required": bool(generators[out["generator"]].get("required", True)),
            "node": str(generators[out["generator"]].get("node", "")),
        }
        for out in sorted(outputs, key=lambda item: item["artifact"])
    ]
    line = json.dumps({"include": include}, separators=(",", ":"))
    print(line)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            handle.write(f"matrix={line}\n")


def fill(text, spec, asset=""):
    """Substitute {version}, {revision}, and {asset} in a declared string."""
    return text.format(
        version=spec["revision"].removeprefix("v"), revision=spec["revision"], asset=asset
    )


def download(spec, asset, folder):
    """Download one asset of the declared release."""
    path = folder / asset
    url = f"https://github.com/{spec['package']}/releases/download/{spec['revision']}/{asset}"
    subprocess.run(["curl", "-fsSL", "--retry", "3", "-o", str(path), url], check=True)
    return path


def fetch(label, spec, asset, folder):
    """Download one release asset. Check its pinned sha256 when one is declared."""
    path = download(spec, asset, folder)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if "sha256" not in spec:
        print(f"::warning::{label} declares no sha256. Computed {digest}")
    elif digest != spec["sha256"]:
        raise ValueError(f"{asset}: expected sha256 {spec['sha256']}, received {digest}")
    return path, digest


def executable(spec, archive, folder):
    """Return the runnable file: the asset itself, or the binary inside its archive."""
    if not spec.get("archive", True):
        archive.chmod(0o755)
        return archive
    binary = folder / spec["binary"]
    with tarfile.open(archive) as bundle:
        member = next(
            (m for m in bundle.getmembers()
             if m.isfile() and Path(m.name).name == spec["binary"]),
            None,
        )
        if member is None:
            raise ValueError(f"{archive.name}: no file named {spec['binary']!r}")
        source = bundle.extractfile(member)
        if source is None:
            raise ValueError(f"{archive.name}: cannot read {member.name!r}")
        with source, binary.open("wb") as target:
            target.write(source.read())
    binary.chmod(0o755)
    return binary


def listed_digest(text, asset):
    """Return the sha256 that a checksums file lists for one asset, or None."""
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip("*") == asset:
            return parts[0]
    return None


def verify_signature(name, gen, verifiers, asset, digest, folder):
    """Check the release signature of a downloaded asset before it is executed."""
    rule = gen["verify"]
    spec = verifiers[rule["verifier"]]
    archive, _ = fetch(f"verifier.{rule['verifier']}", spec, fill(spec["asset"], spec), folder)
    cosign = executable(spec, archive, folder)

    signed_name = fill(rule["signed"], gen, asset)
    signed = folder / asset if signed_name == asset else download(gen, signed_name, folder)
    bundle = download(gen, fill(rule["bundle"], gen, asset), folder)

    subprocess.run(
        [str(cosign), "verify-blob", str(signed), "--bundle", str(bundle),
         "--certificate-identity", fill(rule["certificate_identity"], gen, asset),
         "--certificate-oidc-issuer", rule["certificate_oidc_issuer"]],
        check=True,
    )
    if signed_name != asset:
        listed = listed_digest(signed.read_text(encoding="utf-8"), asset)
        if listed != digest:
            raise ValueError(f"{signed_name}: lists sha256 {listed!r} for {asset}, received {digest}")
    print(f"generator.{name}: signature verified for {signed_name}")


def install(name, gen, verifiers, folder):
    """Return the command prefix for one declared generator."""
    if gen["install"] == "node-builtin":
        subprocess.run(["node", "--version"], check=True)
        subprocess.run(["npm", "--version"], check=True)
        return ["npm"]

    asset = fill(gen["asset"], gen)
    archive, digest = fetch(f"generator.{name}", gen, asset, folder)
    if "verify" in gen:
        verify_signature(name, gen, verifiers, asset, digest, folder)
    binary = executable(gen, archive, folder)
    subprocess.run([str(binary), "--version"], check=True)
    return [str(binary)]


def generate(artifact):
    generators, verifiers, outputs = config()
    out = next((item for item in outputs if item["artifact"] == artifact), None)
    if out is None:
        raise ValueError(f"No output named {artifact!r} in {CONFIG}")
    gen = generators[out["generator"]]

    # WHY: The downloaded executable lives in the temporary folder, so keep
    #      the folder until the SBOM is written.
    with tempfile.TemporaryDirectory() as temp:
        command = install(out["generator"], gen, verifiers, Path(temp))
        OUT.mkdir(exist_ok=True)
        target = (OUT / f"{artifact}.json").resolve()
        for step in gen.get("prepare", []):
            subprocess.run(step, check=True)
        args = [arg.format(path=".", output=str(target)) for arg in out["args"]]
        if out.get("stdout", False):
            with target.open("wb") as handle:
                subprocess.run(command + args, stdout=handle, check=True)
        else:
            subprocess.run(command + args, check=True)

    document = json.loads(target.read_text(encoding="utf-8"))
    received = document.get(VERSION_FIELD[out["format"]])
    if received != out["version"]:
        raise ValueError(f"{artifact}: expected {out['version']}, received {received!r}")
    print(f"{artifact}: {received}, {target.stat().st_size} bytes")


def main(argv):
    try:
        if argv[:1] == ["plan"] and len(argv) == 1:
            plan()
        elif argv[:1] == ["generate"] and len(argv) == 2:
            generate(argv[1])
        else:
            print(__doc__)
            return 2
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(f"::error::{error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
