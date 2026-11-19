#!/usr/bin/env python3
"""One header, one footer, one stylesheet and one title pattern on every page, and the guide hubs as plain lists.

The header button follows docs/product-manifest.v1.json: "available" shows Download, anything else the early access list.
Titles, descriptions and h1s come from .github/product/page-meta.v1.json. Generators pass their pages through apply().
usage: site_chrome.py [--check]
"""
from html import escape as e,unescape
from pathlib import Path
import json,re,sys

ROOT=Path(__file__).resolve().parents[2];DOCS=ROOT/'docs'
NAV=(('features/','Features'),('pricing/','Pricing'),('community/','Community'),('learn/','Learn'),('support/','Support'))
SECTION={'features':'features/','pricing':'pricing/','community':'community/','learn':'learn/','how-to':'learn/','methods':'learn/','examples':'learn/','docs':'learn/','strategy-claim-audit-checklist.html':'learn/','support':'support/','trust':'support/','updates':'support/','help.html':'support/'}
FOOTER=(
    ('Product',(('features/','Features'),('pricing/','Pricing'),('community/','Community'),('updates/','Updates'))),
    ('Guides',(('learn/','Learn'),('how-to/','How-to guides'),('methods/','Methods'),('examples/','Worked examples'),('strategy-claim-audit-checklist.html','Backtest checklist'))),
    ('Company',(('trust/','About'),('support/','Support'),('support/faq.html','FAQ'),('trust/privacy.html','Privacy'),('trust/terms.html','Terms'),('refund-policy.html','Purchases and refunds'))),
)
LEGAL='Trader Cockpit is research software. It does not give financial advice, and no backtest or simulation predicts future results.'
MARK='<svg class="brand-mark" aria-hidden="true" viewBox="0 0 28 25"><path d="M3 12v3m6-10v15m6-19v24m6-17v13m5-10v5"/></svg>'
KEEP_STYLES=('replay-boundary-example.css',)
OLD_SCRIPTS=r'reference-site/|research-lab|assets/generated/|home-v\d'

def read(path):
    return path.read_bytes().decode('utf-8')

def live():
    return json.loads((DOCS/'product-manifest.v1.json').read_text(encoding='utf-8'))['status']=='available'

def cta(root=''):
    """The one action on every page: the download once the app is out, the early access list until then."""
    return (f'{root}download/','Download for Windows') if live() else (f'{root}early-access.html','Get early access')

def root_of(rel):
    # 404.html is served at any depth, so its links start at the site root.
    return '/' if rel=='404.html' else '../'*rel.count('/')

def header(rel):
    root=root_of(rel);here=SECTION.get(rel.split('/')[0],'')
    links=''.join(f'<a href="{root}{href}"{" aria-current=\"page\"" if href==here else ""}>{label}</a>' for href,label in NAV)
    href,label=cta(root)
    return f'<nav class="site-nav" aria-label="Primary"><div class="nav-inner"><a class="brand" href="{root or "./"}">{MARK}Trader Cockpit</a><div class="nav-links">{links}</div><a class="btn primary small nav-cta" href="{href}">{label}</a></div></nav>'

def footer(rel):
    root=root_of(rel);href,label=cta(root)
    cols=''.join(f'<div><h2>{title}</h2><ul>'+''.join(f'<li><a href="{root}{h}">{l}</a></li>' for h,l in links)+'</ul></div>' for title,links in FOOTER)
    return f'<footer class="site-footer"><div class="footer-inner"><div class="footer-cols"><div class="footer-brand"><a class="brand" href="{root or "./"}">{MARK}Trader Cockpit</a><p>Build, backtest and stress-test trading strategies on your own PC.</p><p class="actions"><a href="{href}">{label}</a><a href="https://www.youtube.com/@Thetradercockpit" target="_blank" rel="noopener noreferrer">YouTube</a></p></div>{cols}</div><p class="footer-legal">{LEGAL}</p></div></footer>'

def meta():
    return json.loads((ROOT/'.github/product/page-meta.v1.json').read_text(encoding='utf-8'))

def text_of(html):
    return unescape(re.sub(r'<[^>]+>','',html)).strip()

def set_meta(html,rel,row):
    """Title, description and h1 from the table; every other title just takes the one separator."""
    title=row.get('title') or re.sub(r'\s+(?:—|·|\|)\s+Trader Cockpit.*$','',unescape(re.search(r'<title>(.*?)</title>',html,re.S)[1]).strip())+' | Trader Cockpit'
    if rel=='index.html' and 'title' not in row:title=unescape(re.search(r'<title>(.*?)</title>',html,re.S)[1])
    if title.count('Trader Cockpit')>1 and 'title' not in row:title=title.removesuffix(' | Trader Cockpit')
    html=re.sub(r'<title>.*?</title>',lambda m:f'<title>{e(title,quote=False)}</title>',html,count=1,flags=re.S)
    if 'description' in row:
        html=re.sub(r'<meta name="description" content="[^"]*"',lambda m:f'<meta name="description" content="{e(row["description"])}"',html,count=1)
    if 'h1' in row:
        m=re.search(r'<h1([^>]*)>(.*?)</h1>',html,re.S)
        if m and text_of(m[2])!=row['h1']:
            # The old slogan stays as the first line under the new heading on article pages.
            keep='' if rel.endswith('index.html') or rel.startswith(('learn/concepts/','support/','trust/')) else f'<p class="lede">{m[2].strip()}</p>'
            html=html[:m.start()]+f'<h1{m[1]}>{e(row["h1"],quote=False)}</h1>{keep}'+html[m.end():]
    return html

def apply(html,rel):
    root=root_of(rel)
    html=re.sub(r'<link\b[^>]*rel="stylesheet"[^>]*>',lambda m:m[0] if any(k in m[0] for k in KEEP_STYLES) else '',html)
    html=re.sub(r'<script\b[^>]*src="[^"]*(?:'+OLD_SCRIPTS+r')[^"]*"[^>]*></script>','',html)
    html=re.sub(r'<script\b[^>]*src="[^"]*assets/(?:analytics\.mjs|site-search\.js)"[^>]*></script>','',html)
    head=f'<link rel="stylesheet" href="{root}assets/site.css"><script type="module" src="{root}assets/analytics.mjs"></script>'
    html=html.replace('<!-- search-meta:start -->',head+'<!-- search-meta:start -->',1) if '<!-- search-meta:start -->' in html else html.replace('</head>',head+'</head>',1)
    html=re.sub(r'<!-- reference-(navigation|search):(start|end) -->','',html)
    html=re.sub(r'<nav class="site-nav"[^>]*>.*?</nav>',lambda m:header(rel),html,count=1,flags=re.S)
    html=re.sub(r'<footer\b[^>]*>.*?</footer>',lambda m:footer(rel),html,count=1,flags=re.S)
    html=html.replace('</body>',f'<script src="{root}assets/site-search.js" defer></script></body>',1)
    # Labels above headings, links to the removed Research Lab, and arrows after link text.
    html=re.sub(r'\s*<(span|p|div|a)\b[^>]*class="(?:[^"]* )?(?:eyebrow|kicker|visual-kicker|pp-kicker)(?: [^"]*)?"[^>]*>[^<]*</\1>','',html)
    html=re.sub(r'\s*<a\b[^>]*href="[^"]*research-lab\.html[^"]*"[^>]*>.*?</a>','',html,flags=re.S)
    html=re.sub(r'\s*(?:→|&rarr;|&#8594;)\s*</a>','</a>',html)
    # Label chips under a guide's title tell a reader nothing; worked examples keep theirs (they mark the data as made up).
    if rel.startswith(('how-to/','methods/')):html=re.sub(r'\s*<div class="article-meta">(?:\s*<span>[^<]*</span>)+\s*</div>','',html)
    return set_meta(html,rel,meta().get(rel,{}))

def page_line(path):
    """A guide's own h1 and description, so a hub never restates them."""
    html=read(path);rel=path.relative_to(DOCS).as_posix();row=meta().get(rel,{})
    h1=row.get('h1') or text_of(re.search(r'<h1[^>]*>(.*?)</h1>',html,re.S)[1])
    desc=row.get('description') or unescape(re.search(r'<meta name="description" content="([^"]*)"',html)[1])
    return h1,desc

def listing(folder,here):
    rows=''
    for p in sorted((DOCS/folder).glob('*.html')):
        if p.name=='index.html':continue
        h1,desc=page_line(p);href=p.name if folder==here else f'../{folder}/{p.name}'
        rows+=f'<li><a href="{href}"><strong>{e(h1,quote=False)}</strong><span>{e(desc,quote=False)}</span></a></li>'
    return f'<ul class="guide-list">{rows}</ul>'

def hub_main(rel):
    row=meta()[rel];here=rel.rsplit('/',1)[0];up='../'
    def group(title,folder,anchor):
        return f'<section class="guide-group" id="{anchor}"><h2>{title}</h2>{listing(folder,here)}</section>'
    if rel=='learn/index.html':
        body=('<section class="guide-group" id="start"><h2>Start here</h2><ul class="guide-list">'
              +''.join(f'<li><a href="{h}"><strong>{t}</strong><span>{d}</span></a></li>' for h,t,d in (
                  ('start-here.html','How to judge a backtest','The order to ask questions of any backtest, from the claim to what was tried before it.'),
                  ('../strategy-claim-audit-checklist.html','Backtest checklist','One page of questions to ask before you believe a published backtest.'),
                  ('glossary.html','Glossary','Backtesting terms in plain language, each linked to its full guide.'),
                  ('videos.html','Video lessons','Short lessons, each paired with a written guide.')))
              +'</ul></section>'
              +group('Concepts','learn/concepts','concepts')+group('How-to guides','how-to','how-to')+group('Methods','methods','methods')+group('Worked examples','examples','examples'))
        lead='Free guides to what a backtest can and cannot tell you.'
    elif rel=='how-to/index.html':
        body=group('Guides','how-to','guides')+f'<p class="measure">Each guide links to the idea behind it. The ideas are in <a href="{up}learn/#concepts">Concepts</a> and <a href="{up}methods/">Methods</a>.</p>'
        lead='Step-by-step guides to testing a strategy and reading the result.'
    else:
        body=group('Examples','examples','list')
        lead='Each example follows one question from the first result to its limits. The data is made up for teaching and marked as such.'
    return f'<main id="main" tabindex="-1"><div class="wrap"><header class="page-head"><h1>{e(row["h1"],quote=False)}</h1><p class="lead">{lead}</p></header>{body}</div></main>'

HUBS=('learn/index.html','how-to/index.html','examples/index.html')

def build():
    out={}
    for p in sorted(DOCS.rglob('*.html')):
        rel=p.relative_to(DOCS).as_posix();html=read(p)
        if 'http-equiv="refresh"' in html:continue
        if rel in HUBS:html=re.sub(r'<main\b.*?</main>',lambda m:hub_main(rel),html,count=1,flags=re.S)
        out[rel]=apply(html,rel)
    out['search-index.v1.json']=search_index()
    return out

def search_index():
    """Search results show each page's own h1 and description, so they can't drift from the page."""
    data=json.loads(read(DOCS/'search-index.v1.json'))
    for entry in data['entries']:
        path=entry['path']
        if '#' in path:
            entry['summary']=re.sub(r'^Product-neutral interpretation guidance for (.*)\.$',r'How to read \1.',entry['summary']);continue
        page=DOCS/(path+'index.html' if path.endswith('/') or not path else path)
        if page.is_file():entry['title'],entry['summary']=page_line(page)
    return json.dumps(data,indent=2,ensure_ascii=False)+'\n'

def main():
    check='--check' in sys.argv;stale=[]
    for rel,text in build().items():
        p=DOCS/rel
        if read(p)!=text:
            stale.append(rel)
            if not check:p.write_bytes(text.encode('utf-8'))
    if check and stale:
        print('SITE CHROME: FAIL stale: '+', '.join(stale));return 1
    print('SITE CHROME: '+('PASS' if check else f'wrote {len(stale)} pages'));return 0

if __name__=='__main__':sys.exit(main())
