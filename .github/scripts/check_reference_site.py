#!/usr/bin/env python3
"""Reference-import integrity only. Does not award visual or release approval."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib,json,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_reference_content import validate_content
ROOT=Path(__file__).resolve().parents[2];DOCS=ROOT/'docs'
def validate(root=ROOT):
 docs=root/'docs';errors=[]
 def need(ok,why):
  if not ok: errors.append(why)
 def read(p): return (root/p).read_text(encoding='utf-8')
 receipt=json.loads(read('.github/reference-import-receipt.json'))
 need(receipt['source_archive_sha256']=='0b0ee403e7f21773a1fb1c61520f467c39987a1dce44c7ed69aca8e5599f3a4c','Wrong input archive identity')
 content_manifest=json.loads(read('.github/reference-content-manifest.json'))
 errors.extend(validate_content(root))
 expected_files=set(receipt['unchanged']) | {p[5:] for p in receipt['outputs'] if p.startswith('docs/')} | {'assets/reference-site/original-charts.png','assets/reference-site/original-models.png','assets/reference-site/pricing.css','assets/reference-site/content.css'}
 actual_files={p.relative_to(docs).as_posix() for p in docs.rglob('*') if p.is_file()}
 need(actual_files==expected_files,'Unlisted or missing publishing files: '+str(sorted(actual_files ^ expected_files)))
 for name,item in receipt['outputs'].items():
  if name.endswith(('.webp','.svg')):
   p=root/name;need(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],'Source artwork changed: '+name)
 for name,digest in receipt['unchanged'].items():
  if name=='pricing/index.html' or name in content_manifest['files']:continue
  p=docs/name;need(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,'Existing public file changed: '+name)
 records=json.loads(read('.github/reference-site/provenance/product-captures.json'))['captures']
 for r in records:
  p=docs/'assets/reference-site'/('original-'+r['id']+'.png')
  need(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==r['original_sha256'],'Original capture identity: '+r['id'])
 commerce=json.loads(read('docs/commerce-public.v1.json'));tiers=commerce.get('tiers',[])
 need([(x['name'],x['unitAmount']) for x in tiers]==[('Core',1999),('Trader',4999),('Quant',9999),('ApolloPro',15000)],'Four approved tier prices drifted')
 need(commerce['checkout']=={'enabled':False,'url':None,'reason':'Checkout opens after payment-to-entitlement provisioning is verified end to end.'},'Checkout boundary changed')
 html=read('docs/index.html');bridge=read('docs/assets/reference-site/integration.mjs');app=read('docs/assets/reference-site/app.js')
 need('assets/generated/site-webgl-v1.js' not in html and 'quant-universe' not in html,'Retired hero reintroduced')
 need('data-scene="room"' in html and 'data-scene="laptop"' in html,'Reference scenes missing')
 for marker in ['loadProductManifest','loadPrelaunchConfig','activatePrelaunch','commerce-public.v1.json']:
  need(marker in bridge,'Missing product/commerce integration: '+marker)
 need('prefers-reduced-motion' in app and 'visibilitychange' in app,'Scene accessibility safeguards missing')
 need('synthetic' in app.lower() and 'release approval' in app.lower(),'Capture limitations missing')
 for name in ['product-state','product-heading','product-summary','manifest-capabilities','manifest-detail','product-cta','youtube-cta','purchase-support','waitlist-form','waitlist-email','waitlist-first-name','waitlist-source','waitlist-utm-source','waitlist-utm-medium','waitlist-utm-campaign']:
  need('id="'+name+'"' in html,'Missing functional access element: '+name)
 for marker in ['<form id="waitlist-form"','id="product-cta"','name="email_address"','name="fields[first_name]"']:
  need(marker in html,'Missing form contract: '+marker)
 need(re.search(r'<form[^>]*id="waitlist-form"[^>]*hidden',html) is not None,'Signup must start hidden')
 need(re.search(r'<a[^>]*id="product-cta"[^>]*hidden',html) is not None,'CTA must start hidden')
 need('href="learn/" data-journey="#/learn"' in html,'No-JavaScript learning route missing')
 need('href="docs/"' in html and 'href="trust/privacy.html"' in html,'No-JavaScript documents missing')
 pricing=read('docs/pricing/index.html')
 for tier in tiers:
  amount=('$'+format(tier['unitAmount']/100,'.2f')).removesuffix('.00')
  need(tier['name'] in pricing and amount in pricing,'Static pricing record disagrees: '+tier['name'])
 need('One plan, one access path' not in pricing,'Obsolete single-plan claim')
 return errors
if __name__=='__main__':
 try: errors=validate()
 except (OSError,ValueError,KeyError,TypeError) as e:errors=[str(e)]
 print('REFERENCE INTEGRITY: '+('FAIL' if errors else 'PASS (original scene bytes; labelled original captures; preserved routes; commerce; no-JS access)'))
 for error in errors:print('- '+error)
 raise SystemExit(bool(errors))
