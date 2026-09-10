#!/usr/bin/env python3
"""Generate static public concept pages from docs/concepts.v1.json."""
from __future__ import annotations

from html import escape
from pathlib import Path
import argparse
import json
import sys

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
SOURCE = DOCS / "concepts.v1.json"
OUTPUT = DOCS / "learn" / "concepts"
SITE = "https://javin23863.github.io/tradercockpit/"


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def render_list(items: list[str]) -> str:
    return "\n".join(f"            <li>{esc(item)}</li>" for item in items)


def render_related(items: list[dict]) -> str:
    return "\n".join(
        f'          <a class="related-link" href="{esc(item["path"])}"><strong>{esc(item["title"])}</strong><span>Continue to the related public concept.</span></a>'
        for item in items
    )

def render(entry: dict) -> str:
    slug = entry["slug"]
    title = entry["title"]
    canonical = f"{SITE}learn/concepts/{slug}.html"
    related = render_related(entry["related"])
    tells = render_list(entry["tells"])
    cannot = render_list(entry["cannot"])
    how_to = entry.get("howTo")
    how_to_action = f'          <a class="deep-link" href="{esc(how_to)}">Open the How-To →</a>' if how_to else ""
    how_to_aside = f'            <a class="deep-link" href="{esc(how_to)}">How-To →</a>' if how_to else ""
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="icon" href="data:,">
  <title>{esc(title)} — TraderCockpit Learn</title>
  <meta name="description" content="{esc(entry['description'])}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="stylesheet" href="../../assets/site-v2.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <nav class="site-nav" aria-label="Primary">
    <div class="nav-inner">
      <a class="brand" href="../../index.html"><span class="brand-mark" aria-hidden="true"></span>TraderCockpit</a>
      <div class="nav-links">
        <a href="../../research-lab.html">Research Lab</a>
        <a href="../" aria-current="page">Learn</a>
        <a href="../../docs/">Docs</a>
        <a href="../../methods/">Methods</a>
        <a href="../../examples/">Examples</a>
        <a href="../../updates/">Updates</a>
      </div>
    </div>
  </nav>

  <main id="main" tabindex="-1">
    <section class="article-hero">
      <div class="shell article-hero-inner">
        <div class="breadcrumb"><a href="../">Learn</a><span>/</span><span>Concepts</span><span>/</span><span>{esc(title)}</span></div>
        <span class="eyebrow">Concept / research education</span>
        <h1>{esc(title)}</h1>
        <p>{esc(entry['description'])}</p>
        <div class="article-meta"><span>Synthetic examples only</span><span>No performance promised</span><span>Research concept</span></div>
        <div class="article-actions">
          <a class="deep-link" href="{esc(entry['visual'])}">Open the visual explanation →</a>
          <a class="deep-link" href="{esc(entry['method'])}">Read the method →</a>
{how_to_action}
        </div>
      </div>
    </section>

    <section class="section article-section-wrap">
      <div class="shell article-layout">
        <article class="article-main">
          <section class="article-section" id="definition">
            <span class="kicker">Plain-language definition</span>
            <h2>What is it?</h2>
            <div class="definition-card"><strong>{esc(title)}:</strong> {esc(entry['definition'])}</div>
          </section>
          <section class="article-section" id="research-question">
            <span class="kicker">Research question</span>
            <h2>What question does it help answer?</h2>
            <p>{esc(entry['question'])}</p>
          </section>
          <section class="article-section" id="can-tell">
            <span class="kicker">Bounded interpretation</span>
            <h2>What can it tell you?</h2>
            <ul>
{tells}
            </ul>
          </section>
          <section class="article-section" id="cannot-tell">
            <span class="kicker">Limitations</span>
            <h2>What can it not tell you?</h2>
            <ul>
{cannot}
            </ul>
          </section>
          <section class="article-section" id="synthetic-example">
            <span class="kicker">Synthetic example</span>
            <h2>See the shape before reading the formula.</h2>
            <p>{esc(entry['example'])}</p>
            <a class="deep-link" href="{esc(entry['visual'])}">Open this concept in Research Lab →</a>
          </section>
          <section class="article-section" id="product-boundary">
            <span class="kicker">Where this fits</span>
            <h2>Research concept, not product instruction.</h2>
            <div class="boundary-card"><strong>Research concept:</strong> this page explains the idea itself. It does not mean a matching TraderCockpit feature is available today. For product-specific instructions, use Docs when a verified reference is published.</div>
          </section>
          <section class="article-section" id="related">
            <span class="kicker">Continue learning</span>
            <h2>Related concepts</h2>
            <div class="related-grid">
{related}
            </div>
          </section>
        </article>

        <aside class="article-aside" aria-label="Page guide">
          <div class="side-panel">
            <h2>On this page</h2>
            <ul>
              <li><a href="#definition">Definition</a></li>
              <li><a href="#research-question">Research question</a></li>
              <li><a href="#can-tell">What it can tell you</a></li>
              <li><a href="#cannot-tell">Limitations</a></li>
              <li><a href="#synthetic-example">Synthetic example</a></li>
              <li><a href="#related">Related concepts</a></li>
            </ul>
          </div>
          <div class="side-panel">
            <h2>Go deeper</h2>
            <p class="micro">Concept pages explain intuition. Methods explain assumptions and calculation. Research Lab makes the geometry visible.</p>
            <a class="deep-link" href="{esc(entry['method'])}">Method →</a>
            <a class="deep-link" href="{esc(entry['visual'])}">Visual →</a>
{how_to_aside}
          </div>
        </aside>
      </div>
    </section>
  </main>

  <footer><div class="footer-inner"><div>TraderCockpit · evidence-first research education · no performance promised.</div><div class="footer-links"><a href="../../index.html">Home</a><a href="../">Learn</a><a href="../../methods/">Methods</a></div></div></footer>
  <script src="../../assets/site-search.js" defer></script>
</body>
</html>
'''


def load_entries() -> list[dict]:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if data.get("schema") != "concept-content/v1":
        raise ValueError("unsupported concept-content schema")
    return data.get("entries", [])

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated pages differ from source data")
    args = parser.parse_args()
    entries = load_entries()
    slugs = [entry.get("slug") for entry in entries]
    if len(slugs) != len(set(slugs)):
        raise ValueError("duplicate concept slugs")

    expected = {f"{slug}.html" for slug in slugs}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    for entry in entries:
        target = OUTPUT / f"{entry['slug']}.html"
        content = render(entry)
        if args.check:
            if not target.is_file():
                problems.append(f"missing generated concept page: {target.relative_to(REPO)}")
            elif target.read_text(encoding="utf-8") != content:
                problems.append(f"stale generated concept page: {target.relative_to(REPO)}")
        else:
            target.write_text(content, encoding="utf-8", newline="\n")

    if args.check:
        extras = {path.name for path in OUTPUT.glob("*.html")} - expected
        problems.extend(f"unexpected generated concept page: {(OUTPUT / name).relative_to(REPO)}" for name in sorted(extras))
        if problems:
            print("CONCEPT GENERATION: FAIL")
            for problem in problems:
                print(f"- {problem}")
            return 1
        print(f"CONCEPT GENERATION: PASS ({len(entries)} pages current)")
    else:
        print(f"Generated {len(entries)} concept pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
