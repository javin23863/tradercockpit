#!/usr/bin/env python3
"""Enforce public product-claim and research-disclosure boundaries."""
from __future__ import annotations

from pathlib import Path
import json
import re
import sys

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
MANIFEST = DOCS / "product-manifest.v1.json"
HOME = DOCS / "index.html"

RISKY_PHRASES = (
    "available now",
    "buy now",
    "guaranteed profit",
    "guaranteed returns",
    "risk-free returns",
    "proven profitable",
    "beat the market guaranteed",
)
INTERNAL_MARKERS = (
    "c:\\users\\",
    "docs/handoffs/",
    "recovery/2026-",
    "codex/website-",
)
def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    problems: list[str] = []
    manifest = json.loads(read(MANIFEST))
    home = read(HOME)

    if manifest.get("status") != "waitlist":
        problems.append(f"expected current public status waitlist, got {manifest.get('status')!r}")
    if manifest.get("verifiedCapabilities") != []:
        problems.append("current public manifest unexpectedly exposes verified capabilities")

    if 'id="product-state">STATUS: UNVERIFIED<' not in home:
        problems.append("homepage static product state must fail closed as UNVERIFIED")
    if not re.search(r'<form[^>]*id="waitlist-form"[^>]*hidden', home):
        problems.append("homepage waitlist form must be hidden until manifest verification")
    if not re.search(r'<a[^>]*id="product-cta"[^>]*hidden', home):
        problems.append("homepage product CTA must be hidden until manifest verification")

    public_files = [p for p in DOCS.rglob("*") if p.is_file() and p.suffix.lower() in {".html", ".json", ".js", ".mjs"}]
    for path in public_files:
        text = read(path).lower()
        for phrase in RISKY_PHRASES:
            if phrase in text:
                problems.append(f"risky static public claim {phrase!r}: {path.relative_to(REPO)}")
        for marker in INTERNAL_MARKERS:
            if marker in text:
                problems.append(f"internal/local marker leaked to public surface {marker!r}: {path.relative_to(REPO)}")
    lab = read(DOCS / "research-lab.html").lower()
    for marker in ("synthetic", "not trading recommendations", "no market data"):
        if marker not in lab:
            problems.append(f"Research Lab missing public research boundary: {marker}")

    for page in sorted((DOCS / "learn" / "concepts").glob("*.html")):
        text = read(page).lower()
        if "public research concept" not in text or "does not assert" not in text:
            problems.append(f"concept page missing product-boundary disclosure: {page.relative_to(REPO)}")

    for page in sorted((DOCS / "examples").glob("*.html")):
        if page.name == "index.html":
            continue
        text = read(page).lower()
        for marker in ("synthetic", "limitations", "no performance claim"):
            if marker not in text:
                problems.append(f"example missing disclosure/limitation marker {marker!r}: {page.relative_to(REPO)}")

    if problems:
        print("PUBLIC CLAIMS: FAIL")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print(f"PUBLIC CLAIMS: PASS (status={manifest['status']}, verifiedCapabilities=0, files={len(public_files)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
