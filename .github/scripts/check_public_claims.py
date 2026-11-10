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
COMMERCE = DOCS / "commerce-public.v1.json"

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
    commerce = json.loads(read(COMMERCE))
    if commerce.get("schema") != "public-commerce/v1": problems.append("invalid public commerce schema")
    checkout = commerce.get("checkout") or {}
    if manifest.get("status") != "available" and checkout.get("enabled") is not False: problems.append("checkout must stay disabled while public product status is not available")
    if checkout.get("enabled") is False and checkout.get("url") is not None: problems.append("disabled checkout must not expose a checkout URL")
    plan = commerce.get("plan") or {}
    if not isinstance(plan.get("unitAmount"), int) or plan.get("unitAmount", 0) <= 0: problems.append("public commerce plan must expose a positive integer unitAmount")

    if manifest.get("status") != "waitlist":
        problems.append(f"expected current public status waitlist, got {manifest.get('status')!r}")
    if not manifest.get("verifiedCapabilities"):
        problems.append("early access manifest must list its verified capabilities")

    if 'id="product-state" role="status">Early access<' not in home:
        problems.append("homepage static early access status is missing")
    if 'action="https://app.kit.com/forms/10131311/subscriptions"' not in read(DOCS / "early-access.html"):
        problems.append("early access form must post to the approved list only")
    if 'type="email"' in home:
        problems.append("the email form belongs on the early access page, not the homepage")
    if 'href="strategy-claim-audit-checklist.html"' not in home:
        problems.append("homepage must link to the educational checklist")

    public_files = [p for p in DOCS.rglob("*") if p.is_file() and p.suffix.lower() in {".html", ".json", ".js", ".mjs"}]
    for path in public_files:
        text = read(path).lower()
        for retired in ('app.kit.com', 'email_address', 'trackconfirmedsignup', 'bindwaitlistsubmit', 'waitlist-form'):
            # Only the early access page may post to the email provider, and only these two tokens.
            if retired in text and not (path == DOCS / "early-access.html" and retired in ("app.kit.com", "email_address")):
                problems.append(f"retired signup wiring {retired!r}: {path.relative_to(REPO)}")
        for phrase in RISKY_PHRASES:
            if phrase in text:
                problems.append(f"risky static public claim {phrase!r}: {path.relative_to(REPO)}")
        for marker in INTERNAL_MARKERS:
            if marker in text:
                problems.append(f"internal/local marker leaked to public surface {marker!r}: {path.relative_to(REPO)}")
    journeys = read(DOCS / "assets" / "reference-site" / "journeys.js").lower()
    privacy = read(DOCS / "trust" / "privacy.html").lower()
    if "localstorage" in journeys:
        false_storage_claim = "current public code does not call <code>document.cookie</code>, <code>localstorage</code>"
        if false_storage_claim in privacy:
            problems.append("privacy page falsely denies localStorage use while research notes read it")
        for marker in ("research-notes", "localstorage", "save on this device", "clearing browser data", "not sent to a server"):
            if marker not in privacy:
                problems.append(f"privacy page missing research-notes storage disclosure: {marker!r}")
    lab = read(DOCS / "research-lab.html").lower()
    for marker in ("synthetic", "not trading recommendations", "no market data"):
        if marker not in lab:
            problems.append(f"Research Lab missing public research boundary: {marker}")

    for page in sorted((DOCS / "learn" / "concepts").glob("*.html")):
        text = read(page).lower()
        if "keep the context:" not in text or "for trader cockpit controls and workflow details, open docs." not in text:
            problems.append(f"concept page missing customer-facing context disclosure: {page.relative_to(REPO)}")

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

    print(f"PUBLIC CLAIMS: PASS (status={manifest['status']}, verifiedCapabilities={len(manifest['verifiedCapabilities'])}, files={len(public_files)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
