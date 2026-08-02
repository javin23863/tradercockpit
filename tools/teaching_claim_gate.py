#!/usr/bin/env python3
"""Fail closed when a teaching-series paragraph lacks a private claim receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path

MARKER = re.compile(r"^#\s*receipt:\s*([A-Za-z0-9._,-]+)\s*$")
SLOT = re.compile(r"^=== SLOT ")
STAGE = re.compile(r"^\[[^\]]+\]$")
SCHEMA = "teaching-claims/v1"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paragraphs(path: Path) -> list[tuple[tuple[str, ...], str]]:
    out: list[tuple[tuple[str, ...], str]] = []
    receipt: tuple[str, ...] | None = None
    spoken: list[str] = []

    def flush() -> None:
        nonlocal receipt, spoken
        text = " ".join(line.strip() for line in spoken if line.strip()).strip()
        spoken = []
        if not text:
            return
        if receipt is None:
            raise ValueError(f"spoken paragraph has no '# receipt:' marker: {text[:100]!r}")
        out.append((receipt, text))
        receipt = None

    for raw in path.read_text(encoding="utf-8").splitlines() + [""]:
        line = raw.strip()
        marker = MARKER.match(line)
        if marker:
            flush()
            if receipt is not None:
                raise ValueError(f"receipt {receipt!r} has no spoken paragraph")
            receipt = tuple(part.strip() for part in marker.group(1).split(","))
        elif SLOT.match(line) or not line:
            flush()
        elif line.startswith("#") or STAGE.match(line):
            continue
        else:
            spoken.append(line)
    if receipt is not None:
        raise ValueError(f"receipt {receipt!r} has no spoken paragraph")
    return out


def validate(script: Path, ontology: Path) -> tuple[int, int]:
    data = json.loads(ontology.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError(f"{ontology}: schema must be {SCHEMA!r}")
    if data.get("script_sha256") != _sha(script):
        raise ValueError(f"{ontology}: script_sha256 does not match {script}")

    sources = data.get("sources")
    claims = data.get("claims")
    if not isinstance(sources, dict) or not isinstance(claims, dict):
        raise ValueError(f"{ontology}: sources and claims must be objects")

    rows = paragraphs(script)
    ids = [claim_id for receipt_ids, _ in rows for claim_id in receipt_ids]
    if len(ids) != len(set(ids)):
        raise ValueError("each receipt ID must bind exactly one spoken paragraph")
    if set(ids) != set(claims):
        missing = sorted(set(ids) - set(claims))
        unused = sorted(set(claims) - set(ids))
        raise ValueError(f"claim IDs differ; missing={missing}, unused={unused}")

    for source_id, source in sources.items():
        required = {"citation", "locator", "supports", "limitations"}
        if not isinstance(source, dict) or not required <= source.keys():
            raise ValueError(f"source {source_id!r} needs {sorted(required)}")
        if not all(str(source[key]).strip() for key in required):
            raise ValueError(f"source {source_id!r} has an empty required field")

    used: set[str] = set()
    for claim_id in ids:
        claim = claims[claim_id]
        kind = claim.get("kind")
        source_ids = claim.get("source_ids", [])
        if kind not in {"academic", "run_receipt", "delivery"}:
            raise ValueError(f"claim {claim_id!r}: invalid kind {kind!r}")
        if kind == "delivery":
            if source_ids or not str(claim.get("why_non_claim", "")).strip():
                raise ValueError(f"delivery claim {claim_id!r} needs why_non_claim and no sources")
            continue
        if not source_ids:
            raise ValueError(f"claim {claim_id!r} needs at least one source")
        unknown = set(source_ids) - set(sources)
        if unknown:
            raise ValueError(f"claim {claim_id!r} names unknown sources {sorted(unknown)}")
        used.update(source_ids)

    return len(rows), len(used)


def demo() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        script = root / "vo.txt"
        script.write_text(
            "=== SLOT scene-a -> a.wav ===\n\n"
            "# receipt: C1,C2\nA factual sentence.\n\n"
            "# receipt: C3\nWelcome back.\n",
            encoding="utf-8",
        )
        ontology = root / "claims.json"
        ontology.write_text(json.dumps({
            "schema": SCHEMA,
            "script_sha256": _sha(script),
            "sources": {
                "S1": {
                    "citation": "Example",
                    "locator": "p. 1",
                    "supports": "The factual sentence.",
                    "limitations": "Demonstration source only.",
                }
            },
            "claims": {
                "C1": {"kind": "academic", "source_ids": ["S1"]},
                "C2": {"kind": "academic", "source_ids": ["S1"]},
                "C3": {
                    "kind": "delivery",
                    "source_ids": [],
                    "why_non_claim": "Greeting only.",
                },
            },
        }), encoding="utf-8")
        assert validate(script, ontology) == (2, 1)
    print("PASS: every spoken paragraph is bound to one valid private receipt")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", type=Path)
    parser.add_argument("--ontology", type=Path)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        demo()
        return 0
    if not args.script or not args.ontology:
        parser.error("--script and --ontology are required unless --demo is used")
    paragraph_count, source_count = validate(args.script, args.ontology)
    print(f"PASS: {paragraph_count} spoken paragraphs; {source_count} sources used")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
