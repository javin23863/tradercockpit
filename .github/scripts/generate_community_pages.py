#!/usr/bin/env python3
"""Build the Community pages from docs/community/items.v1.json.

Writes community/index.html, one page per item (community/<kind>s/<slug>/), one page per author
(community/authors/<handle>/), their sitemap entries and UX contract rows. The page shell is the
Features page's head; site_chrome gives it the same header and footer as every page.
usage: generate_community_pages.py [--check] [--import <path-or-https-url>]
"""
from datetime import date
from html import escape as e
from pathlib import Path
from urllib.parse import urlsplit
import json,re,shutil,sys,urllib.request

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import search_metadata
from site_chrome import apply as chrome,cta
from generate_product_pages import facts as product_facts,fill
ROOT=HERE.parents[1];DOCS=ROOT/'docs';COMMUNITY=DOCS/'community';ITEMS=COMMUNITY/'items.v1.json'
SITE='https://trader-cockpit.com/';SCHEMA='tc.community-items.v1'
KINDS={'strategy':'Strategies','indicator':'Indicators','idea':'Ideas'};FOLDER={'strategy':'strategies','indicator':'indicators','idea':'ideas'}
BACKTEST_NOTE='Hypothetical backtest, not actual trading. Past results don’t predict future ones. Not financial advice.'
ID=re.compile(r'[0-9a-f]{64}');HANDLE=re.compile(r'[a-z0-9-]{1,40}');IMAGE_TYPES={'image/png':'png','image/jpeg':'jpg'}
MAX_IMAGE=5_000_000

def slugify(text):return re.sub(r'[^a-z0-9]+','-',text.lower()).strip('-')[:60].strip('-')

def load():return json.loads(ITEMS.read_bytes().decode('utf-8'))['items']

def ordered(items):return sorted(items,key=lambda i:(i['published_at'],i['id']),reverse=True)

def with_paths(items):
    """Each item gets its page path; a repeated title gets the id's first 6 characters."""
    seen=set()
    for i in sorted(items,key=lambda i:i['id']):
        slug=slugify(i['title']) or i['id'][:12]
        if (i['kind'],slug) in seen:slug+='-'+i['id'][:6]
        seen.add((i['kind'],slug));i['_rel']=f'community/{FOLDER[i["kind"]]}/{slug}/index.html'
    return ordered(items)

def day(value):
    d=date.fromisoformat(value[:10]);return f'{d.day} {d:%b %Y}'

def url_of(rel):return rel.removesuffix('index.html')

def link_text(text):
    """Plain text with newlines kept; https links become links."""
    return re.sub(r'https://[^\s<>"]+',lambda m:f'<a href="{m[0]}" rel="nofollow ugc noopener">{m[0]}</a>',e(text)).replace('\n','<br>')

def where(i):return ' · '.join(x for x in (i.get('market'),i.get('timeframe')) if x)

def shell(rel,title,desc,main):
    """The Features page with this page's title, description, canonical, root path and <main>."""
    t=(DOCS/'features/index.html').read_bytes().decode('utf-8')
    root='../'*rel.count('/')
    t=re.sub(r'<!-- search-meta:start -->.*?<!-- search-meta:end -->','',t,flags=re.S)
    t=t.replace('href="../',f'href="{root}').replace('src="../',f'src="{root}')
    t=re.sub(r'<title>.*?</title>',lambda m:f'<title>{e(title,quote=False)}</title>',t,count=1,flags=re.S)
    t=re.sub(r'<meta name="description" content="[^"]*">',lambda m:f'<meta name="description" content="{e(desc)}">',t,count=1)
    t=re.sub(r'<link rel="canonical" href="[^"]*">',lambda m:f'<link rel="canonical" href="{SITE}{url_of(rel)}">',t,count=1)
    t=re.sub(r'<main id="main".*?</main>',lambda m:main,t,count=1,flags=re.S)
    return search_metadata.apply(chrome(t,rel),rel)

def href(frm,rel):return '../'*frm.count('/')+url_of(rel)

def card(i,frm):
    pic=f'<figure class="shot"><img src="{href(frm,"community/"+i["image"])}" alt="" loading="lazy"></figure>' if i.get('image') else ''
    meta=where(i) or (f'Pine indicator, {i["indicator"]["licence"]}' if i['kind']=='indicator' and i.get('indicator',{}).get('licence') else '')
    return f'<li><a href="{href(frm,i["_rel"])}">{pic}<strong>{e(i["title"])}</strong><span>by {e(i["author"]["name"])}'+(f'. {e(meta)}' if meta else '')+'</span></a></li>'

def note(kind,frm):
    """The web shows a few of the app's indicators; the count of all of them comes from capabilities.v1.json."""
    if kind!='indicator' or frm!='community/index.html':return ''
    return '<p class="measure">'+e(fill('The Community inside the app has {communityIndicators} open-source indicators, each with a picture of what it draws. These are a few to read on the web.',product_facts()))+'</p>'

def sections(items,frm,level='h2'):
    out=''
    for kind,name in KINDS.items():
        rows=[i for i in items if i['kind']==kind]
        if rows:out+=f'<section class="guide-group" id="{FOLDER[kind]}" aria-labelledby="h-{FOLDER[kind]}"><{level} id="h-{FOLDER[kind]}">{name} ({len(rows)})</{level}>{note(kind,frm)}<ul class="guide-list{" pictures" if rows[0].get("image") else ""}">'+''.join(card(i,frm) for i in rows)+'</ul></section>'
    return out

def index_page(items):
    rel='community/index.html'
    jump=''.join(f'<a href="#{FOLDER[k]}">{n}</a>' for k,n in KINDS.items() if any(i['kind']==k for i in items))
    go,label=cta('../')
    main=f'<main id="main" tabindex="-1"><div class="wrap"><header class="page-head"><h1>Strategies, indicators and ideas.</h1><p class="lead">Study the rules and backtest behind a strategy, read an indicator’s Pine code, and open them in Trader Cockpit. Research, not financial advice, and no result is promised.</p><div class="actions"><a class="btn primary" href="{go}">{label}</a></div></header>{sections(items,rel)}</div></main>'
    return rel,shell(rel,'Trading Strategies and Pine Indicators | Trader Cockpit Community','Trading strategies with their rules and backtests, open-source Pine indicators, and ideas, to study and open in Trader Cockpit.',main)

def facts(rows):return '<dl class="kv">'+''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k,v in rows if v is not None)+'</dl>'

def num(v,fmt,sign=False):return None if v is None else (('+' if sign and v>0 else '')+format(v,fmt))

def body(i):
    if i['kind']=='strategy':
        s=i['strategy']
        grade=f'<p class="cm-grade"><span>{e(s["grade"])}</span>{e(s.get("headline") or "")}</p>' if s.get('grade') else ''
        span=f'{day(s["from"])} to {day(s["to"])}' if s.get('from') and s.get('to') else None
        rows=[('Trades',None if s.get('trades') is None else str(s['trades'])),('Net',num(s.get('net_pct'),'.1f',True) and num(s.get('net_pct'),'.1f',True)+'%'),('Profit factor',num(s.get('profit_factor'),'.2f')),
              ('Win rate',num(s.get('win_rate_pct'),'.2f') and num(s.get('win_rate_pct'),'.2f')+'%'),('Max drawdown',num(s.get('max_drawdown_pct'),'.2f') and num(s.get('max_drawdown_pct'),'.2f')+'%'),('Tested',span)]
        rules=''.join(f'<li>{e(r)}</li>' for r in s.get('rules',[]))
        return f'{grade}{facts(rows)}<p class="micro">{BACKTEST_NOTE}</p><h2>Rules</h2><ul class="ticks">{rules}</ul>'
    if i['kind']=='indicator':
        x=i['indicator']
        rows=[('Licence',x.get('licence')),('Version',x.get('version')),('Uses',str(x['use_count']) if x.get('use_count') else None)]
        return f'{facts(rows)}<h2>Pine code</h2><p>In Trader Cockpit, open Community and press Add to chart. This is the code it runs.</p><pre><code>{e(x["code"])}</code></pre>'
    return f'<h2>Note</h2><p>{link_text(i["idea"]["note"])}</p>'

def described(i):
    text=i.get('description','')
    if 'micro index futures' in text and '. The picture shows' in text:
        text=text.replace('. The picture shows','. Micro contracts began trading in 2019, so the years before that are not the micro contracts’ own prices. The picture shows',1)
    return text

def item_page(i):
    rel=i['_rel'];root='../'*rel.count('/')
    a=i['author'];pic=f'<figure class="shot"><img src="{root}community/{e(i["image"])}" alt="{e(i["title"])}"></figure>' if i.get('image') else ''
    meta=''.join(f'<span>{e(v)}</span>' for v in (day(i['published_at']),where(i)) if v)
    go,label=cta(root)
    main=(f'<main id="main" tabindex="-1"><div class="wrap"><header class="page-head"><p class="breadcrumb"><a href="{root}community/#{FOLDER[i["kind"]]}">{KINDS[i["kind"]]}</a></p><h1>{e(i["title"])}</h1>'
          f'<p class="lead">{link_text(described(i))}</p><p class="article-meta"><span>by <a href="{href(rel,author_rel(a))}">{e(a["name"])}</a></span>{meta}</p>'
          f'<div class="actions"><a class="btn primary" href="{go}">{label}</a></div></header><div class="prose">{pic}{body(i)}</div></div></main>')
    # The description is the item's own first sentence, so each page's preview says what it is.
    first=re.split(r'(?<=[.!?])\s',i.get('description','').replace('\n',' ').strip())[0][:155] or f'{i["title"]} on Trader Cockpit Community.'
    return rel,shell(rel,i['title']+(': Pine Indicator' if i['kind']=='indicator' else ': Strategy and Backtest' if i['kind']=='strategy' else '')+' | Trader Cockpit',first,main)

def author_rel(a):return f'community/authors/{a["handle"]}/index.html'

def author_page(handle,items):
    a=items[0]['author'];rel=author_rel(a)
    main=f'<main id="main" tabindex="-1"><div class="wrap"><header class="page-head"><p class="breadcrumb"><a href="../../">Community</a></p><h1>{e(a["name"])}</h1><p class="lead">{len(items)} published.</p></header>{sections(items,rel)}</div></main>'
    return rel,shell(rel,f'Published by {a["name"]} | Community',f'Strategies, indicators and ideas by {a["name"]} on Trader Cockpit Community.',main)

def sitemap(rels):
    """sitemap.xml with exactly these community URLs, dated the way search_metadata dates every URL."""
    t=(DOCS/'sitemap.xml').read_bytes().decode('utf-8')
    t=re.sub(r'  <url>\n    <loc>'+re.escape(SITE)+r'community/[^<]*</loc>.*?</url>\n','',t,flags=re.S)
    t=t.replace('</urlset>',''.join(f'  <url>\n    <loc>{SITE}{url_of(r)}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.6</priority>\n  </url>\n' for r in rels)+'</urlset>')
    return search_metadata.sitemap(search_metadata.config(),t)

def build():
    items=with_paths(load());out={}
    pages=[index_page(items)]+[item_page(i) for i in items]
    handles={}
    for i in items:handles.setdefault(i['author']['handle'],[]).append(i)
    pages+=[author_page(h,rows) for h,rows in sorted(handles.items())]
    for rel,text in pages:out[rel]=text
    out['sitemap.xml']=sitemap([r for r,_ in pages])
    return out

def contracts():
    from reference_contracts import refresh_contracts,serialize_contracts
    readiness=json.loads((ROOT/'.github/website-reference-readiness.json').read_bytes().decode('utf-8'))
    ok=readiness.get('gates',{}).get('owner_visual_acceptance_of_integrated_result')=='complete; owner approved exact integrated visual candidate on 2026-09-18'
    base=json.loads((ROOT/'.github/reference-site/ux-contracts-before.json').read_bytes().decode('utf-8'))
    return serialize_contracts(refresh_contracts(base,owner_visual_approval=ok,approved_at='2026-09-18' if ok else None))

# --import: the account service's GET /v1/community/items response, merged by id. A remote import is the service's whole
# approved list, so service items missing from it (unpublished) leave the site; our own seed items stay.
def check_item(i):
    """Validate one service item at the trust boundary; returns the item as the site stores it."""
    def need(ok,why):
        if not ok:raise ValueError(f'item {i.get("id")!r}: {why}')
    need(isinstance(i.get('id'),str) and ID.fullmatch(i['id']),'id must be 64 lowercase hex')
    need(i.get('kind') in KINDS,'unknown kind')
    need(isinstance(i.get('title'),str) and 0<len(i['title'].strip())<=120,'title')
    need(isinstance(i.get('description',''),str) and len(i.get('description',''))<=4000,'description')
    a=i.get('author') or {}
    need(isinstance(a.get('name'),str) and 0<len(a['name'])<=60 and isinstance(a.get('handle'),str) and HANDLE.fullmatch(a['handle']),'author')
    need(isinstance(i.get('published_at'),str) and re.fullmatch(r'\d{4}-\d\d-\d\dT[0-9:.]+Z',i['published_at']),'published_at')
    for k in ('market','timeframe'):need(i.get(k) is None or isinstance(i[k],str) and len(i[k])<=(80 if k=='market' else 40),k)
    need(isinstance(i.get(i['kind']),dict),'missing '+i['kind']+' block')
    if i['kind']=='idea':need(isinstance(i['idea'].get('note'),str) and len(i['idea']['note'])<=2000,'note')
    if i['kind']=='indicator':need(isinstance(i['indicator'].get('code'),str),'code')
    if i['kind']=='strategy':need(isinstance(i['strategy'].get('rules',[]),list) and all(isinstance(r,str) for r in i['strategy'].get('rules',[])),'rules')
    keep={k:i.get(k) for k in ('id','kind','title','description','author','published_at','market','timeframe')}
    keep['author']={'name':a['name'],'handle':a['handle']};keep[i['kind']]=i[i['kind']];keep['from_service']=True
    return keep

def fetch(url,limit):
    with urllib.request.urlopen(url,timeout=30) as r:
        body=r.read(limit+1)
        if len(body)>limit:raise ValueError('response too large: '+url)
        return body,r.headers.get_content_type()

def import_items(source):
    remote=source.startswith('https://')
    if not remote and re.match(r'[a-z]+://',source):raise SystemExit('Import from an https URL or a local file')
    raw=fetch(source,20_000_000)[0] if remote else Path(source).read_bytes()
    data=json.loads(raw.decode('utf-8'))
    if data.get('schema')!=SCHEMA or not isinstance(data.get('items'),list):raise SystemExit('Not a '+SCHEMA+' response')
    current={i['id']:i for i in load() if not (remote and i.get('from_service'))};img=COMMUNITY/'img';img.mkdir(exist_ok=True)
    imported=0
    for row in data['items']:
        try:item=check_item(row)
        except ValueError as why:print(f'COMMUNITY: skipped {why}');continue
        path=row.get('image');item['image']=None
        if remote and isinstance(path,str) and path==f'/v1/community/items/{item["id"]}/image':
            s=urlsplit(source);blob,kind=fetch(f'{s.scheme}://{s.netloc}{path}',MAX_IMAGE)
            if kind not in IMAGE_TYPES:print(f'COMMUNITY: skipped item {item["id"]!r}: image type {kind}');continue
            name=f'img/{item["id"]}.{IMAGE_TYPES[kind]}';(COMMUNITY/name).write_bytes(blob);item['image']=name
        elif not remote and isinstance(path,str) and re.fullmatch(r'img/[0-9a-f]{64}\.(png|jpg)',path) and (Path(source).parent/path).is_file():
            # shortcut: a local file keeps its image only when it sits beside an img/ folder, as the site's own file does
            if (Path(source).parent/path).resolve()!=(COMMUNITY/path).resolve():shutil.copyfile(Path(source).parent/path,COMMUNITY/path)
            item['image']=path
        current[item['id']]=item;imported+=1
    items=[{k:v for k,v in i.items() if not k.startswith('_')} for i in ordered(list(current.values()))]
    ITEMS.write_text(json.dumps({'schema':SCHEMA,'items':items},indent=1,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
    return imported

def main(argv=sys.argv[1:]):
    if '--import' in argv:
        print(f'COMMUNITY: imported {import_items(argv[argv.index("--import")+1])} items')
    check='--check' in argv;stale=[]
    out=build()
    for old in COMMUNITY.rglob('index.html'):
        rel=old.relative_to(DOCS).as_posix()
        if rel not in out:
            stale.append(rel)
            if not check:old.unlink()
    for name,text in out.items():
        p=DOCS/name
        if not p.is_file() or p.read_bytes().decode('utf-8')!=text:
            stale.append(name)
            if not check:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode('utf-8'))
    # The UX contract file lists every public page, so it follows the pages written above.
    ux=ROOT/'.github/product/ux-page-contracts.v1.json'
    if ux.read_bytes()!=contracts():
        stale.append('.github/product/ux-page-contracts.v1.json')
        if not check:ux.write_bytes(contracts())
    if check and stale:
        print('COMMUNITY PAGES: FAIL stale: '+', '.join(stale));return 1
    print('COMMUNITY PAGES: '+('PASS' if check else f'wrote {len(stale)} files'));return 0

if __name__=='__main__':sys.exit(main())
