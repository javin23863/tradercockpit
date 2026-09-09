#!/usr/bin/env python3
"""Focused integrity checks for the additive TraderCockpit public-site architecture."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json
import os
import sys

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
PAGES = [
    DOCS / "research-lab.html",
    DOCS / "docs" / "index.html",
    DOCS / "learn" / "index.html",
    DOCS / "how-to" / "index.html",
    DOCS / "methods" / "index.html",
    DOCS / "examples" / "index.html",
    DOCS / "updates" / "index.html",
]
REGISTRY = DOCS / "help-registry.v1.json"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.title = ""
        self.description = ""
        self.canonical = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        data = dict(attrs)
        if data.get("id"):
            self.ids.add(data["id"])
        if tag == "a" and data.get("href"):
            self.links.append(data["href"])
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


def main() -> int:
    problems: list[str] = []
    parsers: dict[Path, PageParser] = {}

    for page in PAGES:
        if not page.is_file():
            problems.append(f"missing page: {page.relative_to(REPO)}")
            continue
        parser = parse_page(page)
        parsers[page] = parser
        if not parser.title.strip():
            problems.append(f"missing title: {page.relative_to(REPO)}")
        if not parser.description.strip():
            problems.append(f"missing description: {page.relative_to(REPO)}")
        if not parser.canonical.startswith("https://javin23863.github.io/tradercockpit/"):
            problems.append(f"bad canonical: {page.relative_to(REPO)}")

    if not REGISTRY.is_file():
        problems.append("missing docs/help-registry.v1.json")
    else:
        try:
            registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"invalid help registry JSON: {exc}")
            registry = {"entries": []}
        entries = registry.get("entries", [])
        ids = [entry.get("id") for entry in entries]
        if len(ids) != len(set(ids)):
            problems.append("duplicate help registry IDs")
        for entry in entries:
            required = {"id", "path", "title", "kind", "status", "aliases"}
            missing = required.difference(entry)
            if missing:
                problems.append(f"help entry {entry.get('id')} missing {sorted(missing)}")
                continue
            split = urlsplit(entry["path"])
            target = DOCS / split.path
            if split.path.endswith("/"):
                target /= "index.html"
            if not target.is_file():
                problems.append(f"help entry {entry['id']} missing target {entry['path']}")
                continue
            if split.fragment:
                parser = parsers.get(target) or parse_page(target)
                if split.fragment not in parser.ids:
                    problems.append(f"help entry {entry['id']} missing anchor #{split.fragment}")

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

    print(f"WEBSITE INTEGRITY: PASS ({len(PAGES)} pages, {len(json.loads(REGISTRY.read_text(encoding='utf-8'))['entries'])} help IDs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
