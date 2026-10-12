#!/usr/bin/env python3
"""Search and link-preview metadata for every indexable public page.

Each indexable page carries one managed block in its <head>, between
<!-- search-meta:start --> and <!-- search-meta:end -->: Open Graph, Twitter card and JSON-LD
(BreadcrumbList on inner pages, Article on guides; Organization, WebSite and SoftwareApplication
on the homepage). The block is derived from the page's own <title>, description and canonical
URL plus .github/search-pages.json, so the visible page and its previews always agree.

usage: search_metadata.py [--check]
"""
from __future__ import annotations
from pathlib import Path
import argparse, html as htmllib, json, re, sys

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / 'docs'
PAGES = ROOT / '.github' / 'search-pages.json'
SITE = 'https://trader-cockpit.com/'
ORG_ID = SITE + '#organization'
TEAM = 'TraderCockpit team'
IMAGE = SITE + 'assets/social/tradercockpit-card.png'
IMAGE_ALT = 'TraderCockpit: backtesting and strategy validation guides, beside a development-build Charts capture'
LOGO = SITE + 'assets/social/tradercockpit-logo.png'
SAME_AS = ['https://www.youtube.com/@Thetradercockpit']
START, END = '<!-- search-meta:start -->', '<!-- search-meta:end -->'
SECTIONS = {'learn': 'Learn', 'methods': 'Methods', 'how-to': 'How-to guides', 'examples': 'Examples', 'docs': 'Documentation',
            'support': 'Support', 'trust': 'Trust', 'pricing': 'Pricing', 'updates': 'Updates'}
SKIP = {'404.html', 'confirmed.html', 'thanks.html', 'help.html'}


def config() -> dict:
    return json.loads(PAGES.read_text(encoding='utf-8'))


def is_article(rel: str, cfg: dict) -> bool:
    if rel in cfg['articles']:
        return True
    parts = rel.split('/')
    return len(parts) > 1 and parts[0] in {'methods', 'how-to', 'examples'} and parts[-1] != 'index.html' or rel.startswith('learn/concepts/')


def attr(value: str) -> str:
    return htmllib.escape(value, quote=True)


def ld(value) -> str:
    return '<script type="application/ld+json">' + json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + '</script>'


def page_facts(text: str):
    title = re.search(r'<title>(.*?)</title>', text, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', text)
    canonical = re.search(r'<link rel="canonical" href="([^"]+)"', text)
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.S)
    clean = lambda v: htmllib.unescape(re.sub(r'<[^>]+>', '', v)).strip() if v else ''
    return clean(title.group(1) if title else ''), htmllib.unescape(desc.group(1)) if desc else '', canonical.group(1) if canonical else '', clean(h1.group(1) if h1 else '')


def breadcrumbs(rel: str, title: str, url: str):
    items = [{'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE}]
    parts = rel.split('/')
    if len(parts) > 1 and parts[0] in SECTIONS:
        section_url = SITE + parts[0] + '/'
        if url != section_url:
            items.append({'@type': 'ListItem', 'position': 2, 'name': SECTIONS[parts[0]], 'item': section_url})
    items.append({'@type': 'ListItem', 'position': len(items) + 1, 'name': title.split(' — ')[0], 'item': url})
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': items}


def organization():
    return {'@type': 'Organization', '@id': ORG_ID, 'name': 'TraderCockpit', 'url': SITE, 'logo': {'@type': 'ImageObject', 'url': LOGO, 'width': 512, 'height': 512}, 'sameAs': SAME_AS,
            'description': 'TraderCockpit publishes educational guides to backtesting and strategy validation and is building a Windows desktop app for trading strategy research.'}


def block_for(rel: str, text: str, cfg: dict) -> str | None:
    if rel in SKIP or re.search(r'<meta name="robots" content="[^"]*noindex', text):
        return None
    title, desc, url, h1 = page_facts(text)
    if not (title and desc and url):
        return None
    article = is_article(rel, cfg)
    tags = [
        f'<meta property="og:type" content="{"article" if article else "website"}">',
        '<meta property="og:site_name" content="TraderCockpit">',
        '<meta property="og:locale" content="en_US">',
        f'<meta property="og:title" content="{attr(title)}">',
        f'<meta property="og:description" content="{attr(desc)}">',
        f'<meta property="og:url" content="{attr(url)}">',
        f'<meta property="og:image" content="{IMAGE}">',
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{attr(IMAGE_ALT)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{attr(title)}">',
        f'<meta name="twitter:description" content="{attr(desc)}">',
        f'<meta name="twitter:image" content="{IMAGE}">',
        f'<meta name="twitter:image:alt" content="{attr(IMAGE_ALT)}">',
    ]
    if rel == 'index.html':
        graph = {'@context': 'https://schema.org', '@graph': [
            organization(),
            {'@type': 'WebSite', '@id': SITE + '#website', 'name': 'TraderCockpit', 'url': SITE, 'inLanguage': 'en', 'publisher': {'@id': ORG_ID}},
            {'@type': 'SoftwareApplication', '@id': SITE + '#app', 'name': 'TraderCockpit', 'applicationCategory': 'FinanceApplication', 'operatingSystem': 'Windows',
             'description': 'A Windows desktop app for trading strategy research: charts, strategy building and testing, and validation. In development; not yet released.',
             'url': SITE, 'publisher': {'@id': ORG_ID}, 'image': IMAGE},
        ]}
        tags.append(ld(graph))
    else:
        tags.append(ld(breadcrumbs(rel, title, url)))
    if article:
        dates = cfg['dates'].get(rel) or cfg['dates']['default']
        tags.append(f'<meta property="article:modified_time" content="{dates["modified"]}">')
        tags.append(ld({'@context': 'https://schema.org', '@type': 'Article', 'headline': (h1 or title.split(' — ')[0])[:110], 'description': desc,
                        'mainEntityOfPage': url, 'url': url, 'image': IMAGE, 'inLanguage': 'en', 'isAccessibleForFree': True,
                        'datePublished': dates.get('published', dates['modified']), 'dateModified': dates['modified'],
                        'author': {'@type': 'Organization', 'name': TEAM, 'url': SITE + 'trust/#authorship', 'parentOrganization': {'@id': ORG_ID}},
                        'publisher': {'@type': 'Organization', '@id': ORG_ID, 'name': 'TraderCockpit', 'logo': {'@type': 'ImageObject', 'url': LOGO}}}))
    return START + ''.join(tags) + END


def apply(text: str, rel: str, cfg: dict | None = None) -> str:
    cfg = cfg or config()
    text = re.sub(re.escape(START) + r'[\s\S]*?' + re.escape(END), '', text)
    block = block_for(rel, text, cfg)
    if block is None:
        return text
    return text.replace('</head>', block + '</head>', 1)


def sitemap(cfg: dict) -> str:
    """The sitemap with a <lastmod> for every URL, from the same dates the pages declare."""
    text = (DOCS / 'sitemap.xml').read_text(encoding='utf-8')
    def date_for(url: str) -> str:
        rel = url[len(SITE):] or 'index.html'
        if rel.endswith('/'):
            rel += 'index.html'
        return (cfg['dates'].get(rel) or cfg['dates']['default'])['modified']
    text = re.sub(r'\n    <lastmod>[^<]*</lastmod>', '', text)
    return re.sub(r'(    <loc>([^<]+)</loc>)', lambda m: m.group(1) + f'\n    <lastmod>{date_for(m.group(2))}</lastmod>', text)


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--check', action='store_true'); args = ap.parse_args()
    cfg = config(); stale = []
    site_map = sitemap(cfg)
    if site_map != (DOCS / 'sitemap.xml').read_text(encoding='utf-8'):
        stale.append('sitemap.xml')
        if not args.check:
            (DOCS / 'sitemap.xml').write_bytes(site_map.encode('utf-8'))
    for page in sorted(DOCS.rglob('*.html')):
        rel = page.relative_to(DOCS).as_posix()
        text = page.read_bytes().decode('utf-8')
        new = apply(text, rel, cfg)
        if new != text:
            stale.append(rel)
            if not args.check:
                page.write_bytes(new.encode('utf-8'))
    if args.check:
        print('SEARCH METADATA: ' + ('FAIL' if stale else 'PASS'))
        for rel in stale:
            print('- stale search metadata: ' + rel)
        return 1 if stale else 0
    print(f'Updated search metadata on {len(stale)} pages')
    return 0


if __name__ == '__main__':
    sys.exit(main())
