#!/usr/bin/env python3
"""Enforce the TraderCockpit public-page UX authority."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import json
import re

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
DESIGN = REPO / "DESIGN.md"
CONTRACTS = DOCS / "ux-page-contracts.v1.json"
SITE_STYLE = DOCS / "assets" / "site-v2.css"
HOME_STYLE = DOCS / "assets" / "cinematic-lab-v1.css"
VISUAL_DEPTH_STYLE = DOCS / "assets" / "site-visual-depth.css"
HOME = DOCS / "index.html"

REQUIRED_DIMENSIONS = {
    "intent", "hierarchy", "state_completeness", "form_ux",
    "feedback_affordance", "design_system", "visual_character", "audit",
}
BANNED_PUBLIC_PHRASES = (
    "is being built", "work in progress", "development preview", "public-ready",
    "product boundary", "verified-public", "internal development", "release boundary",
    "matching tradercockpit feature", "future tier", "reserved pricing",
)
BANNED_SLOP_PHRASES = (
    "quantitative research.reimagined", "game-changing", "cutting-edge", "revolutionary",
    "unlock your potential", "supercharge your", "seamless experience",
)


class UXParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.h1_depth = 0
        self.h1_text: list[str] = []
        self.h1s: list[str] = []
        self.labels_for: set[str] = set()
        self.label_depth = 0
        self.inputs: list[dict[str, object]] = []
        self.visible_disabled: list[str] = []
        self.metas: list[dict[str, str | None]] = []
        self.images: list[dict[str, str | None]] = []
        self.public_text: list[str] = []
        self._ignore = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        data = dict(attrs)
        if tag in {"script", "style"}:
            self._ignore += 1
        if tag == "meta":
            self.metas.append(data)
        if tag == "img":
            self.images.append(data)
        if tag == "h1":
            self.h1_depth += 1
            self.h1_text = []
        if tag == "label":
            self.label_depth += 1
            if data.get("for"):
                self.labels_for.add(data["for"])
        if tag in {"input", "select", "textarea"}:
            self.inputs.append({
                "tag": tag,
                "id": data.get("id", ""),
                "type": data.get("type", ""),
                "placeholder": data.get("placeholder", ""),
                "nested_label": self.label_depth > 0,
                "aria_label": data.get("aria-label", ""),
                "hidden": "hidden" in data or data.get("type") == "hidden",
            })
        if tag in {"button", "input", "select", "textarea"} and "disabled" in data and "hidden" not in data:
            if not data.get("title") and not data.get("aria-describedby"):
                self.visible_disabled.append(data.get("id") or data.get("name") or tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignore:
            self._ignore -= 1
        if tag == "h1" and self.h1_depth:
            self.h1_depth -= 1
            self.h1s.append(" ".join("".join(self.h1_text).split()))
        if tag == "label" and self.label_depth:
            self.label_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.h1_depth:
            self.h1_text.append(data)
        if not self._ignore:
            value = " ".join(data.split())
            if value:
                self.public_text.append(value)


def parse_page(path: Path) -> UXParser:
    parser = UXParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def png_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def main() -> int:
    problems: list[str] = []
    public = sorted(DOCS.rglob("*.html"))
    public_rel = {page.relative_to(DOCS).as_posix() for page in public}

    if not DESIGN.is_file():
        problems.append("missing DESIGN.md public design authority")
    else:
        design = DESIGN.read_text(encoding="utf-8")
        for marker in (
            "## 1. Intent discovery", "## 2. Information hierarchy", "## 3. State completeness",
            "## 4. Form UX", "## 5. Feedback and affordance", "## 6. UX audit",
            "## 7. Design system discipline", "## 8. Visual character", "## Anti-slop requirements",
        ):
            if marker not in design:
                problems.append(f"DESIGN.md missing authority section: {marker}")

    if not CONTRACTS.is_file():
        problems.append("missing docs/ux-page-contracts.v1.json")
        contracts = {}
    else:
        try:
            contracts = json.loads(CONTRACTS.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"invalid UX page contracts: {exc}")
            contracts = {}
    if contracts:
        if contracts.get("schema") != "tc.public-page-ux.v1":
            problems.append("UX page contracts schema mismatch")
        rows = contracts.get("pages") if isinstance(contracts.get("pages"), list) else []
        by_path = {row.get("path"): row for row in rows if isinstance(row, dict) and isinstance(row.get("path"), str)}
        if set(by_path) != public_rel:
            missing = sorted(public_rel - set(by_path))
            extra = sorted(set(by_path) - public_rel)
            problems.append(f"UX page coverage mismatch; missing={missing} extra={extra}")
        if contracts.get("page_count") != len(public):
            problems.append(f"UX page count mismatch: {contracts.get('page_count')} != {len(public)}")
        for rel in sorted(public_rel):
            row = by_path.get(rel, {})
            absent = REQUIRED_DIMENSIONS.difference(row)
            if absent:
                problems.append(f"{rel} missing UX dimensions: {sorted(absent)}")
            if row.get("audit", {}).get("status") != "pass":
                problems.append(f"{rel} does not have a passing UX audit disposition")

    for page in public:
        rel = page.relative_to(DOCS).as_posix()
        parser = parse_page(page)
        theme_colors = [attrs.get("content") for attrs in parser.metas if (attrs.get("name") or "").lower() == "theme-color"]
        expected_theme = "#080706" if page == HOME else "#060207"
        if theme_colors != [expected_theme]:
            problems.append(f"{rel} must declare the canonical dark theme-color exactly once")
        page_text = page.read_text(encoding="utf-8")
        if "site-search.js" in page_text and page != HOME and "site-visual-depth.css" not in page_text:
            problems.append(f"{rel} is missing the route-specific visual-depth stylesheet")
        if page == HOME and "site-visual-depth.css" in page_text:
            problems.append("homepage must not download route-specific visual-depth CSS")
        for image in parser.images:
            src = str(image.get("src") or "")
            if not src or src.startswith(("http://", "https://", "data:")):
                continue
            target = (page.parent / src.split("?", 1)[0].split("#", 1)[0]).resolve()
            if target.suffix.lower() != ".png" or not target.is_file():
                continue
            actual = png_dimensions(target)
            try:
                declared = (int(str(image.get("width") or "")), int(str(image.get("height") or "")))
            except ValueError:
                declared = None
            if actual and declared != actual:
                problems.append(f"{rel} image {src} must declare intrinsic size {actual[0]}x{actual[1]}")
        if len(parser.h1s) != 1:
            problems.append(f"{rel} must have exactly one H1, found {len(parser.h1s)}")
        for field in parser.inputs:
            if field["hidden"]:
                continue
            labelled = bool(field["nested_label"] or field["aria_label"] or (field["id"] and field["id"] in parser.labels_for))
            if field["placeholder"] and not labelled:
                problems.append(f"{rel} uses placeholder text without a persistent label: {field['id'] or field['tag']}")
        if parser.visible_disabled:
            problems.append(f"{rel} has visible disabled controls without an explanation: {parser.visible_disabled}")
        visible_text = " ".join(parser.public_text)
        text = visible_text.lower()
        if "\ufffd" in visible_text:
            problems.append(f"{rel} contains Unicode replacement characters")
        if re.search(r"[A-Za-z]\?[A-Za-z]", visible_text):
            problems.append(f"{rel} contains a likely encoding-damaged word")
        for phrase in (*BANNED_PUBLIC_PHRASES, *BANNED_SLOP_PHRASES):
            if phrase in text:
                problems.append(f"{rel} contains prohibited public copy: {phrase}")

    home = HOME.read_text(encoding="utf-8") if HOME.is_file() else ""
    hero_match = re.search(r'<section class="lab-hero">([\s\S]*?)</section>', home)
    if not hero_match:
        problems.append("homepage hero missing")
    else:
        hero = hero_match.group(1)
        if hero.count("lab-button-primary") != 1:
            problems.append("homepage hero must expose exactly one primary action")
        if "See TraderCockpit" not in hero:
            problems.append("homepage primary action must lead with product proof")
        if "lab-button-secondary" not in hero:
            problems.append("homepage secondary hero action must be visually subordinate")
        if "desktop-current.png" not in hero:
            problems.append("homepage hero must integrate current product proof")
    if 'class="quant-path"' in home:
        problems.append("homepage retains generic icon-feature row before product proof")

    for style_path in (SITE_STYLE, HOME_STYLE, VISUAL_DEPTH_STYLE):
        if not style_path.is_file():
            problems.append(f"missing shared UX stylesheet {style_path.relative_to(REPO)}")
    if SITE_STYLE.is_file():
        site_css = SITE_STYLE.read_text(encoding="utf-8")
        for marker in ("--ux-touch-target:44px", "@media (hover:none)", ".control-btn{padding:.68rem .72rem}", "color-scheme: dark", "touch-action: manipulation", "overscroll-behavior: contain"):
            if marker not in site_css:
                problems.append(f"shared site CSS missing UX contract marker: {marker}")
        if "100vh" in site_css:
            problems.append("shared site CSS must use dynamic viewport height instead of 100vh")
        if re.search(r"transition\s*:\s*all", site_css):
            problems.append("shared site CSS must not use transition: all")
    if VISUAL_DEPTH_STYLE.is_file():
        depth_css = VISUAL_DEPTH_STYLE.read_text(encoding="utf-8")
        if "Mandatory visual-skills parity pass" not in depth_css:
            problems.append("route-specific visual-depth CSS is missing its authority marker")
    if HOME_STYLE.is_file():
        home_css = HOME_STYLE.read_text(encoding="utf-8")
        for marker in ("--lab-brass:#c89b5c", ".lab-hero", ".lab-monitor", ".lab-pricing-grid", "@media (prefers-reduced-motion:reduce)"):
            if marker not in home_css:
                problems.append(f"homepage CSS missing UX contract marker: {marker}")

    if problems:
        print("PUBLIC UX: FAIL")
        for item in problems:
            print(f"- {item}")
        return 1
    print(f"PUBLIC UX: PASS ({len(public)}/{len(public)} public pages; 8/8 review dimensions enforced)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
