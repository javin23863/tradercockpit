#!/usr/bin/env python3
"""Audit a human-facing text surface without rewriting or validating its claims."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__:
    from . import ai_writing_gate
else:
    import ai_writing_gate


SURFACE_MODES = {
    "teaching_narration": "personal",
    "youtube_title": "marketing",
    "youtube_description": "marketing",
    "public_doc": "technical",
}

SCOPE = {
    "rewrites_text": False,
    "checks_claim_accuracy": False,
    "checks_required_disclosures": False,
}


def _unsupported(surface_kind: str) -> dict:
    return {
        "verdict": "BLOCK",
        "blocked": [{
            "type": "unsupported surface kind",
            "count": 1,
            "detail": (
                f"Unsupported surface kind {surface_kind!r}; expected one of "
                f"{', '.join(SURFACE_MODES)}."
            ),
        }],
        "warns": [],
        "metrics": {},
        "surface_kind": surface_kind,
        "context_mode": None,
        "scope": SCOPE.copy(),
    }


def audit_text(text: str, surface_kind: str) -> dict:
    """Route text to the existing detector and preserve separate claim/disclosure gates."""
    context_mode = SURFACE_MODES.get(surface_kind)
    if context_mode is None:
        return _unsupported(surface_kind)

    report = ai_writing_gate.audit_text(text, context_mode)
    return {
        **report,
        "surface_kind": surface_kind,
        "context_mode": context_mode,
        "scope": SCOPE.copy(),
    }


def _read_target(target: Path, json_key: str | None = None) -> str:
    text = target.read_text(encoding="utf-8")
    if json_key is None:
        return text
    document = json.loads(text)
    if not isinstance(document, dict):
        raise ValueError("JSON root must be an object")
    if json_key not in document:
        raise ValueError(f"JSON key {json_key!r} is missing")
    value = document[json_key]
    if not isinstance(value, str):
        raise ValueError(f"JSON key {json_key!r} must contain a string")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("surface_kind")
    parser.add_argument("target", type=Path)
    parser.add_argument("--json-key", help="audit one top-level string field from a JSON target")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        text = _read_target(args.target, args.json_key)
        report = audit_text(text, args.surface_kind)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        report = {
            **_unsupported(args.surface_kind),
            "blocked": [{
                "type": "gate input",
                "count": 1,
                "detail": f"Unable to read {args.target}: {exc}",
            }],
        }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"human_facing_gate: {report['verdict']} -- {args.surface_kind}")
        for finding in report["blocked"]:
            print(f"  BLOCK {finding['type']}: {finding['detail']}")
    return 1 if report["verdict"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
