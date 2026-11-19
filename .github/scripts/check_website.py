#!/usr/bin/env python3
"""Focused integrity checks for the Trader Cockpit public-site architecture."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
PAGES = [
    DOCS / "index.html",
    DOCS / "docs" / "index.html",
    DOCS / "learn" / "index.html",
    DOCS / "how-to" / "index.html",
    DOCS / "how-to" / "read-monte-carlo.html",
    DOCS / "methods" / "index.html",
    DOCS / "methods" / "monte-carlo.html",
    DOCS / "methods" / "result-metrics.html",
    DOCS / "examples" / "index.html",
    DOCS / "examples" / "holdout-selection.html",
    DOCS / "updates" / "index.html",
    DOCS / "help.html",
] + sorted((DOCS / "learn" / "concepts").glob("*.html")) + sorted((DOCS / "community").rglob("index.html"))
REGISTRY = DOCS / "help-registry.v1.json"
SEARCH_INDEX = DOCS / "search-index.v1.json"
CONTENT_REGISTRY = DOCS / "content-registry.v1.json"
CONCEPT_SOURCE = DOCS / "concepts.v1.json"
CONCEPT_GENERATOR = REPO / ".github" / "scripts" / "generate_concept_pages.py"
HELP_PAGE = DOCS / "help.html"
HELP_RESOLVER = DOCS / "assets" / "help-resolver.js"
SITE_SEARCH = DOCS / "assets" / "site-search.js"
VIDEO_SCRIPT = DOCS / "assets" / "video-slot.js"
HOME_PAGE = DOCS / "index.html"
PUBLIC_HTML = sorted(DOCS.rglob("*.html"))
SITEMAP = DOCS / "sitemap.xml"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.scripts: list[str] = []
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.title = ""
        self.description = ""
        self.canonical = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        data = dict(attrs)
        if data.get("id"):
            value = data["id"]
            if value in self.ids:
                self.duplicate_ids.add(value)
            self.ids.add(value)
        if tag == "a" and data.get("href"):
            self.links.append(data["href"])
        if tag == "script" and data.get("src"):
            self.scripts.append(data["src"])
        if tag == "meta" and data.get("name") == "description":
            self.description = data.get("content", "")
        if tag == "link" and data.get("rel") == "canonical":
            self.canonical = data.get("href", "")
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def resolve_path(path_value: str) -> tuple[Path, str]:
    split = urlsplit(path_value)
    target = DOCS / split.path
    if split.path.endswith("/"):
        target /= "index.html"
    return target, split.fragment


def resolve_link(source: Path, href: str) -> tuple[Path, str] | None:
    if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:")):
        return None
    if href.startswith("#"):
        return source, href[1:]
    split = urlsplit(href)
    target = Path(os.path.normpath(os.path.join(source.parent, split.path)))
    if split.path.endswith("/"):
        target /= "index.html"
    return target, split.fragment

def validate_target(label: str, path_value: str, parsers: dict[Path, PageParser], problems: list[str]) -> None:
    target, fragment = resolve_path(path_value)
    if not target.is_file():
        problems.append(f"{label} missing target {path_value}")
        return
    if fragment and target.suffix == ".html":
        parser = parsers.get(target) or parse_page(target)
        if fragment not in parser.ids:
            problems.append(f"{label} missing anchor #{fragment}")


def main() -> int:
    problems: list[str] = []
    parsers: dict[Path, PageParser] = {}

    for page in PAGES:
        if not page.is_file():
            problems.append(f"missing page: {page.relative_to(REPO)}")
            continue
        parser = parse_page(page)
        parsers[page] = parser
        if parser.duplicate_ids:
            problems.append(f"duplicate HTML ids in {page.relative_to(REPO)}: {sorted(parser.duplicate_ids)}")
        if not parser.title.strip():
            problems.append(f"missing title: {page.relative_to(REPO)}")
        if not parser.description.strip():
            problems.append(f"missing description: {page.relative_to(REPO)}")
        if not parser.canonical.startswith("https://trader-cockpit.com/"):
            problems.append(f"bad canonical: {page.relative_to(REPO)}")
        if not any(src.endswith("assets/site-search.js") for src in parser.scripts):
            problems.append(f"missing local search script: {page.relative_to(REPO)}")

    home_text = HOME_PAGE.read_text(encoding="utf-8") if HOME_PAGE.is_file() else ""
    result = subprocess.run([sys.executable, str(REPO / '.github/scripts/check_reference_site.py')], cwd=REPO, capture_output=True, text=True)
    if result.returncode:
        problems.append('Page record integrity failed: ' + (result.stdout + result.stderr).strip())
    # One header, one footer and one stylesheet on every page: site_chrome.py owns all three.
    chrome = subprocess.run([sys.executable, str(REPO / '.github/scripts/site_chrome.py'), '--check'], cwd=REPO, capture_output=True, text=True)
    if chrome.returncode:
        problems.append('shared header, footer or stylesheet is stale: ' + (chrome.stdout + chrome.stderr).strip())
    for page in PUBLIC_HTML:
        text = page.read_text(encoding="utf-8")
        if 'http-equiv="refresh"' in text:
            continue
        sheets = re.findall(r'<link[^>]*rel="stylesheet"[^>]*href="([^"]+)"', text)
        if not any(sheet.endswith("assets/site.css") for sheet in sheets) or any(not sheet.endswith(("assets/site.css", "assets/replay-boundary-example.css")) for sheet in sheets):
            problems.append(f"public page must load the one shared stylesheet: {page.relative_to(REPO)}")
        if "research-lab.html" in text:
            problems.append(f"public page links the removed Research Lab: {page.relative_to(REPO)}")
    pricing_text = (DOCS / "pricing" / "index.html").read_text(encoding="utf-8")
    if "pricing-tier-tab" in pricing_text or ">+ Future tier<" in pricing_text or "Reserved future pricing tier" in pricing_text or "Reserved pricing expansion slot" in pricing_text:
        problems.append("pricing must expose only the verified current plan, with no unfinished expansion controls")
    if 'type="email"' in home_text:
        problems.append("the email form belongs on the early access page, not the homepage")
    if 'href="strategy-claim-audit-checklist.html"' not in home_text or 'href="features/"' not in home_text or 'href="pricing/' not in home_text:
        problems.append("the homepage must link Features, Pricing and the backtest checklist without JavaScript")
    for legacy_id in ("initiate", "rungrid", "phases", "verdict", "chips"):
        if f'id="{legacy_id}"' in home_text:
            problems.append(f"legacy homepage simulation remains present: #{legacy_id}")
    for gone in ("assets/reference-site/app.js", "assets/reference-site/journeys.js", "assets/generated", "assets/site-v2.css"):
        if (DOCS / gone).exists():
            problems.append(f"file of the removed design is back: docs/{gone}")
    if not CONCEPT_SOURCE.is_file():
        problems.append("missing docs/concepts.v1.json")
    elif not CONCEPT_GENERATOR.is_file():
        problems.append("missing concept-page generator")
    else:
        generated = subprocess.run(
            [sys.executable, str(CONCEPT_GENERATOR), "--check"],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )
        if generated.returncode != 0:
            detail = (generated.stdout + generated.stderr).strip().replace("\n", " | ")
            problems.append(f"generated concept pages are stale: {detail}")
    # Link previews, structured data and sitemap dates must match each page's own title and description.
    search_meta = subprocess.run(
        [sys.executable, str(REPO / ".github" / "scripts" / "search_metadata.py"), "--check"],
        cwd=REPO, text=True, capture_output=True, check=False,
    )
    if search_meta.returncode != 0:
        detail = (search_meta.stdout + search_meta.stderr).strip().replace("\n", " | ")
        problems.append(f"search metadata is stale: {detail}")

    content_entries: list[dict] = []
    if not CONTENT_REGISTRY.is_file():
        problems.append("missing docs/content-registry.v1.json")
    else:
        try:
            content_registry = json.loads(CONTENT_REGISTRY.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"invalid content registry JSON: {exc}")
            content_registry = {"kinds": {}, "entries": []}
        if content_registry.get("schema") != "content-registry/v1":
            problems.append("unsupported content registry schema")
        kinds = content_registry.get("kinds", {})
        required_kinds = {"concept", "method", "how-to", "reference", "lab", "landing", "example", "updates"}
        if not required_kinds.issubset(kinds):
            problems.append(f"content registry missing kinds: {sorted(required_kinds.difference(kinds))}")
        content_entries = content_registry.get("entries", [])
        content_ids = [entry.get("id") for entry in content_entries]
        if len(content_ids) != len(set(content_ids)):
            problems.append("duplicate content registry IDs")
        for entry in content_entries:
            required = {"id", "kind", "path", "title", "status"}
            missing = required.difference(entry)
            if missing:
                problems.append(f"content entry {entry.get('id')} missing {sorted(missing)}")
                continue
            if entry["kind"] not in kinds:
                problems.append(f"content entry {entry['id']} has unknown kind {entry['kind']}")
            if entry["status"] != "public":
                problems.append(f"public content registry entry {entry['id']} must have status public")
            validate_target(f"content entry {entry['id']}", entry["path"], parsers, problems)

        concept_paths = {f"learn/concepts/{entry.get('slug')}.html" for entry in json.loads(CONCEPT_SOURCE.read_text(encoding="utf-8")).get("entries", [])}
        registered_concepts = {entry.get("path") for entry in content_entries if entry.get("kind") == "concept"}
        if concept_paths != registered_concepts:
            problems.append("content registry concept paths do not exactly match generated concept source")
    registry_entries: list[dict] = []
    if not REGISTRY.is_file():
        problems.append("missing docs/help-registry.v1.json")
    else:
        try:
            registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"invalid help registry JSON: {exc}")
            registry = {"entries": []}
        if registry.get("schema") != "help-registry/v1":
            problems.append("unsupported help registry schema")
        registry_entries = registry.get("entries", [])
        ids = [entry.get("id") for entry in registry_entries]
        if len(ids) != len(set(ids)):
            problems.append("duplicate help registry IDs")
        for entry in registry_entries:
            required = {"id", "path", "title", "kind", "status", "aliases"}
            missing = required.difference(entry)
            if missing:
                problems.append(f"help entry {entry.get('id')} missing {sorted(missing)}")
                continue
            validate_target(f"help entry {entry['id']}", entry["path"], parsers, problems)

    search_entries: list[dict] = []
    if not SEARCH_INDEX.is_file():
        problems.append("missing docs/search-index.v1.json")
    else:
        try:
            search_index = json.loads(SEARCH_INDEX.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"invalid search index JSON: {exc}")
            search_index = {"entries": []}
        if search_index.get("schema") != "site-search/v1":
            problems.append("unsupported search index schema")
        search_entries = search_index.get("entries", [])
        ids = [entry.get("id") for entry in search_entries]
        if len(ids) != len(set(ids)):
            problems.append("duplicate search index IDs")
        for entry in search_entries:
            required = {"id", "title", "path", "kind", "summary", "terms"}
            missing = required.difference(entry)
            if missing:
                problems.append(f"search entry {entry.get('id')} missing {sorted(missing)}")
                continue
            if urlsplit(entry["path"]).scheme:
                problems.append(f"search entry {entry['id']} must remain local")
                continue
            validate_target(f"search entry {entry['id']}", entry["path"], parsers, problems)

    help_parser = parsers.get(HELP_PAGE)
    if not HELP_PAGE.is_file():
        problems.append("missing docs/help.html")
    elif help_parser and not any(src.endswith("assets/help-resolver.js") for src in help_parser.scripts):
        problems.append("help.html is missing the help resolver script")
    if not HELP_RESOLVER.is_file():
        problems.append("missing docs/assets/help-resolver.js")
    else:
        resolver_script = HELP_RESOLVER.read_text(encoding="utf-8")
        if "help-registry.v1.json" not in resolver_script:
            problems.append("help resolver does not load public registry")
        if "URLSearchParams" not in resolver_script or "window.location.replace" not in resolver_script:
            problems.append("help resolver must accept an ID and resolve it to the registry destination")
        if "target.origin !== window.location.origin" not in resolver_script:
            problems.append("help resolver is missing same-origin target enforcement")
        if "innerHTML" in resolver_script:
            problems.append("help resolver should not use innerHTML")
        if "http://" in resolver_script or "https://" in resolver_script:
            problems.append("help resolver contains an external network target")
    if not SITE_SEARCH.is_file():
        problems.append("missing docs/assets/site-search.js")
    else:
        search_script = SITE_SEARCH.read_text(encoding="utf-8")
        if "search-index.v1.json" not in search_script:
            problems.append("site search does not load local search index")
        if "http://" in search_script or "https://" in search_script:
            problems.append("site search contains an external network target")
        for marker in (
            "MAX_INITIAL_QUERY_LENGTH = 120",
            "hashParams.get('search') ?? urlParams.get('q')",
            "searchUi.input.value = initialQuery",
            "searchUi.search(initialQuery)",
        ):
            if marker not in search_script:
                problems.append(f"site search missing bounded URL-prefill contract: {marker}")

    example_text = (DOCS / "examples" / "holdout-selection.html").read_text(encoding="utf-8")
    for example_marker in ("256 synthetic candidates", "Reserved holdout", "No performance claim", "limitations", "next-question"):
        if example_marker not in example_text:
            problems.append(f"synthetic example contract missing: {example_marker}")

    if not VIDEO_SCRIPT.is_file():
        problems.append("missing docs/assets/video-slot.js")
    else:
        video_script = VIDEO_SCRIPT.read_text(encoding="utf-8")
        if "youtube-nocookie.com/embed/" not in video_script or "addEventListener('click'" not in video_script:
            problems.append("video loader must create privacy-enhanced embed only after click")

    for page, parser in parsers.items():
        for href in parser.links:
            resolved = resolve_link(page, href)
            if not resolved:
                continue
            target, fragment = resolved
            if not target.is_file():
                problems.append(f"broken link {page.relative_to(REPO)} -> {href}")
                continue
            if target == HOME_PAGE and fragment.split('?')[0] in {'/learn','/learn/monte-carlo','/learn/checklist','/platform/charts','/platform/models','/access'}:
                continue  # Exact existing hash routes have native page rendering, not static IDs.
            if fragment and target.suffix == ".html":
                target_parser = parsers.get(target) or parse_page(target)
                if fragment not in target_parser.ids:
                    problems.append(f"broken anchor {page.relative_to(REPO)} -> {href}")

    if not SITEMAP.is_file():
        problems.append("missing docs/sitemap.xml")
    else:
        try:
            root = ET.parse(SITEMAP).getroot()
            sitemap_urls = {node.text.strip() for node in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc") if node.text}
        except (ET.ParseError, OSError) as exc:
            problems.append(f"invalid sitemap XML: {exc}")
            sitemap_urls = set()
        expected_urls = {parser.canonical for page, parser in parsers.items() if page != HELP_PAGE and parser.canonical}
        missing_urls = expected_urls.difference(sitemap_urls)
        if missing_urls:
            problems.append(f"sitemap missing public pages: {sorted(missing_urls)}")

    public_text = "\n".join(page.read_text(encoding="utf-8") for page in PAGES if page.is_file())
    if REGISTRY.is_file():
        public_text += "\n" + REGISTRY.read_text(encoding="utf-8")
    if SEARCH_INDEX.is_file():
        public_text += "\n" + SEARCH_INDEX.read_text(encoding="utf-8")
    for marker in ("api_key", "secret_key", "password=", "C:\\Users\\"):
        if marker.lower() in public_text.lower():
            problems.append(f"public-disclosure marker detected: {marker}")

    if problems:
        print("WEBSITE INTEGRITY: FAIL")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print(
        f"WEBSITE INTEGRITY: PASS ({len(PAGES)} pages, "
        f"{len(registry_entries)} help IDs, {len(search_entries)} search entries)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
