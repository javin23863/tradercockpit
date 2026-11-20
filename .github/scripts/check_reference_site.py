#!/usr/bin/env python3
"""Page-record integrity: every published file is listed with its fingerprint, and plan prices agree everywhere.

Does not award visual or release approval.
"""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_reference_content import validate_content
ROOT=Path(__file__).resolve().parents[2];DOCS=ROOT/'docs'
def validate(root=ROOT):
 docs=root/'docs';errors=[]
 def need(ok,why):
  if not ok: errors.append(why)
 def read(p): return (root/p).read_text(encoding='utf-8')
 receipt=json.loads(read('.github/reference-import-receipt.json'))
 manifest=json.loads(read('.github/reference-content-manifest.json'))
 errors.extend(validate_content(root))
 # Files of the first import that the rebuild removed are named in removed_files, so nothing leaves unrecorded.
 removed=set(manifest.get('removed_files',[]))
 expected_files=(set(receipt['unchanged']) | {p[5:] for p in receipt['outputs'] if p.startswith('docs/')} | set(manifest.get('added_files',{}))) - removed
 actual_files={p.relative_to(docs).as_posix() for p in docs.rglob('*') if p.is_file()}
 need(actual_files==expected_files,'Unlisted or missing publishing files: '+str(sorted(actual_files ^ expected_files)))
 for name,digest in receipt['unchanged'].items():
  if name=='pricing/index.html' or name in removed or name in manifest['files'] or name in manifest.get('approved_updates',{}) or name in manifest.get('added_files',{}):continue
  p=docs/name;need(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,'Existing public file changed: '+name)
 commerce=json.loads(read('docs/commerce-public.v1.json'));tiers=commerce.get('tiers',[])
 need([(x['name'],x['unitAmount']) for x in tiers]==[('Core',1999),('Trader',4999),('Quant',9999),('ApolloPro',15000)],'Four approved tier prices drifted')
 need(commerce['checkout']=={'enabled':False,'url':None,'reason':'Checkout is not open yet.'},'Checkout boundary changed')
 html=read('docs/index.html')
 need('noindex' not in html.lower() and 'nofollow' not in html.lower(),'Public homepage must remain indexable')
 for marker in ['property="og:type"','property="og:site_name"','property="og:title"','property="og:description"','property="og:url"','name="twitter:card"','type="application/ld+json"']:
  need(marker in html,'Public homepage metadata missing: '+marker)
 need('assets/features/' in html,'Homepage must show real app screens')
 need('<form' not in html and 'type="email"' not in html,'Email capture reintroduced')
 need('href="learn/"' in html and 'href="strategy-claim-audit-checklist.html"' in html,'Guides or the backtest checklist missing from the homepage')
 pricing=read('docs/pricing/index.html')
 for tier in tiers:
  amount=('$'+format(tier['unitAmount']/100,'.2f')).removesuffix('.00')
  need(tier['name'] in pricing and amount in pricing,'Static pricing record disagrees: '+tier['name'])
 need('One plan, one access path' not in pricing,'Obsolete single-plan claim')
 need('#/access' not in pricing,'Pricing must keep one set of plan text')
 for plan in ['Core','Trader','Quant','ApolloPro']:
  need(f'data-access-plan="{plan}"' in pricing and f'href="#plan-' in pricing,'Missing static pricing fallback: '+plan)
 return errors
if __name__=='__main__':
 try: errors=validate()
 except (OSError,ValueError,KeyError,TypeError) as e:errors=[str(e)]
 print('PAGE RECORDS: '+('FAIL' if errors else 'PASS (every published file listed; prices agree; no email form on home)'))
 for error in errors:print('- '+error)
 raise SystemExit(bool(errors))
