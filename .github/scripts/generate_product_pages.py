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

def facts():
    """Shared numbers and phrases: {name} in any text of capabilities.v1.json; {Name} gives it a capital."""
    return json.loads(read(PRODUCT/'capabilities.v1.json'))['facts']

def fill(text,f):
    for k,v in f.items():text=text.replace('{'+k+'}',v).replace('{'+k[0].upper()+k[1:]+'}',v[0].upper()+v[1:])
    return text

def load():
    f=facts()
    data=json.loads(fill(read(PRODUCT/'capabilities.v1.json'),f))
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

def shot(s,root,first=False,link=False,caption=''):
    """One app screen. A phone gets its own tighter crop when there is one, so the words stay readable.
    On Features a screen opens at full size."""
    load_attr=' fetchpriority="high"' if first else ' loading="lazy"'
    img=f'<img src="{root}{e(s["src"])}" alt="{e(s["alt"])}" width="{s["w"]}" height="{s["h"]}"{load_attr}>'
    if s.get('phone'):
        ph=s['phone'];img=f'<picture><source media="(max-width:600px)" srcset="{root}{e(ph["src"])}" width="{ph["w"]}" height="{ph["h"]}">{img}</picture>'
    cap=f'<figcaption>{e(caption)}</figcaption>' if caption else ''
    return f'<figure class="shot">'+(f'<a href="{root}{e(s["src"])}">{img}</a>' if link else img)+cap+'</figure>'

def find_shot(data,src):
    for a in data['areas']:
        for s in a.get('shots',[]):
            if s['src']==src:return s
            if s.get('phone',{}).get('src')==src:return {'src':src,'alt':s['alt'],'w':s['phone']['w'],'h':s['phone']['h']}
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
    return f'''<main id="main" tabindex="-1"><div class="wrap"><header class="page-head split"><div class="stack"><h1>A Free plan and four monthly plans.</h1><p class="lead">Every paid plan includes every feature. They differ in Apollo credits a month, Apollo tasks at a time and Models batch size. {e(fill("{unmetered}",facts()))}{closed}</p><p class="facts">Prices in US dollars, billed monthly. For Windows.</p></div>{shot(find_shot(data,"assets/features/charts-multi.webp"),"../",caption=f"Free includes {dict(data['plans'][0]['facts'])['Charts at once']} charts at once and {dict(data['plans'][0]['facts'])['Indicators per chart']} indicators on each.")}</header>{plan_cards(data,"",2)}<section class="band" aria-label="What each plan includes"><h2>What each plan includes</h2><div class="plan-list">{details}</div></section><section class="band" aria-labelledby="compare-title"><h2 id="compare-title">Compare plans</h2><p class="micro scroll-cue">The table scrolls sideways: every plan has a column.</p><div class="table-scroll"><table><thead><tr><th scope="col">Area</th>{heads}</tr></thead><tbody>{rows}</tbody></table></div></section><section class="band stack loose"><h2>Before you choose</h2><p class="lead">Trader Cockpit is research software. No plan can make a historical result predict the future or guarantee returns.</p><div class="actions"><a class="btn primary" href="{href}">{label}</a><a class="more" href="../features/">See every feature</a></div></section></div></main>'''

# Home's bands: what the app is best at, each with the part of a real screen its sentence is about.
# (title, text, area the link opens, screen, layout: "wide" stacks the screen under the text, "split" sets them side by side)
HOME_BANDS=[
    ('Search without code','Pick a market and set your costs. Builder builds and backtests thousands of strategies on your own PC, keeps the ones that pass your rules, and shows why the rest were dropped.','builder','assets/features/run-reasons.webp','split'),
    ('Break it before you trade it','Ready-made workflows run out-of-sample periods, other markets, slippage, Monte Carlo and walk-forward on their own. You see why each strategy dropped out.','workflows','assets/features/workflow-steps.webp','wide'),
    ('A straight verdict','Every strategy gets one grade and the reasons behind it. A backtest can look strong and still fail out of sample or under Monte Carlo, and the verdict says so.','results','assets/features/verdict.webp','wide'),
    ('Take it with you','Your own Pine scripts run on the chart. Strategies go out the other way: retest on TradingView’s bar-close timing and export as Pine, or take the rules as MetaTrader, EasyLanguage or Python code.','exports','assets/features/pine-editor.webp','split'),
]
HOME_TRIO=[
    ('order-flow','assets/features/footprint-crop.webp','Order flow','Footprint, TPO and volume profiles and an order book heatmap, on crypto charts.'),
    ('paper','assets/features/paper-crop.webp','Paper trading','Buy and sell from the chart with simulated money, at live crypto prices or in Bar Replay.'),
    ('charts','assets/features/watchlist.webp','Watchlists','Several lists, flags and notes, the day’s change at a glance, and one click to the chart.'),
]

def run_proof(r):
    """The recorded search's own figures and drop reasons, as text, so they read at any width."""
    figs=''.join(f'<div><dt>{e(label)}</dt><dd{" class=\"kept\"" if key=="kept" else ""}>{e(r[key])}</dd></div>' for key,label in (('tried','built and backtested'),('kept','kept'),('dropped','dropped')))
    rows=''.join(f'<li><span>{e(label)}</span><span class="bar" aria-hidden="true"><i style="width:{share}%"></i></span><b>{share}%</b></li>' for label,share in r['reasons'])
    return (f'<figure class="run-proof"><dl class="run-figures">{figs}</dl><p class="run-why">Why the {e(r["dropped"])} were dropped</p>'
            f'<ul class="run-reasons">{rows}</ul><figcaption>{e(r["caption"])}</figcaption></figure>')

def home_main(data):
    by={a['id']:a for a in data['areas']}
    href,label=cta()
    low=min(p['price'] for p in data['plans'] if p['price'])
    stage=data['homeStage']
    radios=''.join(f'<input type="radio" name="stage" id="stage-{i+1}" aria-label="{e(st["label"])}"{"" if i else " checked"}>' for i,st in enumerate(stage))
    tabs=''.join(f'<label for="stage-{i+1}">{e(st["label"])}</label>' for i,st in enumerate(stage))
    frames=''.join(shot(st,'') for st in stage)
    def band(i,row):
        title,text,area,src,layout=row;a=by[area]
        copy=f'<div class="stack"><h2 id="band-{area}">{e(title)}</h2><p class="lead">{e(text)}</p><a class="more" href="features/#{area}">{e(a["title"])}</a></div>'
        inner=f'<div class="wrap split">{copy}{shot(find_shot(data,src),"")}</div>' if layout=='split' else f'<div class="wrap stack loose">{copy}{shot(find_shot(data,src),"")}</div>'
        return f'<section class="band{" tint" if i%2 else ""}" aria-labelledby="band-{area}">{inner}</section>'
    bands=''.join(band(i,row) for i,row in enumerate(HOME_BANDS))
    trio=''.join(f'<a class="tile" href="features/#{a}">{shot(find_shot(data,src),"")}<strong>{e(t)}</strong><span>{e(x)}</span></a>' for a,src,t,x in HOME_TRIO)
    index=''.join(f'<a href="features/#{a_id(a)}"><strong>{e(a["title"])}</strong><span>{e(a["lead"])}</span></a>' for a in data['areas'])
    b=data['brokers']
    return f'''<main id="main" tabindex="-1">
<section class="hero" aria-labelledby="hero-title"><div class="wrap hero-grid"><div class="stack loose"><h1 id="hero-title">Find strategies that hold up.</h1><p class="lead">Trader Cockpit searches thousands of rule combinations on your market, backtests each one, then tries to break the ones it keeps. It runs on your PC and needs no code.</p><div class="actions"><a class="btn primary" href="{href}">{label}</a><a class="more" href="features/">See every feature</a></div><p class="facts">For Windows. A Free plan, and paid plans from {price_text(low)} a month.</p></div>{run_proof(data["proofRun"])}</div></section>
<section class="band tint" aria-labelledby="inside-title"><div class="wrap stack loose"><h2 id="inside-title">Inside Trader Cockpit</h2><div class="stage" role="group" aria-label="Screens of the app">{radios}<div class="stage-tabs">{tabs}</div>{frames}</div></div></section>
{bands}
<section class="band" aria-labelledby="band-charts"><div class="wrap stack loose"><div class="stack"><h2 id="band-charts">Charts that keep up</h2><p class="lead">Seventeen chart types, {fill("{communityIndicators}",facts())} community indicators beside the built-ins, drawings, alerts, watchlists, Bar Replay and your own Pine scripts. Up to sixteen charts at once.</p><a class="more" href="features/#charts">Charts</a></div>{shot(find_shot(data,"assets/features/charts.webp"),"")}<div class="tiles">{trio}</div></div></section>
<section class="band tint" aria-labelledby="band-brokers"><div class="wrap stack loose"><div class="stack"><h2 id="band-brokers">Connect your broker</h2><p class="lead">{b["open"]} brokers connect to Trader Cockpit. You sign in with your broker in your own browser, and your password never goes into the app.</p></div><div class="cols-2">{broker_lists(data)}</div></div></section>
<section class="band" aria-labelledby="pricing-title"><div class="wrap stack loose"><div class="stack"><h2 id="pricing-title">A Free plan and four monthly plans</h2><p class="lead">Every paid plan includes every feature. {e(fill("{unmetered}",facts()))}</p></div>{plan_cards(data,"pricing/",3)}</div></section>
<section class="band tint" aria-labelledby="all-title"><div class="wrap"><h2 id="all-title">Everything in the app</h2><nav class="index-list" aria-label="What Trader Cockpit does">{index}</nav></div></section>
<section class="band last" aria-label="Community and guides"><div class="wrap cols-2"><div class="stack"><h2>Community</h2><p class="lead">Strategies with their rules and backtests, and open-source Pine indicators. Open one in the app with a click, and publish your own.</p>{shot(find_shot(data,data["communityPicture"]),"")}<a class="more" href="community/">Browse the Community</a></div><div class="stack"><h2>Guides</h2><p class="lead">Out-of-sample testing, Monte Carlo, walk-forward and the ways a backtest can mislead you.</p><p class="actions"><a class="more" href="learn/">Read the guides</a><a class="more" href="strategy-claim-audit-checklist.html">Open the backtest checklist</a></p></div></div></section>
</main>'''

def faq_main(data):
    by={a['id']:a for a in data['areas']};f=facts();b=data['brokers']
    free=data['plans'][0];paid=data['plans'][1:];ff=dict(free['facts'])
    def money(p):return price_text(p['price'])
    def lst(xs):return ', '.join(xs[:-1])+' and '+xs[-1]
    qa=[
     ('What is Trader Cockpit?','Trader Cockpit is a Windows app for building and testing trading strategies. It searches thousands of rule combinations on your market, backtests each one, then tries to break the ones it keeps. It also has charts, order flow, paper trading, broker connections, a Community, a journal and the Apollo assistant.','../features/','See every feature'),
     ('Do I need to code?','No. Strategy Builder builds and backtests strategies from the market, costs and rules you set. Apollo turns an idea in plain words into a Builder rule part or a Pine script. If you write Pine, your own v5 and v6 scripts run on the chart.',None,None),
     ('Which markets and data can I use?','Crypto from Coinbase and Kraken comes with free public history and live prices, with no exchange account. Daily history for stocks, indices, forex pairs and futures downloads inside the app, and so does forex and metals history. You can also import your own price files, and use MetaTrader 5 history and quotes from your own terminal.','../features/#data','Market data and import'),
     ('Does it run my Pine scripts?',fill('Yes. Your own Pine v5 and v6 indicators and strategies run on the chart, and anything that can’t run is listed by line. The chart’s indicator list also has {communityIndicators} open-source community indicators, and each one opens its code as a copy.',f),None,None),
     ('Is there a free plan, and what is in it?',f'Yes, after a free sign-in and with no payment. Free has {ff["Charts at once"]} charts at once and {ff["Indicators per chart"]} indicators on each. It includes: '+'; '.join(i[0].lower()+i[1:] for i in free['included'])+'. '+lst(free['excluded'][:6])+' are on the paid plans.','../pricing/#plan-free','See what Free includes'),
     ('What do the paid plans cost and how do they differ?',f'{lst([f"{p["name"]} is {money(p)} a month" for p in paid])}. Every paid plan includes every feature. They differ in Apollo credits a month ({lst([f"{p["credits"]:,}" for p in paid])}), Apollo tasks at a time ({lst([str(p["jobs"]) for p in paid])}) and Models batch size. '+fill('{unmetered}',f)+' Prices are in US dollars, billed monthly.','../pricing/','Compare the plans'),
     ('Can I connect my broker, and does it place live orders?',f'{b["open"]} brokers connect on a paid plan. You sign in with your broker in your own browser, and your password never goes into Trader Cockpit. With {len(b["trade"])} of them you place orders from the chart yourself, and with the other {len(b["read"])} you see your positions, balances and orders. Apollo never sends live broker orders. {b["note"]}','../features/#brokers','See the broker list'),
     ('Does it run on Mac?','No. Trader Cockpit is a Windows app.',None,None),
     ('Where is my data kept?',' '.join(by['save']['items'])+' '+by['save']['lead'],None,None),
     ('What is Apollo and what are credits?',f'Apollo is the assistant inside the app. Describe an idea in plain words and it turns it into a strategy you can test, and you confirm every change. Apollo runs on Apollo credits. Each paid plan includes them every month, from {paid[0]["credits"]:,} on {paid[0]["name"]} to {paid[-1]["credits"]:,} on {paid[-1]["name"]}, and a credit pack adds more ('+', '.join(f'{price_text(p["priceCents"])} buys {p["credits"]:,} credits' for p in data['creditPacks'])+').','../features/#apollo','Apollo assistant'),
     ('Can I take a strategy to another platform?','Yes. Retest a strategy on TradingView’s bar-close timing and export it as Pine. Anything that can’t match is refused, with the reason. Results also writes the strategy as EasyLanguage, MetaTrader or Python code, and trades export as CSV or Excel.','../features/#exports','Exports'),
     ('Is a backtest a promise of profit?','No. Trader Cockpit is research software and does not give financial advice. No backtest or simulation predicts future results. The guides explain what each test can and cannot tell you.','../learn/','Read the guides'),
    ]
    href,label=cta('../')
    items=''.join(f'<details class="qa"><summary>{e(q)}</summary><div><p>{e(a)}</p>'+(f'<p><a href="{l}">{e(t)}</a></p>' if l else '')+'</div></details>' for q,a,l,t in qa)
    items+=f'<details class="qa"><summary>How do I get it?</summary><div><p>{"Download it for Windows." if data["live"] else "The Windows app is in early access. Leave your email on the early access list and we tell you when it opens."}</p><p><a href="{href}">{label}</a></p></div></details>'
    return f'<main id="main" tabindex="-1"><div class="wrap"><header class="page-head"><h1>Trader Cockpit FAQ</h1><p class="lead">Short answers about the app, the plans and how to get it.</p></header><div class="measure">{items}</div><section class="band stack"><h2>Ask us</h2><p>Write to <a href="mailto:support@trader-cockpit.com">support@trader-cockpit.com</a>.</p><div class="actions"><a class="btn primary" href="{href}">{label}</a><a class="more" href="../pricing/">See the plans</a></div></section></div></main>'

def build():
    data=load()
    out={}
    faq=read(DOCS/'support/faq.html')
    out['support/faq.html']=re.sub(r'<main id="main".*?</main>',lambda m:faq_main(data),faq,count=1,flags=re.S)
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
