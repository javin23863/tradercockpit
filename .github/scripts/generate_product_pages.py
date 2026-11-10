#!/usr/bin/env python3
"""Build Features, Pricing and the homepage body from .github/product/capabilities.v1.json.

Plan prices come from docs/commerce-public.v1.json and brokers from .github/product/brokers.v1.json, so the three pages can't disagree.
usage: generate_product_pages.py [--check]
"""
from html import escape as e
from pathlib import Path
import json,re,sys

ROOT=Path(__file__).resolve().parents[2];DOCS=ROOT/'docs';PRODUCT=ROOT/'.github/product'
ARROW=' →'

def price_text(cents):
    return '$'+format(cents/100,'.2f').removesuffix('.00')

def broker_groups():
    """Orders proven from the chart and see your account, each A to Z."""
    trade,read=[],[]
    brokers=json.loads((PRODUCT/'brokers.v1.json').read_text(encoding='utf-8'))
    for key,row in brokers['institutions'].items():
        routes=row['routes'];name=row['name']
        label=f'{name} Paper' if list(routes)==['paper'] else f'{name} (with paper)' if 'paper' in routes else name
        (trade if key in brokers['chartOrders'] else read).append(label)
    tested=[]
    if set(brokers['chartOrders'])!=set(brokers['chartOrdersTested']):
        tested=[f"{brokers['institutions'][k]['name']} Paper" for k in brokers['chartOrdersTested']]
    return [sorted(g,key=str.casefold) for g in (trade,read,tested)]

def orders_note(tested):
    return (f'Tested with real orders on a paper account: {", ".join(tested)}. ' if tested else '')+'Paper trading with no broker account is on every chart.'

def load():
    data=json.loads((PRODUCT/'capabilities.v1.json').read_text(encoding='utf-8'))
    data['live']=json.loads((DOCS/'product-manifest.v1.json').read_text(encoding='utf-8'))['status']=='available'
    trade,read,tested=broker_groups()
    opened=len(trade)+len(read)
    data['brokers']={'trade':trade,'read':read,'open':opened,'note':orders_note(tested)}
    for area in data['areas']:
        if area['id']=='brokers':
            area['lead']=f'{opened} brokers connect to TraderCockpit, and your account activity comes into your Journal.'
            area['items']=[area['how'],f'Orders from the chart: {", ".join(trade)}. {data["brokers"]["note"]}',f'See your account: {", ".join(read)}.']
    data['paidByArea']['brokers']=f'{opened} brokers'
    for plan in data['plans']:
        if 'excluded' in plan:plan['excluded']=[i.replace('{brokers}',str(opened)) for i in plan['excluded']]
    tiers={t['name']:t['unitAmount'] for t in json.loads((DOCS/'commerce-public.v1.json').read_text(encoding='utf-8'))['tiers']}
    for plan in data['plans']:
        if plan['id']!='free':plan['price']=tiers.pop(plan['commerce'])
    packs=', '.join(f'{price_text(p["priceCents"])} buys {p["credits"]:,} credits' for p in data['creditPacks'])
    data['paidLimits']+=[['Apollo limit per run',f'{data["runLimitCredits"]:,} credits'],['Credit packs',packs]]
    for plan in data['plans']:
        if plan['id']!='free':plan['facts']=[['Apollo credits a month',f'{plan["credits"]:,}'],['Jobs at once',str(plan['jobs'])],['Models batch size',str(plan['modelsBatch'])]]
    if tiers:raise SystemExit('Plans missing from capabilities.v1.json: '+', '.join(tiers))
    return data

def figure(area,root):
    if not area.get('image'):return ''
    return f'<figure class="pp-shot"><img src="{root}{e(area["image"])}" alt="{e(area["alt"])}" loading="lazy"><figcaption>{e(area["caption"])}</figcaption></figure>'

def broker_list(title,names,note):
    return f'<div class="pp-broker-group"><h3>{e(title)} <span>{len(names)}</span></h3><p>{e(note)}</p><ul>'+''.join(f'<li>{e(n)}</li>' for n in names)+'</ul></div>'

def broker_section(area,data):
    b=data['brokers']
    lists=broker_list('Orders from the chart',b['trade'],f'Place orders from the chart, and see your positions, balances and orders. {b["note"]}')+broker_list('See your account',b['read'],'See your positions, balances and orders.')
    return f'<section class="pp-brokers" id="{a_id(area)}" aria-labelledby="h-{a_id(area)}"><span class="pp-kicker">{e(area["kicker"])}</span><h2 id="h-{a_id(area)}">{e(area["title"])}</h2><p class="pp-lead">{e(area["lead"])}</p><p class="pp-broker-how">{e(area["how"])}</p><div class="pp-broker-groups">{lists}</div></section>'

def features_main(data):
    index=''.join(f'<a href="#{a["id"]}">{e(a["title"])}</a>' for a in data['areas'])
    sections=''
    for area in data['areas']:
        if area['id']=='brokers':
            sections+=broker_section(area,data);continue
        items=''.join(f'<li>{e(i)}</li>' for i in area['items'])
        sections+=f'<section class="pp-area{"" if area.get("image") else " pp-text"}" id="{a_id(area)}"><div class="pp-copy"><span class="pp-kicker">{e(area["kicker"])}</span><h2>{e(area["title"])}</h2><p class="pp-lead">{e(area["lead"])}</p><ul class="pp-list">{items}</ul></div>{figure(area,"../")}</section>'
    return f'''<main id="main" tabindex="-1"><div class="pp-page"><header class="pp-head"><span class="pp-kicker">Features</span><h1>Everything TraderCockpit does.</h1><p class="pp-lead">Every part of the Windows app, in plain words. Research tools, not financial advice, and no result is promised.</p><div class="pp-actions"><a class="pp-btn gold" href="../early-access.html">Join the early access list{ARROW}</a><a class="pp-btn" href="../pricing/">See the plans{ARROW}</a></div></header><nav class="pp-index" aria-label="Feature areas">{index}</nav>{sections}</div></main>'''

def a_id(area):return e(area['id'])

def plan_price(plan):
    return '$0<span> / month</span>' if not plan['price'] else f'{price_text(plan["price"])}<span> / month</span>'

def facts_table(rows):
    return '<dl class="pp-facts">'+''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k,v in rows)+'</dl>'

def plan_details(plan,data):
    if plan['id']=='free':
        body=facts_table(plan['facts'])+'<div class="pp-columns"><div><h3>Included</h3><ul class="pp-list yes">'+''.join(f'<li>{e(i)}</li>' for i in plan['included'])+'</ul></div><div><h3>On the paid plans</h3><ul class="pp-list no">'+''.join(f'<li>{e(i)}</li>' for i in plan['excluded'])+'</ul></div></div>'
    else:
        groups=''.join(f'<div class="pp-group"><h4><a href="../features/#{a_id(a)}">{e(a["title"])}</a></h4><ul class="pp-list">'+''.join(f'<li>{e(i)}</li>' for i in a['items'])+'</ul></div>' for a in data['areas'])
        body=facts_table(plan['facts']+data['paidLimits'])+f'<h3>Everything that comes with {e(plan["name"])}</h3><div class="pp-groups">{groups}</div>'
    return f'<details class="pp-plan" id="plan-{e(plan["id"])}"><summary><span class="pp-plan-name">{e(plan["name"])}</span><span class="pp-plan-price">{plan_price(plan)}</span><span class="pp-plan-sum">{e(plan["summary"])}</span><span class="pp-plan-open">What’s included</span></summary><div class="pp-plan-body">{body}</div></details>'

def pricing_main(data):
    cards=''
    for plan in data['plans']:
        attr='' if plan['id']=='free' else f' data-access-plan="{e(plan["commerce"])}"'
        facts=''.join(f'<li><span>{e(k)}:</span> {e(v)}</li>' for k,v in plan['facts'][:3])
        cards+=f'<article class="pp-card{" pp-free" if plan["id"]=="free" else ""}"><h2>{e(plan["name"])}</h2><p class="pp-price">{plan_price(plan)}</p><p class="pp-card-sum">{e(plan["summary"])}</p><ul class="pp-card-facts">{facts}</ul><a class="pp-btn{"" if plan["id"]=="free" else " gold"}" href="#plan-{e(plan["id"])}"{attr}>What’s included{ARROW}</a></article>'
    details=''.join(plan_details(p,data) for p in data['plans'])
    rows=''
    paid=[p for p in data['plans'] if p['id']!='free']
    for area in data['areas']:
        f=data['freeByArea'].get(area['id'],'—')
        rows+=f'<tr><th scope="row"><a href="../features/#{a_id(area)}">{e(area["title"])}</a></th><td>{f}</td>'+f'<td>{e(data["paidByArea"].get(area["id"],"Yes"))}</td>'*len(paid)+'</tr>'
    heads=''.join(f'<th scope="col">{e(p["name"])}</th>' for p in data['plans'])
    return f'''<main id="main" tabindex="-1"><div class="pp-page"><header class="pp-head"><span class="pp-kicker">Pricing</span><h1>A Free plan and four monthly plans. One research environment.</h1><p class="pp-lead">Every paid plan includes everything listed here. They differ only in included Apollo credits and how many jobs run at once. TraderCockpit is in early access, so checkout isn’t open yet.</p><div class="article-meta"><span>Monthly USD</span><span>Windows desktop</span><span id="pricing-product-state">Checking availability</span></div></header><div class="pp-cards" id="pricing-current-tier">{cards}</div><section class="pp-compare" aria-labelledby="compare-title"><h2 id="compare-title">Compare plans</h2><div class="pp-table"><table><thead><tr><th scope="col">Area</th>{heads}</tr></thead><tbody>{rows}</tbody></table></div><p class="micro">“Part” means some of that area is in the Free plan; open Free below for exactly what’s in it.</p></section><section class="pp-details" aria-label="What each plan includes"><h2>What each plan includes</h2>{details}</section><section class="pp-note"><h2>Before you choose</h2><p>TraderCockpit is research software. No plan can make a historical result predict the future or guarantee returns. <a href="../trust/">Trust and evidence{ARROW}</a></p><a class="pp-btn gold" href="../early-access.html">Join the early access list{ARROW}</a></section></div></main>'''

# The one action on every product page: the download once the app is out, the early access list until then.
def cta(data,root=''):
    return (f'{root}download/','Download for Windows') if data['live'] else (f'{root}early-access.html','Join the early access list')

# Home's four bands: what the app is best at, each with one screen. (title, text, area the link opens, image, alt)
HOME_BANDS=[
    ('Search without code','Pick a market and set your costs. Builder builds and backtests thousands of strategies and keeps the ones that pass your rules.','builder','assets/features/builder.webp','Builder’s setup: a market, its costs and the rules a strategy must pass'),
    ('Break it before you trade it','Ready-made workflows run out-of-sample periods, other markets, slippage, Monte Carlo and walk-forward on their own. You see why each strategy dropped out.','workflows','assets/features/workflows.webp','A workflow’s steps, each with the strategies it kept and dropped'),
    ('It runs on your PC','Your strategies, results and data stay in your own folder. Searches and backtests run on your computer, with no meter on them.','results','assets/features/results.webp','A strategy’s results: verdict, equity and trades'),
    ('Take it with you','Export a strategy as Pine for TradingView, or as MetaTrader, EasyLanguage or Python code.','exports','assets/features/export.webp','A strategy’s code, ready to export'),
]

def home_main(data):
    by={a['id']:a for a in data['areas']}
    href,label=cta(data)
    def band(i,row):
        title,text,area,image,alt=row
        return f'<section class="pp-band{" flip" if i%2 else ""}" aria-labelledby="band-{area}"><div class="pp-copy"><h2 id="band-{area}">{e(title)}</h2><p class="pp-lead">{e(text)}</p><a class="pp-more" href="features/#{area}">{e(by[area]["title"])}{ARROW}</a></div><figure class="pp-shot"><img src="{image}" alt="{e(alt)}" loading="lazy"></figure></section>'
    bands=''.join(band(i,row) for i,row in enumerate(HOME_BANDS))
    def pair(area,title,text):
        a=by[area]
        return f'<a class="pp-duo" href="features/#{area}"><img src="{e(a["image"])}" alt="{e(a["alt"])}" loading="lazy"><strong>{e(title)}</strong><span>{e(text)}</span></a>'
    duo=pair('charts','Charts','Seventeen chart types, more than a thousand indicators, drawings, footprint and profiles, and your own Pine scripts.')+pair('apollo','Apollo','Describe an idea. Apollo turns it into a strategy you can test, and asks before it changes anything.')
    index=''.join(f'<a href="features/#{a_id(a)}">{e(a["title"])}</a>' for a in data['areas'])
    plans=''.join(f'<a class="pp-mini" href="pricing/#plan-{e(p["id"])}"><strong>{e(p["name"])}</strong><span>{plan_price(p)}</span></a>' for p in data['plans'])
    return f'''<main id="main" tabindex="-1">
<section class="hero" id="top" aria-labelledby="hero-title"><div class="pp-hero-copy"><h1 id="hero-title" tabindex="-1">Find strategies that hold up.</h1><p class="pp-lead">Trader Cockpit searches thousands of rule combinations on your market, then tries to break the ones it keeps. On your PC, with no code.</p><div class="actions"><a class="button gold" href="{href}">{label}</a><a class="button glass" href="features/">See every feature</a></div></div><figure class="pp-hero-shot"><img src="assets/features/hero.webp" alt="Trader Cockpit’s Builder during a strategy search, with the strategies it has kept so far" fetchpriority="high"></figure></section>
<div class="pp-page">{bands}
<section class="pp-duos" aria-label="Charts and Apollo">{duo}</section>
<section class="pp-guides" id="community"><div><h2>Community</h2><p>Indicators and strategies other traders have published. Open one on your chart or in Builder with a click.</p></div><div class="pp-actions"><a class="pp-btn" href="community/">Browse the community{ARROW}</a></div></section>
<section class="pp-home-plans" id="pricing" aria-labelledby="pricing-title"><div><h2 id="pricing-title">A Free plan and four monthly plans</h2><p class="pp-lead">Every paid plan includes every feature.{"" if data["live"] else " Checkout isn’t open yet."}</p></div><div class="pp-minis">{plans}</div></section>
<section class="pp-all" aria-labelledby="all-title"><h2 id="all-title">Everything in the app</h2><nav class="pp-index" aria-label="What Trader Cockpit does">{index}</nav></section>
<section class="pp-guides" id="learning"><div><h2>Guides to testing a strategy honestly</h2><p>Out-of-sample testing, Monte Carlo, walk-forward and the ways a backtest can mislead you.</p></div><div class="pp-actions"><a class="pp-btn" href="learn/" data-journey="#/learn">Read the guides{ARROW}</a><a class="pp-btn" href="strategy-claim-audit-checklist.html">Open the backtest checklist{ARROW}</a></div></section></div>
</main>'''

def build():
    data=load()
    out={}
    features=(DOCS/'features/index.html').read_text(encoding='utf-8')
    out['features/index.html']=re.sub(r'<main id="main".*?</main>',lambda m:features_main(data),features,count=1,flags=re.S)
    pricing=(DOCS/'pricing/index.html').read_text(encoding='utf-8')
    out['pricing/index.html']=re.sub(r'<main id="main".*?</main>',lambda m:pricing_main(data),pricing,count=1,flags=re.S)
    manifest=json.loads((DOCS/'product-manifest.v1.json').read_text(encoding='utf-8'))
    manifest['verifiedCapabilities']=[{'id':a['id'],'label':a['title'],'summary':a['lead']} for a in data['areas']]
    manifest['brokers']={'connectable':data['brokers']['open'],'tradeFromChart':len(data['brokers']['trade']),'seeAccount':len(data['brokers']['read'])}
    out['product-manifest.v1.json']=json.dumps(manifest,indent=2,ensure_ascii=False)+'\n'
    home=(DOCS/'index.html').read_text(encoding='utf-8')
    out['index.html']=re.sub(r'<main id="main".*?</main>',lambda m:home_main(data),home,count=1,flags=re.S)
    return out

def main():
    check='--check' in sys.argv
    stale=[]
    for name,text in build().items():
        p=DOCS/name
        if p.read_text(encoding='utf-8')!=text:
            stale.append(name)
            if not check:p.write_bytes(text.encode('utf-8'))
    if check and stale:
        print('PRODUCT PAGES: FAIL stale: '+', '.join(stale));return 1
    print('PRODUCT PAGES: '+('PASS' if check else f'wrote {len(stale)} pages'));return 0

if __name__=='__main__':sys.exit(main())
