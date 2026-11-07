#!/usr/bin/env python3
"""Keep plan numbers honest. Public pages show what a person receives in credits, never dollars.

Always checks every public file. With --app-repo PATH it also compares .github/product/capabilities.v1.json
with commercial_catalog.py, and .github/product/brokers.v1.json with deploy/snaptrade-brokerages.json, on
that checkout's origin/main (the app repository is private, so CI can't read it). Run that form after any change to the catalog.
"""
from pathlib import Path
import json,re,subprocess,sys

ROOT=Path(__file__).resolve().parents[2];DOCS=ROOT/'docs'
NANOS_PER_CREDIT=1_000_000  # web/apollo-meter.mjs in the app
TAGS=re.compile(r'<[^>]+>')
# What runs behind the product, and how it got here, stays off the public site. Privacy and terms name suppliers where they must.
BACKGROUND=re.compile(r'snaptrade|openrouter|luxalgo|\bstripe|\bvela\b|draft screen|final screens|early access build|enabled for our',re.I)
LEGAL={'privacy.html','terms.html'}
# "$4 of credit", "$4 worth of Apollo credits", "credit ... $4". A pack price ("$10 buys 8,000 credits") is allowed.
DOLLAR_CREDIT=re.compile(r'\$\s?\d[\d.,]*\s*(?:a month\s*)?(?:(?:worth\s+)?(?:of\s+)?(?:apollo\s+)?(?:usage\s+)?credit)|credits?\b[^.\n"]{0,30}\$\s?\d(?![\d.,]*\s+buys)',re.I)

def public_problems():
    problems=[]
    for p in DOCS.rglob('*'):
        if p.is_file() and p.suffix.lower() in {'.html','.json','.js','.mjs','.txt'} and 'generated' not in p.parts:
            raw=p.read_text(encoding='utf-8',errors='ignore')
            if p.name not in LEGAL:
                for m in BACKGROUND.finditer(raw):problems.append(f'{p.relative_to(DOCS)}: background wording: {m.group(0)!r}')
            text=TAGS.sub(' ',raw)
            for m in DOLLAR_CREDIT.finditer(text):
                if ' buys' not in text[m.start():m.end()+8]:problems.append(f'{p.relative_to(DOCS)}: dollars tied to credit: {m.group(0)[:60]!r}')
            if re.search(r'1 credit\s*(=|is)\s*\$',text,re.I):problems.append(f'{p.relative_to(DOCS)}: credit priced in dollars')
    return problems

def catalog_problems(repo):
    text=subprocess.run(['git','-C',repo,'show','origin/main:product/tradercockpit/commercial_catalog.py'],capture_output=True,text=True,encoding='utf-8',check=True).stdout
    usd=int(re.search(r'^USD = ([\d_]+)',text,re.M)[1].replace('_',''))
    to_credits=lambda n:n*usd//NANOS_PER_CREDIT
    data=json.loads((ROOT/'.github/product/capabilities.v1.json').read_text(encoding='utf-8'))
    problems=[]
    plans={p['name']:p for p in data['plans']}
    for name,cents,dollars,jobs,batch in re.findall(r'Plan\("\w+", "([^"]+)", (\d+), (\d+) \* USD, (\d+), RUN_PROVIDER_CALLS, RUN_CEILING_NANOS, (\d+), \*FEATURE_LIMITS\)',text):
        plan=plans.get(name)
        got=plan and (plan['credits'],plan['jobs'],plan['modelsBatch'])
        want=(to_credits(int(dollars)),int(jobs),int(batch))
        if got!=want:problems.append(f'{name}: site {got}, catalog {want}')
    ceiling=int(re.search(r'^RUN_CEILING_NANOS = (\d+) \* USD',text,re.M)[1])
    if data['runLimitCredits']!=to_credits(ceiling):problems.append('run limit differs from the catalog')
    packs=[{'priceCents':int(c),'credits':to_credits(int(d))} for c,d in re.findall(r'"price_cents": (\d+), "credit_nanos": (\d+) \* USD',text)]
    if data['creditPacks']!=packs:problems.append(f'credit packs differ: {packs}')
    return problems+broker_problems(repo)

def broker_problems(repo):
    text=subprocess.run(['git','-C',repo,'show','origin/main:deploy/snaptrade-brokerages.json'],capture_output=True,text=True,encoding='utf-8',check=True).stdout
    routes=lambda rows:{(k,r['name'],m,v['trading'] is True) for k,r in rows.items() for m,v in r['routes'].items()}
    app=routes(json.loads(text)['institutions'])
    site=routes(json.loads((ROOT/'.github/product/brokers.v1.json').read_text(encoding='utf-8'))['institutions'])
    return [f'broker route on the site differs from the app: {r}' for r in sorted(site-app)]

def main():
    problems=public_problems()
    if '--app-repo' in sys.argv:
        problems+=catalog_problems(sys.argv[sys.argv.index('--app-repo')+1])
    for problem in problems:print('- '+problem)
    print('PLAN CATALOG: '+('FAIL' if problems else 'PASS'))
    return 1 if problems else 0

if __name__=='__main__':sys.exit(main())
