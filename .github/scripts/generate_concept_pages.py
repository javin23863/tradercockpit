#!/usr/bin/env python3
"""Generate static public concept pages from docs/concepts.v1.json."""
from __future__ import annotations

from html import escape
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_chrome import apply as chrome, cta

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"
SOURCE = DOCS / "concepts.v1.json"
OUTPUT = DOCS / "learn" / "concepts"
SITE = "https://trader-cockpit.com/"


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def render_list(items: list[str]) -> str:
    return "\n".join(f"            <li>{esc(item)}</li>" for item in items)


def render_related(items: list[dict]) -> str:
    return "\n".join(
        f'          <a class="related-link" href="{esc(item["path"])}"><strong>{esc(item["title"])}</strong></a>'
        for item in items
    )

# Where each idea is used in the app: (features anchor, its name, one line).
FEATURES = {
    "monte-carlo": ("results", "Results", "Results runs Monte Carlo tests on a strategy's own trades and shows the spread of outcomes."),
    "out-of-sample": ("workflows", "Workflows and robustness checks", "Workflows hold back out-of-sample periods and test a strategy on them without you setting up each run."),
    "walk-forward": ("workflows", "Workflows and robustness checks", "Workflows run walk-forward windows and recompute them when you change the windows."),
    "parameter-robustness": ("workflows", "Workflows and robustness checks", "Robustness checks retest a strategy on other markets, other timeframes and with slippage."),
    "drawdown": ("results", "Results", "Results shows each strategy's drawdown beside its trades, equity and results by period."),
    "selection-bias": ("workflows", "Workflows and robustness checks", "After a search, workflows put every kept strategy through tests it was not built on."),
    "correlation-diversification": ("portfolio", "Portfolio", "Portfolio combines your saved strategies and shows their results together."),
    "distribution-shape": ("results", "Results", "Results shows trade excursions and results by period, so you see more than the average."),
    "regime-map": ("results", "Results", "Results breaks a strategy's results down by period and by market."),
}


def render(entry: dict) -> str:
    slug = entry["slug"]
    cta_href, cta_label = cta("../../")
    title = entry["title"]
    canonical = f"{SITE}learn/concepts/{slug}.html"
    related = render_related(entry["related"])
    tells = render_list(entry["tells"])
    cannot = render_list(entry["cannot"])
    how_to = entry.get("howTo")
    how_to_action = f'          <a class="deep-link" href="{esc(how_to)}">Read the how-to guide</a>' if how_to else ""
    how_to_aside = f'            <a class="deep-link" href="{esc(how_to)}">How-to guide</a>' if how_to else ""
    modified = entry.get('dateModified')
    authorship = '<p class="micro">By <a href="../../trust/#authorship">the Trader Cockpit team</a>. Educational material, not financial advice.</p>'
    feature, feature_name, feature_line = FEATURES[slug]
    example = f'<section class="article-section" id="example"><h2>{esc(entry.get("exampleTitle") or "An example")}</h2><p>{esc(entry["example"])}</p></section>' if entry.get('example') else ''
    example_link = '<li><a href="#example">Example</a></li>' if entry.get('example') else ''
    assumptions = '<section class="article-section" id="assumptions"><h2>What the test assumes</h2><ul>'+render_list(entry['assumptions'])+'</ul></section>' if entry.get('assumptions') else ''
    references = '<section class="article-section" id="references"><h2>Sources</h2><ul>'+''.join(f'<li><a href="{esc(ref["url"])}">{esc(ref["title"])}</a> — {esc(ref["scope"])}</li>' for ref in entry.get('references',[]))+'</ul></section>' if entry.get('references') else ''
    html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="icon" href="/assets/reference-site/mark.svg" type="image/svg+xml">
  <title>{esc(entry.get('seoTitle', title))} — Trader Cockpit Learn</title>
  <meta name="description" content="{esc(entry['description'])}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="stylesheet" href="../../assets/site-v2.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <nav class="site-nav" aria-label="Primary">
    <div class="nav-inner">
      <a class="brand" href="../../index.html"><span class="brand-mark" aria-hidden="true"></span>Trader Cockpit</a>
      <div class="nav-links">
        <a href="../../research-lab.html">Research Lab</a>
        <a href="../" aria-current="page">Learn</a>
        <a href="../../community/">Community</a>
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
        <h1>{esc(title)}</h1>
        <p>{esc(entry['description'])}</p>
        {authorship}
        <div class="article-actions">
          <a class="deep-link" href="{esc(entry['method'])}">Read the method</a>
{how_to_action}
        </div>
      </div>
    </section>

    <section class="section article-section-wrap">
      <div class="shell article-layout">
        <article class="article-main">
          <section class="article-section" id="definition">
            <h2>What is it?</h2>
            <div class="definition-card"><strong>{esc(title)}:</strong> {esc(entry['definition'])}</div>
          </section>
          <section class="article-section" id="research-question">
            <h2>What question does it help answer?</h2>
            <p>{esc(entry['question'])}</p>
          </section>
          <section class="article-section" id="can-tell">
            <h2>What can it tell you?</h2>
            <ul>
{tells}
            </ul>
          </section>
          <section class="article-section" id="cannot-tell">
            <h2>What can it not tell you?</h2>
            <ul>
{cannot}
            </ul>
          </section>
          {example}
          {assumptions}
          {references}
          <section class="article-section" id="in-the-app">
            <h2>Do this in Trader Cockpit</h2>
            <p>{feature_line}</p>
            <div class="article-actions"><a class="deep-link" href="../../features/#{feature}">{feature_name}</a><a class="deep-link" href="../../pricing/">Pricing</a><a class="deep-link" href="{cta_href}">{cta_label}</a></div>
          </section>
          <section class="article-section" id="related">
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
              {example_link}
              <li><a href="#related">Related concepts</a></li>
            </ul>
          </div>
          <div class="side-panel">
            <h2>Go deeper</h2>
            <a class="deep-link" href="{esc(entry['method'])}">Method</a>
{how_to_aside}
          </div>
        </aside>
      </div>
    </section>
  </main>

  <footer><div class="footer-inner"><div>Trader Cockpit · evidence-first research education · no performance promised.</div><div class="footer-links"><a href="../../index.html">Home</a><a href="../">Learn</a><a href="../../methods/">Methods</a></div></div></footer>
  <script src="../../assets/site-search.js" defer></script>
</body>
</html>
'''
    return '\n'.join(line.rstrip() for line in html.splitlines()) + '\n'


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
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from search_metadata import apply as search_meta
        content = search_meta(chrome(render(entry), f"learn/concepts/{entry['slug']}.html"), f"learn/concepts/{entry['slug']}.html")
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
