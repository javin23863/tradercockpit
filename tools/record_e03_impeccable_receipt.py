#!/usr/bin/env python3
"""Record the literal Impeccable detector result for the E03 candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


SCHEMA = "into-the-laboratory/e03-timing-session-rebuild/impeccable-receipt/v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def stable_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def target_manifest(target: Path, output: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(target.rglob("*")):
        if not path.is_file() or path == output or "build" in path.relative_to(target).parts:
            continue
        rows.append({
            "path": path.relative_to(target).as_posix(),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--detector", type=Path, required=True)
    args = parser.parse_args()

    target = args.target.resolve()
    package = args.package.resolve()
    detector = args.detector.resolve()
    output = package / "impeccable-receipt.json"
    for path in (target, package, detector):
        if not path.exists():
            raise SystemExit(f"BLOCK: Impeccable receipt input missing: {path}")

    result = subprocess.run(
        ["node", str(detector), "--json", str(target)],
        cwd=detector.parents[4],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    stdout = result.stdout.strip()
    try:
        findings = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"BLOCK: Impeccable output was not JSON: {stdout!r}") from exc
    if result.returncode != 0:
        raise SystemExit(f"BLOCK: Impeccable detector exited {result.returncode}: {result.stderr[-2000:]}")
    if findings != []:
        raise SystemExit(f"BLOCK: Impeccable findings were not literal []: {findings!r}")

    manifest = target_manifest(target, output)
    manifest_bytes = json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode("utf-8")
    receipt = {
        "schema": SCHEMA,
        "episode": 3,
        "status": "PASS",
        "findings": [],
        "detector": {
            "path": str(detector),
            "sha256": sha256(detector),
            "command": "node .agents/skills/impeccable/scripts/detect.mjs --json <e03-package>",
        },
        "target": {
            "path": str(target),
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest().upper(),
            "files": manifest,
        },
    }
    stable_json(output, receipt)
    print(json.dumps({
        "receipt": str(output),
        "receipt_sha256": sha256(output),
        "detector_sha256": receipt["detector"]["sha256"],
        "target_manifest_sha256": receipt["target"]["manifest_sha256"],
        "findings": [],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
