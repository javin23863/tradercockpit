#!/usr/bin/env python3
"""Public-site hardening checks that complement check_website.py."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json
import re
import sys
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
BASE = "https://javin23863.github.io/tradercockpit/"
MAX_TEXT_ASSET_BYTES = 100_000
GENERATED_WEBGL_BUNDLE = DOCS / "assets" / "generated" / "home-webgl-v1.js"
MAX_GENERATED_WEBGL_BYTES = 650_000
MAX_HOME_BASE_TEXT_BYTES = 165_000
MAX_HOME_LOCAL_TEXT_BYTES = 810_000

class SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[dict[str, str | None]] = []
        self.links: list[dict[str, str | None]] = []
        self.anchors: list[dict[str, str | None]] = []
        self.iframes: list[dict[str, str | None]] = []
        self.videos: list[dict[str, str | None]] = []
        self.metas: list[dict[str, str | None]] = []
        self.canonical = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        data = dict(attrs)
        if tag == "script": self.scripts.append(data)
        elif tag == "link":
            self.links.append(data)
            if data.get("rel") == "canonical": self.canonical = data.get("href", "") or ""
        elif tag == "a": self.anchors.append(data)
        elif tag == "iframe": self.iframes.append(data)
        elif tag == "video": self.videos.append(data)
        elif tag == "meta": self.metas.append(data)

def parse(path: Path) -> SurfaceParser:
    parser = SurfaceParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def is_external(value: str) -> bool:
    split = urlsplit(value)
    return bool(split.scheme or split.netloc)


def local_asset(source: Path, value: str) -> Path | None:
    split = urlsplit(value)
    if is_external(value) or not split.path or split.path.startswith("data:"):
        return None
    return (source.parent / split.path).resolve()


def main() -> int:
    problems: list[str] = []
    html_pages = sorted(DOCS.rglob("*.html"))
    not_found = DOCS / "404.html"
    if not not_found.is_file(): problems.append("missing public 404.html")
    canonical_seen: dict[str, Path] = {}
    parsers: dict[Path, SurfaceParser] = {}

    for page in html_pages:
        parser = parse(page)
        parsers[page] = parser
        if page == not_found:
            robots = " ".join((attrs.get("content") or "") for attrs in parser.metas if (attrs.get("name") or "").lower() == "robots").lower()
            if "noindex" not in robots: problems.append("404.html must declare robots=noindex")
            if parser.canonical: problems.append("404.html must not declare a canonical URL")
        if parser.canonical:
            if not parser.canonical.startswith(BASE):
                problems.append(f"canonical outside public site: {page.relative_to(REPO)}")
            previous = canonical_seen.get(parser.canonical)
            if previous and previous != page:
                problems.append(f"duplicate canonical: {parser.canonical}")
            canonical_seen[parser.canonical] = page
        for attrs in parser.scripts:
            src = attrs.get("src") or ""
            if src and is_external(src):
                problems.append(f"external script on load: {page.relative_to(REPO)} -> {src}")
        for attrs in parser.links:
            href = attrs.get("href") or ""
            rel = attrs.get("rel") or ""
            if "stylesheet" in rel and href and is_external(href):
                problems.append(f"external stylesheet on load: {page.relative_to(REPO)} -> {href}")
        page_text = page.read_text(encoding="utf-8")
        if '<a class="skip-link" href="#main"' in page_text and not re.search(r'<main\b[^>]*\bid="main"[^>]*\btabindex="-1"', page_text):
            problems.append(f"skip-link target is not keyboard-focusable: {page.relative_to(REPO)}")
        if parser.iframes:
            problems.append(f"eager iframe present: {page.relative_to(REPO)}")
        for attrs in parser.videos:
            if attrs.get("autoplay") is not None:
                problems.append(f"autoplay video present: {page.relative_to(REPO)}")
        for attrs in parser.anchors:
            if attrs.get("target") == "_blank":
                rel = (attrs.get("rel") or "").split()
                if "noopener" not in rel:
                    problems.append(f"target=_blank missing noopener: {page.relative_to(REPO)}")

    # Sitemap must contain every indexable canonical page except the resolver utility.
    sitemap = DOCS / "sitemap.xml"
    if not sitemap.is_file():
        problems.append("missing sitemap.xml")
        sitemap_urls: set[str] = set()
    else:
        try:
            root = ET.parse(sitemap).getroot()
            sitemap_urls = {
                node.text.strip() for node in root.findall(
                    "{http://www.sitemaps.org/schemas/sitemap/0.9}url/"
                    "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
                ) if node.text
            }
        except ET.ParseError as exc:
            problems.append(f"invalid sitemap XML: {exc}")
            sitemap_urls = set()
    for page, parser in parsers.items():
        if page.name == "help.html" or not parser.canonical:
            continue
        if parser.canonical not in sitemap_urls:
            problems.append(f"canonical missing from sitemap: {page.relative_to(REPO)}")

    # Ordinary text assets stay dependency-light. The generated WebGL runtime has its own
    # bounded budget and is rebuilt from pinned source/dependencies in website-integrity CI.
    for path in sorted(DOCS.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".html", ".css", ".js", ".mjs", ".json"}:
            limit = MAX_GENERATED_WEBGL_BYTES if path == GENERATED_WEBGL_BUNDLE else MAX_TEXT_ASSET_BYTES
            if path.stat().st_size > limit:
                problems.append(f"oversized text asset ({path.stat().st_size} bytes > {limit}): {path.relative_to(REPO)}")
    home = DOCS / "index.html"
    home_parser = parsers.get(home)
    if home_parser:
        payload_paths: set[Path] = {home}
        for attrs in home_parser.scripts:
            src = attrs.get("src") or ""
            target = local_asset(home, src)
            if target and target.is_file(): payload_paths.add(target)
        for attrs in home_parser.links:
            if "stylesheet" not in (attrs.get("rel") or ""): continue
            target = local_asset(home, attrs.get("href") or "")
            if target and target.is_file(): payload_paths.add(target)
        payload = sum(path.stat().st_size for path in payload_paths)
        webgl_bytes = GENERATED_WEBGL_BUNDLE.stat().st_size if GENERATED_WEBGL_BUNDLE in payload_paths and GENERATED_WEBGL_BUNDLE.is_file() else 0
        base_payload = payload - webgl_bytes
        if base_payload > MAX_HOME_BASE_TEXT_BYTES:
            problems.append(f"homepage non-WebGL text payload exceeds base budget: {base_payload} bytes")
        if webgl_bytes > MAX_GENERATED_WEBGL_BYTES:
            problems.append(f"homepage generated WebGL bundle exceeds budget: {webgl_bytes} bytes")
        if payload > MAX_HOME_LOCAL_TEXT_BYTES:
            problems.append(f"homepage local text payload exceeds total budget: {payload} bytes")

    # The product and prelaunch JSON remain authorities, not duplicated static claims.
    manifest = json.loads((DOCS / "product-manifest.v1.json").read_text(encoding="utf-8"))
    if manifest.get("status") == "waitlist":
        home_text = home.read_text(encoding="utf-8")
        if 'id="waitlist-form"' not in home_text or 'id="product-cta"' not in home_text:
            problems.append("waitlist manifest state lacks fail-closed conversion surfaces")
        if not re.search(r'id="waitlist-form"[^>]*hidden', home_text):
            problems.append("waitlist form is not statically fail-closed")
        if not re.search(r'id="product-cta"[^>]*hidden', home_text):
            problems.append("product CTA is not statically fail-closed")

    if problems:
        print("SITE HARDENING: FAIL")
        for problem in problems: print(f"- {problem}")
        return 1
    home_payload = sum(path.stat().st_size for path in payload_paths) if home_parser else 0
    print(f"SITE HARDENING: PASS ({len(html_pages)} HTML pages, {len(canonical_seen)} canonicals, home local text payload {home_payload} bytes)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
