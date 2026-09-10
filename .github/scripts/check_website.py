#!/usr/bin/env python3
"""Focused integrity checks for the additive TraderCockpit public-site architecture."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json
import os
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
PAGES = [
    DOCS / "research-lab.html",
    DOCS / "docs" / "index.html",
    DOCS / "learn" / "index.html",
    DOCS / "how-to" / "index.html",
    DOCS / "how-to" / "read-monte-carlo.html",
    DOCS / "methods" / "index.html",
    DOCS / "methods" / "monte-carlo.html",
    DOCS / "examples" / "index.html",
    DOCS / "updates" / "index.html",
    DOCS / "help.html",
] + sorted((DOCS / "learn" / "concepts").glob("*.html"))
REGISTRY = DOCS / "help-registry.v1.json"
SEARCH_INDEX = DOCS / "search-index.v1.json"
CONTENT_REGISTRY = DOCS / "content-registry.v1.json"
CONCEPT_SOURCE = DOCS / "concepts.v1.json"
CONCEPT_GENERATOR = REPO / ".github" / "scripts" / "generate_concept_pages.py"
HELP_PAGE = DOCS / "help.html"
HELP_RESOLVER = DOCS / "assets" / "help-resolver.js"
SITE_SEARCH = DOCS / "assets" / "site-search.js"
VIDEO_SCRIPT = DOCS / "assets" / "video-slot.js"
LAB_DEPTH = DOCS / "assets" / "research-lab-depth.js"
LAB_VALIDATION = DOCS / "assets" / "research-lab-validation.js"
LAB_RISK = DOCS / "assets" / "research-lab-risk.js"


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
        if not parser.canonical.startswith("https://javin23863.github.io/tradercockpit/"):
            problems.append(f"bad canonical: {page.relative_to(REPO)}")
        if not any(src.endswith("assets/site-search.js") for src in parser.scripts):
            problems.append(f"missing local search script: {page.relative_to(REPO)}")

    lab_page = DOCS / "research-lab.html"
    lab_parser = parsers.get(lab_page)
    required_lab_ids = {"parameter-robustness", "correlation", "distribution", "walk-forward", "out-of-sample", "drawdown", "selection-bias"}
    if lab_parser:
        missing_ids = required_lab_ids.difference(lab_parser.ids)
        if missing_ids:
            problems.append(f"Research Lab missing Phase B anchors: {sorted(missing_ids)}")
        if not any(src.endswith("assets/research-lab-depth.js") for src in lab_parser.scripts):
            problems.append("Research Lab Phase B script missing")
        if not any(src.endswith("assets/research-lab-validation.js") for src in lab_parser.scripts):
            problems.append("Research Lab validation script missing")
        if not any(src.endswith("assets/research-lab-risk.js") for src in lab_parser.scripts):
            problems.append("Research Lab risk script missing")
    if not LAB_DEPTH.is_file():
        problems.append("missing docs/assets/research-lab-depth.js")
    else:
        depth_script = LAB_DEPTH.read_text(encoding="utf-8")
        if "IntersectionObserver" not in depth_script:
            problems.append("Research Lab depth modules are not lazy-initialized")
        if "http://" in depth_script or "https://" in depth_script:
            problems.append("Research Lab depth script contains an external network target")
    if not LAB_VALIDATION.is_file():
        problems.append("missing docs/assets/research-lab-validation.js")
    else:
        validation_script = LAB_VALIDATION.read_text(encoding="utf-8")
        if "IntersectionObserver" not in validation_script:
            problems.append("Research Lab validation modules are not lazy-initialized")
        if "http://" in validation_script or "https://" in validation_script:
            problems.append("Research Lab validation script contains an external network target")
        if "innerHTML" in validation_script:
            problems.append("Research Lab validation script should not use innerHTML")
    if not LAB_RISK.is_file():
        problems.append("missing docs/assets/research-lab-risk.js")
    else:
        risk_script = LAB_RISK.read_text(encoding="utf-8")
        if "IntersectionObserver" not in risk_script:
            problems.append("Research Lab risk modules are not lazy-initialized")
        if "http://" in risk_script or "https://" in risk_script:
            problems.append("Research Lab risk script contains an external network target")
        if "innerHTML" in risk_script:
            problems.append("Research Lab risk script should not use innerHTML")
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

    how_to = DOCS / "how-to" / "index.html"
    how_text = how_to.read_text(encoding="utf-8") if how_to.is_file() else ""
    if "data-video-slot" not in how_text or "data-video-load" not in how_text:
        problems.append("How-To click-to-load video slot missing")
    if not re.search(r'data-video-id="[A-Za-z0-9_-]{11}"', how_text):
        problems.append("How-To video slot missing valid public video ID")
    if "<iframe" in how_text.lower():
        problems.append("How-To page eagerly embeds a third-party iframe")
    how_parser = parsers.get(how_to)
    if how_parser and not any(src.endswith("assets/video-slot.js") for src in how_parser.scripts):
        problems.append("How-To video loader script missing")
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
            if fragment and target.suffix == ".html":
                target_parser = parsers.get(target) or parse_page(target)
                if fragment not in target_parser.ids:
                    problems.append(f"broken anchor {page.relative_to(REPO)} -> {href}")

    public_text = "\n".join(page.read_text(encoding="utf-8") for page in PAGES if page.is_file())
    if REGISTRY.is_file():
        public_text += "\n" + REGISTRY.read_text(encoding="utf-8")
    if SEARCH_INDEX.is_file():
        public_text += "\n" + SEARCH_INDEX.read_text(encoding="utf-8")
    for marker in ("api_key", "secret_key", "password=", "C:\\Users\\"):
        if marker.lower() in public_text.lower():
            problems.append(f"public-disclosure marker detected: {marker}")

    lab_text = (DOCS / "research-lab.html").read_text(encoding="utf-8").lower() if (DOCS / "research-lab.html").is_file() else ""
    if "synthetic" not in lab_text or "not trading recommendations" not in lab_text:
        problems.append("Research Lab synthetic-data disclaimer missing")

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
