#!/usr/bin/env python3
"""Build Features, Pricing and the homepage from .github/product/capabilities.v1.json.

Plan prices come from docs/commerce-public.v1.json and brokers from .github/product/brokers.v1.json, so the three pages can't disagree.
usage: generate_product_pages.py [--check]
"""
from html import escape as e
from pathlib import Path
import json,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from site_chrome import apply,cta,read

ROOT=Path(__file__).resolve().parents[2];DOCS=ROOT/'docs';PRODUCT=ROOT/'.github/product'

def price_text(cents):
    return '$'+format(cents/100,'.2f').removesuffix('.00')

def broker_groups():
    """Orders proven from the chart and see your account, each A to Z."""
    trade,seen=[],[]
    brokers=json.loads(read(PRODUCT/'brokers.v1.json'))
    for key,row in brokers['institutions'].items():
        routes=row['routes'];name=row['name']
        label=f'{name} Paper' if list(routes)==['paper'] else f'{name} (with paper)' if 'paper' in routes else name
        (trade if key in brokers['chartOrders'] else seen).append(label)
    return [sorted(g,key=str.casefold) for g in (trade,seen)]

ORDERS_NOTE='Paper trading on live crypto prices needs no broker account.'

def load():
    data=json.loads(read(PRODUCT/'capabilities.v1.json'))
    data['live']=json.loads(read(DOCS/'product-manifest.v1.json'))['status']=='available'
    trade,seen=broker_groups()
    opened=len(trade)+len(seen)
    data['brokers']={'trade':trade,'read':seen,'open':opened,'note':ORDERS_NOTE}
    for area in data['areas']:
        if area['id']=='brokers':
            area['lead']=f'{opened} brokers connect to Trader Cockpit, and your account activity comes into your Journal.'
            area['items']=[area['how'],f'Orders from the chart: {", ".join(trade)}. {data["brokers"]["note"]}',f'See your account: {", ".join(seen)}.']
    data['paidByArea']['brokers']=f'{opened} brokers'
    for plan in data['plans']:
        if 'excluded' in plan:plan['excluded']=[i.replace('{brokers}',str(opened)) for i in plan['excluded']]
    tiers={t['name']:t['unitAmount'] for t in json.loads(read(DOCS/'commerce-public.v1.json'))['tiers']}
    for plan in data['plans']:
        if plan['id']!='free':plan['price']=tiers.pop(plan['commerce'])
    packs=', '.join(f'{price_text(p["priceCents"])} buys {p["credits"]:,} credits' for p in data['creditPacks'])
    data['paidLimits']+=[['Apollo limit per run',f'{data["runLimitCredits"]:,} credits'],['Credit packs',packs]]
    for plan in data['plans']:
        if plan['id']!='free':plan['facts']=[['Apollo credits a month',f'{plan["credits"]:,}'],['Apollo tasks at a time',str(plan['jobs'])],['Models batch size',str(plan['modelsBatch'])]]
    if tiers:raise SystemExit('Plans missing from capabilities.v1.json: '+', '.join(tiers))
    return data

def shot(s,root,first=False,link=False):
    """One app screen. A phone gets its own tighter crop when there is one, so the words stay readable.
    On Features a screen opens at full size."""
    load_attr=' fetchpriority="high"' if first else ' loading="lazy"'
    img=f'<img src="{root}{e(s["src"])}" alt="{e(s["alt"])}" width="{s["w"]}" height="{s["h"]}"{load_attr}>'
    if s.get('phone'):
        ph=s['phone'];img=f'<picture><source media="(max-width:600px)" srcset="{root}{e(ph["src"])}" width="{ph["w"]}" height="{ph["h"]}">{img}</picture>'
    return f'<figure class="shot">'+(f'<a href="{root}{e(s["src"])}">{img}</a>' if link else img)+'</figure>'

def find_shot(data,src):
    for a in data['areas']:
        for s in a.get('shots',[]):
            if s['src']==src:return s
    raise SystemExit('No shot in capabilities.v1.json: '+src)

def shots(area,root):
    rows=''.join(shot(s,root,link=True) for s in area.get('shots',[]))
    return f'<div class="shots">{rows}</div>' if len(area.get('shots',[]))>1 else rows

def ticks(items,cls=''):
    return f'<ul class="ticks{cls}">'+''.join(f'<li>{e(i)}</li>' for i in items)+'</ul>'

def names(title,rows,note):
    return f'<div class="stack"><h3>{e(title)}</h3><p class="measure">{e(note)}</p><ul class="names">'+''.join(f'<li>{e(n)}</li>' for n in rows)+'</ul></div>'

def broker_lists(data):
    b=data['brokers']
    return names(f'Orders from the chart: {len(b["trade"])} brokers',b['trade'],f'Place orders from the chart, and see your positions, balances and orders. {b["note"]}')+names(f'See your account: {len(b["read"])} brokers',b['read'],'See your positions, balances and orders.')

def a_id(area):return e(area['id'])

def features_main(data):
    rail=''.join(f'<a href="#{a_id(a)}">{e(a["title"])}</a>' for a in data['areas'])
    sections=''
    for area in data['areas']:
        brokers=area['id']=='brokers'
        inner=f'<div class="cols-2">{broker_lists(data)}</div>' if brokers else ticks(area['items'])
        lead=area['lead']+(' '+area['how'] if brokers else '')
        sections+=f'<section class="area" id="{a_id(area)}" aria-labelledby="h-{a_id(area)}"><div><h2 id="h-{a_id(area)}">{e(area["title"])}</h2><p class="lead">{e(lead)}</p></div>{shots(area,"../")}{inner}</section>'
    href,label=cta('../')
    return f'''<main id="main" tabindex="-1"><div class="wrap"><header class="page-head"><h1>Everything Trader Cockpit does.</h1><p class="lead">Every part of the Windows app, area by area.</p><div class="actions"><a class="btn primary" href="{href}">{label}</a><a class="more" href="../pricing/">See the plans</a></div></header><div class="with-rail"><nav class="rail" aria-label="Feature areas">{rail}</nav><div>{sections}</div></div></div></main>'''

def plan_price(plan):
    return '$0<span> / month</span>' if not plan['price'] else f'{price_text(plan["price"])}<span> / month</span>'

def facts_table(rows):
    return '<dl class="kv">'+''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k,v in rows)+'</dl>'

def plan_details(plan,data):
    if plan['id']=='free':
        body=facts_table(plan['facts'])+'<div class="cols-2"><div class="stack"><h3>Included</h3>'+ticks(plan['included'])+'</div><div class="stack"><h3>On the paid plans</h3>'+ticks(plan['excluded'],' no')+'</div></div>'
    else:
        groups=''.join(f'<div><h4><a href="../features/#{a_id(a)}">{e(a["title"])}</a></h4>'+ticks(a['items'])+'</div>' for a in data['areas'])
        body=facts_table(plan['facts']+data['paidLimits'])+f'<h3>Everything that comes with {e(plan["name"])}</h3><div class="groups">{groups}</div>'
    return f'<details class="plan-detail" id="plan-{e(plan["id"])}"><summary><span class="n">{e(plan["name"])}</span><span class="p">{plan_price(plan)}</span><span class="s">{e(plan["summary"])}</span><span class="o">Show everything included</span></summary><div class="plan-body">{body}</div></details>'

def plan_cards(data,root,level):
    cards=''
    for plan in data['plans']:
        attr='' if plan['id']=='free' else f' data-access-plan="{e(plan["commerce"])}"'
        facts=''.join(f'<li>{e(k)}: <b>{e(v)}</b></li>' for k,v in plan['facts'][:3])
        cards+=f'<article class="plan"><h{level}>{e(plan["name"])}</h{level}><p class="price">{plan_price(plan)}</p><p>{e(plan["summary"])}</p><ul>{facts}</ul><a class="more" href="{root}#plan-{e(plan["id"])}"{attr}>What’s included</a></article>'
    return f'<div class="plans" id="pricing-current-tier">{cards}</div>'

def pricing_main(data):
    details=''.join(plan_details(p,data) for p in data['plans'])
    rows=''
    paid=[p for p in data['plans'] if p['id']!='free']
    for area in data['areas']:
        f=data['freeByArea'].get(area['id'],'—')
        rows+=f'<tr><th scope="row"><a href="../features/#{a_id(area)}">{e(area["title"])}</a></th><td>{f}</td>'+f'<td>{e(data["paidByArea"].get(area["id"],"Yes"))}</td>'*len(paid)+'</tr>'
    heads=''.join(f'<th scope="col">{e(p["name"])}</th>' for p in data['plans'])
    href,label=cta('../')
    closed='' if data['live'] else ' Checkout isn’t open yet.'
    return f'''<main id="main" tabindex="-1"><div class="wrap"><header class="page-head"><h1>A Free plan and four monthly plans.</h1><p class="lead">Every paid plan includes every feature. They differ in Apollo credits a month, Apollo tasks at a time and Models batch size.{closed}</p><p class="facts">Prices in US dollars, billed monthly. For Windows.</p></header>{plan_cards(data,"",2)}<section class="band" aria-label="What each plan includes"><h2>What each plan includes</h2><div class="plan-list">{details}</div></section><section class="band" aria-labelledby="compare-title"><h2 id="compare-title">Compare plans</h2><div class="table-scroll"><table><thead><tr><th scope="col">Area</th>{heads}</tr></thead><tbody>{rows}</tbody></table></div></section><section class="band stack loose"><h2>Before you choose</h2><p class="lead">Trader Cockpit is research software. No plan can make a historical result predict the future or guarantee returns.</p><div class="actions"><a class="btn primary" href="{href}">{label}</a><a class="more" href="../features/">See every feature</a></div></section></div></main>'''

# Home's bands: what the app is best at, each with the part of a real screen its sentence is about.
# (title, text, area the link opens, screen, layout: "wide" stacks the screen under the text, "split" sets them side by side)
HOME_BANDS=[
    ('Search without code','Pick a market and set your costs. Builder builds and backtests thousands of strategies and keeps the ones that pass your rules.','builder','assets/features/run-search.webp','wide'),
    ('Break it before you trade it','Ready-made workflows run out-of-sample periods, other markets, slippage, Monte Carlo and walk-forward on their own. You see why each strategy dropped out.','workflows','assets/features/workflow-steps.webp','wide'),
    ('A straight verdict','Every strategy gets one grade and the reasons behind it. When it has only been tested on the data it was built on, the verdict says so.','results','assets/features/verdict.webp','wide'),
    ('Take it with you','Your own Pine scripts run on the chart. Strategies go out the other way: retest on TradingView’s bar-close timing and export as Pine, or take the rules as MetaTrader, EasyLanguage or Python code.','exports','assets/features/pine-editor.webp','split'),
]
HOME_TRIO=[
    ('order-flow','assets/features/footprint.webp','Order flow','Footprint, TPO and volume profiles and an order book heatmap, on crypto charts.'),
    ('paper','assets/features/paper.webp','Paper trading','Buy and sell from the chart with simulated money, at live crypto prices or in Bar Replay.'),
    ('charts','assets/features/watchlist.webp','Watchlists','Several lists, flags and notes, the day’s change at a glance, and one click to the chart.'),
]

def proof(data):
    """Numbers from one real Builder run, set large. The loop slot plays a real recording of the app when one is listed."""
    r=data['proofRun']
    figs=''.join(f'<div><dt>{e(label)}</dt><dd{" class=\"kept\"" if key=="kept" else ""}>{e(r[key])}</dd></div>' for key,label in (('tried','strategies built and backtested'),('kept','passed the filters'),('time','minutes and seconds for the whole search'),('perStrategy','per strategy')))
    loop=data.get('homeLoop')
    media=(f'<figure class="shot"><video controls muted loop playsinline preload="none" poster="{e(loop["poster"])}" width="{loop["w"]}" height="{loop["h"]}"><source src="{e(loop["src"])}" type="video/mp4"></video></figure>' if loop else '')
    return (f'<section class="band proof" aria-labelledby="proof-title"><div class="wrap stack loose"><div class="stack"><h2 id="proof-title">It runs on your PC</h2>'
            f'<p class="lead">One Builder search on {e(r["market"])}. Searches and backtests run on your own computer, with no meter on them, and your strategies, results and data stay in your own folder.</p></div>'
            f'<dl class="figures">{figs}</dl>{media}<a class="more" href="features/#save">Where your work is kept</a></div></section>')

def home_main(data):
    by={a['id']:a for a in data['areas']}
    href,label=cta()
    low=min(p['price'] for p in data['plans'] if p['price'])
    stage=data['homeStage']
    radios=''.join(f'<input type="radio" name="stage" id="stage-{i+1}" aria-label="{e(st["label"])}"{"" if i else " checked"}>' for i,st in enumerate(stage))
    tabs=''.join(f'<label for="stage-{i+1}">{e(st["label"])}</label>' for i,st in enumerate(stage))
    frames=''.join(shot(st,'',first=not i) for i,st in enumerate(stage))
    def band(i,row):
        title,text,area,src,layout=row;a=by[area]
        copy=f'<div class="stack"><h2 id="band-{area}">{e(title)}</h2><p class="lead">{e(text)}</p><a class="more" href="features/#{area}">{e(a["title"])}</a></div>'
        inner=f'<div class="wrap split">{copy}{shot(find_shot(data,src),"")}</div>' if layout=='split' else f'<div class="wrap stack loose">{copy}{shot(find_shot(data,src),"")}</div>'
        return f'<section class="band{"" if i%2 else " tint"}" aria-labelledby="band-{area}">{inner}</section>'
    bands=''.join(band(i,row) for i,row in enumerate(HOME_BANDS))
    trio=''.join(f'<a class="tile" href="features/#{a}">{shot(find_shot(data,src),"")}<strong>{e(t)}</strong><span>{e(x)}</span></a>' for a,src,t,x in HOME_TRIO)
    index=''.join(f'<a href="features/#{a_id(a)}"><strong>{e(a["title"])}</strong><span>{e(a["lead"])}</span></a>' for a in data['areas'])
    b=data['brokers']
    return f'''<main id="main" tabindex="-1">
<section class="hero" aria-labelledby="hero-title"><div class="wrap"><h1 id="hero-title">Find strategies that hold up.</h1><p class="lead">Trader Cockpit searches thousands of rule combinations on your market, backtests each one, then tries to break the ones it keeps. It runs on your PC and needs no code.</p><div class="actions"><a class="btn primary" href="{href}">{label}</a><a class="more" href="features/">See every feature</a></div><p class="facts">For Windows. A Free plan, and paid plans from {price_text(low)} a month.</p><div class="stage" role="group" aria-label="Screens of the app">{radios}<div class="stage-tabs">{tabs}</div>{frames}</div></div></section>
{proof(data)}
{bands}
<section class="band" aria-labelledby="band-charts"><div class="wrap stack loose"><div class="stack"><h2 id="band-charts">Charts that keep up</h2><p class="lead">Seventeen chart types, nearly a thousand community indicators beside the built-ins, drawings, alerts, watchlists, Bar Replay and your own Pine scripts. Up to sixteen charts at once.</p><a class="more" href="features/#charts">Charts</a></div>{shot(find_shot(data,"assets/features/charts.webp"),"")}<div class="tiles">{trio}</div></div></section>
<section class="band tint" aria-labelledby="band-brokers"><div class="wrap stack loose"><div class="stack"><h2 id="band-brokers">Connect your broker</h2><p class="lead">{b["open"]} brokers connect to Trader Cockpit. You sign in with your broker in your own browser, and your password never goes into the app.</p></div><div class="cols-2">{broker_lists(data)}</div></div></section>
<section class="band" aria-labelledby="pricing-title"><div class="wrap stack loose"><div class="stack"><h2 id="pricing-title">A Free plan and four monthly plans</h2><p class="lead">Every paid plan includes every feature. Searches and backtests are never metered.</p></div>{plan_cards(data,"pricing/",3)}</div></section>
<section class="band tint" aria-labelledby="all-title"><div class="wrap"><h2 id="all-title">Everything in the app</h2><nav class="index-list" aria-label="What Trader Cockpit does">{index}</nav></div></section>
<section class="band last" aria-label="Community and guides"><div class="wrap cols-2"><div class="stack"><h2>Community</h2><p class="lead">Strategies with their rules and backtests, and open-source Pine indicators. Open one in the app with a click, and publish your own.</p><a class="more" href="community/">Browse the Community</a></div><div class="stack"><h2>Guides</h2><p class="lead">Out-of-sample testing, Monte Carlo, walk-forward and the ways a backtest can mislead you.</p><p class="actions"><a class="more" href="learn/">Read the guides</a><a class="more" href="strategy-claim-audit-checklist.html">Open the backtest checklist</a></p></div></div></section>
</main>'''

def build():
    data=load()
    out={}
    features=read(DOCS/'features/index.html')
    out['features/index.html']=re.sub(r'<main id="main".*?</main>',lambda m:features_main(data),features,count=1,flags=re.S)
    pricing=read(DOCS/'pricing/index.html')
    out['pricing/index.html']=re.sub(r'<main id="main".*?</main>',lambda m:pricing_main(data),pricing,count=1,flags=re.S)
    manifest=json.loads(read(DOCS/'product-manifest.v1.json'))
    manifest['verifiedCapabilities']=[{'id':a['id'],'label':a['title'],'summary':a['lead']} for a in data['areas']]
    manifest['brokers']={'connectable':data['brokers']['open'],'tradeFromChart':len(data['brokers']['trade']),'seeAccount':len(data['brokers']['read'])}
    out['product-manifest.v1.json']=json.dumps(manifest,indent=2,ensure_ascii=False)+'\n'
    # llms.txt lists the same areas, in the same words.
    block='## What the app does\n\n'+''.join(f'- [{a["title"]}](https://trader-cockpit.com/features/#{a["id"]}): {a["lead"]}\n' for a in data['areas'])+'\n'
    out['llms.txt']=re.sub(r'## What the app does\n.*?(?=## )',lambda m:block,read(DOCS/'llms.txt'),count=1,flags=re.S)
    # Home keeps its head; the whole body is built here.
    home=read(DOCS/'index.html')
    out['index.html']=re.sub(r'<body\b.*</body>',lambda m:'<body>\n<a class="skip-link" href="#main">Skip to content</a>\n<nav class="site-nav"></nav>\n'+home_main(data)+'\n<footer></footer>\n</body>',home,count=1,flags=re.S)
    return {name:(apply(text,name) if name.endswith('.html') else text) for name,text in out.items()}

def main():
    check='--check' in sys.argv
    stale=[]
    for name,text in build().items():
        p=DOCS/name
        if read(p)!=text:
            stale.append(name)
            if not check:p.write_bytes(text.encode('utf-8'))
    if check and stale:
        print('PRODUCT PAGES: FAIL stale: '+', '.join(stale));return 1
    print('PRODUCT PAGES: '+('PASS' if check else f'wrote {len(stale)} pages'));return 0

if __name__=='__main__':sys.exit(main())
