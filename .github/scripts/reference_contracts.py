"""Keep structural page contracts separate from human visual approval."""
import copy,json,re
from pathlib import Path
DOCS=Path(__file__).resolve().parents[2]/'docs'

def community_pages():
    """Community pages are generated from docs/community/items.v1.json, so their rows follow the files."""
    return sorted(p.relative_to(DOCS).as_posix() for p in (DOCS/'community').rglob('index.html'))

# Pages added after the owner's 2026-09-18 visual approval; each waits for its own review.
PENDING_OWNER_VISUAL_REVIEW=frozenset({'trust/terms.html','features/index.html','early-access.html',*community_pages()})
PENDING_AUDIT={'status':'pending_visual_review','visual_approval':False}

def refresh_contracts(original, *, owner_visual_approval=False, approved_at=None):
    data=copy.deepcopy(original)
    data['reviewed_at']='2026-10-05'
    data['audit_scope']='Structural contract generation does not grant visual approval. Current visual approval is owner-provided and recorded in .github/website-reference-readiness.json.'
    for row in data['pages']:
        row['audit']=({'status':'retained_visual_composition','visual_approval':True,'approved_at':approved_at,'source':'owner','scope':'Original composition; updated wording checked separately'} if owner_visual_approval else {'status':'pending_visual_review','visual_approval':False})
        row['visual_character']['color']='Warm dark surfaces, ivory text, restrained gold navigation and action accents. Analytical images retain their source colors.'
        if row['path']=='index.html':
            row['title']='Trader Cockpit | Build and Test Trading Strategies'
            row['reviewed_h1']='Build a trading strategy. Find out if it holds up.'
            row['hierarchy']['focal_point']=row['reviewed_h1']
            row['hierarchy']['primary_action']='Join the early access list'
            row['form_ux']['policy']='The email form is on the early access page. Search has a persistent label.'
            row['intent']['primary_job']='Understand what Trader Cockpit does and join the early access list.'
        titles={'learn/concepts/out-of-sample.html':'In-Sample vs Out-of-Sample Backtesting: Avoiding Data Leakage','learn/concepts/monte-carlo.html':'Monte Carlo Simulation for Trading Strategies: Uses and Limitations','strategy-claim-audit-checklist.html':'Trading Strategy Backtest Checklist: How to Evaluate the Evidence'}
        if row['path'] in titles:
            row['reviewed_h1']=titles[row['path']]
            row['title']=titles[row['path']]+' — Trader Cockpit'
            row['hierarchy']['focal_point']=row['reviewed_h1']
        if row['path'] in {'confirmed.html','thanks.html'}:
            done=row['path']=='confirmed.html'
            row['title']=('You’re on the list.' if done else 'Check your email.')+' · Trader Cockpit'
            row['reviewed_h1']='You’re on the list.' if done else 'Check your email.'
            row['hierarchy']['focal_point']=row['reviewed_h1']
            row['hierarchy']['primary_action']='Read the guides'
        if row['path']=='pricing/index.html':
            row['reviewed_h1']='A Free plan and four monthly plans. One research environment.'
            row['hierarchy']['focal_point']=row['reviewed_h1']
            row['intent']['primary_job']='Compare the four published monthly plans and inspect access availability.'
            row['intent']['worst_mistake']='Believing checkout is open or treating a plan name as a verified feature entitlement.'
        if row['path']=='trust/privacy.html':
            row['title']='Privacy Notice — Trader Cockpit'
            row['reviewed_h1']='Your privacy at Trader Cockpit'
            row['hierarchy']['focal_point']=row['reviewed_h1']
    privacy=next((row for row in data['pages'] if row['path']=='trust/privacy.html'),None)
    if privacy is not None and not any(row['path']=='trust/terms.html' for row in data['pages']):
        # The terms page reuses the privacy page's article layout (2026-10-08).
        terms=copy.deepcopy(privacy)
        terms.update(path='trust/terms.html',route='/trust/terms.html',title='Terms of Use — Trader Cockpit',reviewed_h1='Terms of use')
        terms['hierarchy']['focal_point']='Terms of use'
        terms['hierarchy']['primary_action']='Read the terms that apply to the website, app and account service'
        terms['intent']['primary_job']='Understand the terms for using Trader Cockpit: not advice, your trades, broker connections and simulations.'
        terms['intent']['worst_mistake']='Treating Trader Cockpit output as financial advice or a simulated result as a real one.'
        terms['audit']=dict(PENDING_AUDIT)
        data['pages'].insert(data['pages'].index(privacy)+1,terms)
    pricing=next((row for row in data['pages'] if row['path']=='pricing/index.html'),None)
    if pricing is not None:
        for path,route,title,h1,job,worst,action in (
            ('features/index.html','/features/','Features — Trader Cockpit','What Trader Cockpit does today.','See what the app does today, each item shown from the real app on real market data.','Treating a screen as a promise of results.','Join the early access list'),
            ('early-access.html','/early-access.html','Early access — Trader Cockpit','Join the early access list.','Leave an email to hear when the app opens.','Believing the app is already on general release.','Join the list')):
            page=copy.deepcopy(pricing);page.update(path=path,route=route,title=title,reviewed_h1=h1,kind='landing')
            page['hierarchy'].update(focal_point=h1,primary_action=action);page['intent'].update(primary_job=job,worst_mistake=worst);page['audit']=dict(PENDING_AUDIT)
            if path=='early-access.html':page['form_ux']['policy']='One labeled email field; errors are stated and the address stays in the field.'
            data['pages'].append(page)
    features=next((row for row in data['pages'] if row['path']=='features/index.html'),None)
    for path in community_pages() if features is not None else []:
        text=(DOCS/path).read_text(encoding='utf-8')
        title=re.sub(r'<[^>]+>','',re.search(r'<title>(.*?)</title>',text,re.S)[1]);h1=re.sub(r'<[^>]+>','',re.search(r'<h1[^>]*>(.*?)</h1>',text,re.S)[1])
        page=copy.deepcopy(features);page.update(path=path,route='/'+path.removesuffix('index.html'),title=title,reviewed_h1=h1,kind='landing')
        page['hierarchy'].update(focal_point=h1,primary_action='Open in Trader Cockpit' if path.count('/')==3 and '/authors/' not in path else 'Open a community item')
        page['intent'].update(primary_job='Study shared strategies, indicators and ideas, and open them in Trader Cockpit.',worst_mistake='Treating a shared backtest as a promise of results.')
        page['audit']=dict(PENDING_AUDIT);data['pages'].append(page)
    data['page_count']=len(data['pages'])
    return data

def serialize_contracts(value):
    return (json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
