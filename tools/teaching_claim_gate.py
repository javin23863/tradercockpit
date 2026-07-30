#!/usr/bin/env python3
"""Block when a teaching-series paragraph lacks a valid private claim receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

MARKER = re.compile(r"^#\s*receipt:\s*([A-Za-z0-9._-]+)\s*$")
SLOT = re.compile(r"^=== SLOT ")
STAGE = re.compile(r"^\[[^\]]+\]$")
SCHEMA = "teaching-claims/v1"
SOURCE_FIELDS = ("citation", "locator", "supports", "limitations", "path", "sha256")
CLAIM_KINDS = {"academic", "run_receipt", "delivery"}
DELIVERY_ONLY = re.compile(
    r"^(?:welcome(?: back)?|"
    r"now let me show you (?:why|how|what i mean)|"
    r"let(?:'s| us) (?:look at|walk through|break down) (?:it|this|the example|the chart)|"
    r"here(?:'s| is) (?:the point|what we(?:'re| are) going to do)|"
    r"keep that in mind)[.!?]?$",
    re.IGNORECASE,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paragraphs(path: Path) -> list[tuple[str, str]]:
    """Return (receipt ID, spoken text), refusing any unbound spoken paragraph."""
    out: list[tuple[str, str]] = []
    receipt: str | None = None
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
            receipt = marker.group(1)
        elif SLOT.match(line) or not line:
            flush()
        elif line.startswith("#") or STAGE.match(line):
            continue
        else:
            spoken.append(line)
    if receipt is not None:
        raise ValueError(f"receipt {receipt!r} has no spoken paragraph")
    if not out:
        raise ValueError(f"{path}: no receipt-bound spoken paragraphs")
    return out


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(script: Path, ontology: Path) -> tuple[int, int]:
    data = json.loads(ontology.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{ontology}: ontology must be an object")
    if data.get("schema") != SCHEMA:
        raise ValueError(f"{ontology}: schema must be {SCHEMA!r}")
    if data.get("script_sha256") != _sha(script):
        raise ValueError(f"{ontology}: script_sha256 does not match {script}")

    sources = data.get("sources")
    claims = data.get("claims")
    if not isinstance(sources, dict) or not isinstance(claims, dict):
        raise ValueError(f"{ontology}: sources and claims must be objects")

    rows = paragraphs(script)
    ids = [receipt for receipt, _ in rows]
    spoken = dict(rows)
    if len(ids) != len(set(ids)):
        raise ValueError("each receipt ID must bind exactly one spoken paragraph")
    if set(ids) != set(claims):
        missing = sorted(set(ids) - set(claims))
        unused = sorted(set(claims) - set(ids))
        raise ValueError(f"claim IDs differ; missing={missing}, unused={unused}")

    for source_id, source in sources.items():
        if not _nonempty_string(source_id):
            raise ValueError("source IDs must be non-empty strings")
        if not isinstance(source, dict):
            raise ValueError(f"source {source_id!r} must be an object")
        invalid = [field for field in SOURCE_FIELDS if not _nonempty_string(source.get(field))]
        if invalid:
            raise ValueError(f"source {source_id!r} needs non-empty string fields {invalid}")
        evidence = (ontology.parent / source["path"]).resolve()
        try:
            evidence.relative_to(ontology.parent.resolve())
        except ValueError as error:
            raise ValueError(f"source {source_id!r} path escapes the evidence bundle") from error
        if not evidence.is_file():
            raise ValueError(f"source {source_id!r} evidence file is missing: {evidence}")
        if source["sha256"] != _sha(evidence):
            raise ValueError(f"source {source_id!r} evidence sha256 does not match")

    used: set[str] = set()
    for claim_id in ids:
        claim = claims[claim_id]
        if not isinstance(claim, dict):
            raise ValueError(f"claim {claim_id!r} must be an object")
        kind = claim.get("kind")
        source_ids = claim.get("source_ids")
        if kind not in CLAIM_KINDS:
            raise ValueError(f"claim {claim_id!r}: invalid kind {kind!r}")
        if not isinstance(source_ids, list) or any(not _nonempty_string(item) for item in source_ids):
            raise ValueError(f"claim {claim_id!r}: source_ids must be a list of non-empty strings")
        if len(source_ids) != len(set(source_ids)):
            raise ValueError(f"claim {claim_id!r}: source_ids must not contain duplicates")
        if kind == "delivery":
            if source_ids or not _nonempty_string(claim.get("why_non_claim")):
                raise ValueError(f"delivery claim {claim_id!r} needs why_non_claim and no sources")
            if not DELIVERY_ONLY.fullmatch(spoken[claim_id].strip()):
                raise ValueError(
                    f"delivery claim {claim_id!r} is not an allowed delivery-only line"
                )
            continue
        if not source_ids:
            raise ValueError(f"claim {claim_id!r} needs at least one source")
        unknown = set(source_ids) - set(sources)
        if unknown:
            raise ValueError(f"claim {claim_id!r} names unknown sources {sorted(unknown)}")
        used.update(source_ids)

    unused_sources = set(sources) - used
    if unused_sources:
        raise ValueError(f"ontology contains unused sources {sorted(unused_sources)}")
    return len(rows), len(used)


def demo() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        script = root / "vo.txt"
        script.write_text(
            "=== SLOT scene-a -> a.wav ===\n\n"
            "# receipt: C1\nA factual sentence.\n\n"
            "# receipt: C2\nWelcome back.\n",
            encoding="utf-8",
        )
        evidence = root / "evidence.json"
        evidence.write_text('{"survivors": 1}', encoding="utf-8")
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
                    "path": "evidence.json",
                    "sha256": _sha(evidence),
                }
            },
            "claims": {
                "C1": {"kind": "academic", "source_ids": ["S1"]},
                "C2": {
                    "kind": "delivery",
                    "source_ids": [],
                    "why_non_claim": "Greeting only.",
                },
            },
        }), encoding="utf-8")
        assert validate(script, ontology) == (2, 1)
        script.write_text(script.read_text(encoding="utf-8") + "\nChanged.", encoding="utf-8")
        try:
            validate(script, ontology)
        except ValueError as error:
            assert "script_sha256 does not match" in str(error)
        else:
            raise AssertionError("a changed script must invalidate its ontology")
    print("PASS: receipts bind every spoken paragraph and script changes BLOCK")


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
    try:
        paragraph_count, source_count = validate(args.script, args.ontology)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"BLOCK: {error}")
        return 1
    print(f"PASS: {paragraph_count} spoken paragraphs; {source_count} sources used")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
