"""Keep structural page contracts separate from human visual approval."""
import copy,json

def refresh_contracts(original, *, owner_visual_approval=False, approved_at=None):
    data=copy.deepcopy(original)
    data['reviewed_at']='2026-10-05'
    data['audit_scope']='Structural contract generation does not grant visual approval. Current visual approval is owner-provided and recorded in .github/website-reference-readiness.json.'
    for row in data['pages']:
        row['audit']=({'status':'retained_visual_composition','visual_approval':True,'approved_at':approved_at,'source':'owner','scope':'Original composition; updated wording checked separately'} if owner_visual_approval else {'status':'pending_visual_review','visual_approval':False})
        if row['path']!='research-lab.html':
            row['visual_character']['color']='Warm dark surfaces, ivory text, restrained gold navigation and action accents. Analytical images retain their source colors.'
        if row['path']=='index.html':
            row['title']='TraderCockpit | Backtesting & Strategy Validation Guides'
            row['reviewed_h1']='Backtesting and strategy validation guides'
            row['hierarchy']['focal_point']=row['reviewed_h1']
            row['hierarchy']['primary_action']='Read the guides'
            row['form_ux']['policy']='No public email capture. Search has a persistent label.'
            row['intent']['primary_job']='Choose a useful backtesting or strategy validation guide and understand that the app is in development.'
        titles={'learn/concepts/out-of-sample.html':'In-Sample vs Out-of-Sample Backtesting: Avoiding Data Leakage','learn/concepts/monte-carlo.html':'Monte Carlo Simulation for Trading Strategies: Uses and Limitations','strategy-claim-audit-checklist.html':'Trading Strategy Backtest Checklist: How to Evaluate the Evidence'}
        if row['path'] in titles:
            row['reviewed_h1']=titles[row['path']]
            row['title']=titles[row['path']]+' — TraderCockpit'
            row['hierarchy']['focal_point']=row['reviewed_h1']
        if row['path'] in {'confirmed.html','thanks.html'}:
            row['title']='Development status · TraderCockpit'
            row['reviewed_h1']='The app is in development.'
            row['hierarchy']['focal_point']=row['reviewed_h1']
            row['hierarchy']['primary_action']='Read the guides'
        if row['path']=='pricing/index.html':
            row['reviewed_h1']='Four monthly plans. One research environment.'
            row['hierarchy']['focal_point']=row['reviewed_h1']
            row['intent']['primary_job']='Compare the four published monthly plans and inspect access availability.'
            row['intent']['worst_mistake']='Believing checkout is open or treating a plan name as a verified feature entitlement.'
        if row['path']=='trust/privacy.html':
            row['reviewed_h1']='Your privacy at TraderCockpit'
            row['hierarchy']['focal_point']=row['reviewed_h1']
    privacy=next((row for row in data['pages'] if row['path']=='trust/privacy.html'),None)
    if privacy is not None and not any(row['path']=='trust/terms.html' for row in data['pages']):
        # The terms page reuses the privacy page's article layout (2026-10-08).
        terms=copy.deepcopy(privacy)
        terms.update(path='trust/terms.html',route='/trust/terms.html',title='Terms of Use — TraderCockpit',reviewed_h1='Terms of use')
        terms['hierarchy']['focal_point']='Terms of use'
        terms['hierarchy']['primary_action']='Read the terms that apply to the website, app and account service'
        terms['intent']['primary_job']='Understand the terms for using TraderCockpit: not advice, your trades, broker connections and simulations.'
        terms['intent']['worst_mistake']='Treating TraderCockpit output as financial advice or a simulated result as a real one.'
        data['pages'].insert(data['pages'].index(privacy)+1,terms)
    data['page_count']=len(data['pages'])
    return data

def serialize_contracts(value):
    return (json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
