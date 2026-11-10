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
    return f'''<main id="main" tabindex="-1"><div class="pp-page"><header class="pp-head"><span class="pp-kicker">Features</span><h1>Everything TraderCockpit does.</h1><p class="pp-lead">Every part of the Windows app, in plain words. Research tools, not financial advice, and no result is promised.</p><div class="pp-actions"><a class="pp-btn gold" href="../download/">Download for Windows{ARROW}</a><a class="pp-btn" href="../pricing/">See the plans{ARROW}</a></div></header><nav class="pp-index" aria-label="Feature areas">{index}</nav>{sections}</div></main>'''

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
    return f'''<main id="main" tabindex="-1"><div class="pp-page"><header class="pp-head"><span class="pp-kicker">Pricing</span><h1>A Free plan and four monthly plans. One research environment.</h1><p class="pp-lead">Every paid plan includes everything listed here. They differ only in included Apollo credits and how many jobs run at once. Start on Free. A paid plan starts inside the app, under Settings › Plan & billing.</p><div class="article-meta"><span>Monthly USD</span><span>Windows desktop</span><span id="pricing-product-state">Checking availability</span></div></header><div class="pp-cards" id="pricing-current-tier">{cards}</div><section class="pp-compare" aria-labelledby="compare-title"><h2 id="compare-title">Compare plans</h2><div class="pp-table"><table><thead><tr><th scope="col">Area</th>{heads}</tr></thead><tbody>{rows}</tbody></table></div><p class="micro">“Part” means some of that area is in the Free plan; open Free below for exactly what’s in it.</p></section><section class="pp-details" aria-label="What each plan includes"><h2>What each plan includes</h2>{details}</section><section class="pp-note"><h2>Before you choose</h2><p>TraderCockpit is research software. No plan can make a historical result predict the future or guarantee returns. <a href="../trust/">Trust and evidence{ARROW}</a></p><a class="pp-btn gold" href="../download/">Download for Windows{ARROW}</a></section></div></main>'''

def home_main(data):
    by={a['id']:a for a in data['areas']}
    def split(a,flip):
        items=''.join(f'<li>{e(i)}</li>' for i in a['items'][:4])
        return f'<section class="pp-area{" flip" if flip else ""}" id="{a_id(a)}" aria-labelledby="h-{a_id(a)}"><div class="pp-copy"><span class="pp-kicker">{e(a["kicker"])}</span><h2 id="h-{a_id(a)}">{e(a["title"])}</h2><p class="pp-lead">{e(a["lead"])}</p><ul class="pp-list">{items}</ul><a class="pp-more" href="features/#{a_id(a)}">All of {e(a["title"])}{ARROW}</a></div>{figure(a,"")}</section>'
    shown=[a for a in data['areas'] if a.get('image')]
    sections=''.join(split(a,i%2==1) for i,a in enumerate(shown))
    cards=''.join(f'<a class="pp-tile" href="features/#{a_id(a)}"><span class="pp-kicker">{e(a["kicker"])}</span><strong>{e(a["title"])}</strong><span>{e(a["lead"])}</span></a>' for a in data['areas'] if not a.get('image') and a['id']!='brokers')
    index=''.join(f'<a href="features/#{a_id(a)}">{e(a["title"])}</a>' for a in data['areas'])
    strong=''.join(f'<a class="pp-tile" href="compare/"><strong>{e(s["title"])}</strong><span>{e(s["text"])}</span></a>' for s in data['strengths'])
    plans=''.join(f'<a class="pp-mini" href="pricing/#plan-{e(p["id"])}"><strong>{e(p["name"])}</strong><span>{plan_price(p)}</span></a>' for p in data['plans'])
    return f'''<main id="main" tabindex="-1">
<section class="hero" id="top" aria-labelledby="hero-title"><div class="pp-hero-copy"><h1 id="hero-title" tabindex="-1">Build a trading strategy. Find out if it holds up.</h1><p class="pp-lead">TraderCockpit is a Windows research app. Search for strategies on real market data, put them through robustness checks, chart them, and practice on paper. Research tools, not financial advice, and no result is promised.</p><div class="actions"><a class="button gold" href="download/">Download for Windows</a><a class="button glass" href="features/">See every feature</a></div></div><figure class="pp-hero-shot"><img src="assets/features/paper.webp" alt="TraderCockpit Charts on Coinbase BTC/USD hourly bars with a paper order ticket and trade history" fetchpriority="high"><figcaption>The app, on live Coinbase BTC/USD prices.</figcaption></figure></section>
<div class="pp-page"><section class="pp-guides" id="strongest" aria-labelledby="strongest-title"><div><span class="pp-kicker">Why TraderCockpit</span><h2 id="strongest-title">Where TraderCockpit is strongest</h2><p>No platform is best at everything. These four are where we aim to be the best choice.</p></div><div class="pp-actions"><a class="pp-btn" href="compare/">How we compare with the others{ARROW}</a></div></section><section class="pp-tiles" aria-label="Where TraderCockpit is strongest">{strong}</section></div>
<nav class="pp-index" aria-label="What TraderCockpit does">{index}</nav>
<div class="pp-page">{sections}{broker_section(by['brokers'],data)}<section class="pp-tiles" aria-label="More of what it does">{cards}</section>
<section class="pp-home-plans" id="pricing" aria-labelledby="pricing-title"><div><span class="pp-kicker">Pricing</span><h2 id="pricing-title">A Free plan and four monthly plans</h2><p class="pp-lead">Every paid plan includes every feature. Click a plan to see everything that comes with it. Start on Free; a paid plan starts inside the app.</p></div><div class="pp-minis">{plans}</div></section>
<section class="pp-guides" id="learning"><div><span class="pp-kicker">Keep learning</span><h2>Guides to testing a strategy honestly</h2><p>Out-of-sample testing, Monte Carlo, walk-forward and the ways a backtest can mislead you.</p></div><div class="pp-actions"><a class="pp-btn" href="learn/" data-journey="#/learn">Read the guides{ARROW}</a><a class="pp-btn" href="strategy-claim-audit-checklist.html">Open the backtest checklist{ARROW}</a></div></section></div>
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
