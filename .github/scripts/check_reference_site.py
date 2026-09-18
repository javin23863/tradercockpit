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
 production=json.loads(read('.github/reference-site/provenance/production-screen-layers.json'))
 need(receipt['source_archive_sha256']=='0b0ee403e7f21773a1fb1c61520f467c39987a1dce44c7ed69aca8e5599f3a4c','Wrong input archive identity')
 content_manifest=json.loads(read('.github/reference-content-manifest.json'))
 errors.extend(validate_content(root))
 expected_files=set(receipt['unchanged']) | {p[5:] for p in receipt['outputs'] if p.startswith('docs/')} | {'assets/reference-site/original-charts.png','assets/reference-site/original-models.png','assets/reference-site/pricing.css','assets/reference-site/content.css'}
 actual_files={p.relative_to(docs).as_posix() for p in docs.rglob('*') if p.is_file()}
 need(actual_files==expected_files,'Unlisted or missing publishing files: '+str(sorted(actual_files ^ expected_files)))
 for name,item in receipt['outputs'].items():
  if name.endswith(('.webp','.svg')) and not name.endswith(('room-screen.webp','laptop-screen.webp')):
   p=root/name;need(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],'Source artwork changed: '+name)
 for name,digest in receipt['unchanged'].items():
  if name=='pricing/index.html' or name in content_manifest['files']:continue
  p=docs/name;need(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,'Existing public file changed: '+name)
 need(production.get('schema')=='tradercockpit.production-screen-layers/v1' and production.get('quality')=='FULL_RESOLUTION_CAPTURE_SOURCE','Production screen-layer provenance missing or downgraded')
 need(hashlib.sha256((root/'.github/scripts/generate_reference_screen_layers.mjs').read_bytes()).hexdigest()==production.get('generator_sha256'),'Screen-layer generator identity changed')
 need(hashlib.sha256((root/'.github/reference-site/provenance/screen-placement.json').read_bytes()).hexdigest()==production.get('placement_sha256'),'Screen placement authority changed')
 expected_layers={'room':('charts','original-charts.png','room-screen.webp','bc2746d1fdda38c5cdcea0a74d9f82e78d0fb6cb9f98844023b4283f55aad9ae'),'laptop':('models','original-models.png','laptop-screen.webp','3a63057265cb14c7640883cbba1144907c7dd2e2e5419b8f37fcb5ca14ff3bc6')}
 layers={item.get('scene'):item for item in production.get('layers',[])}
 need(set(layers)==set(expected_layers),'Production screen layers must be room and laptop only')
 for scene,(capture,source,output,source_hash) in expected_layers.items():
  item=layers.get(scene,{})
  src=docs/'assets/reference-site'/source;out=docs/'assets/reference-site'/output
  need(item.get('capture')==capture and item.get('source_asset')=='docs/assets/reference-site/'+source,'Screen layer must use verified original: '+scene)
  need(src.is_file() and hashlib.sha256(src.read_bytes()).hexdigest()==source_hash==item.get('source_sha256'),'Full-resolution screen source identity: '+scene)
  need(out.is_file() and hashlib.sha256(out.read_bytes()).hexdigest()==item.get('output_sha256'),'Generated screen-layer identity: '+scene)
  need(item.get('generator')=='.github/scripts/generate_reference_screen_layers.mjs' and item.get('release_approved') is False,'Screen layer provenance boundary: '+scene)
 records=json.loads(read('.github/reference-site/provenance/product-captures.json'))['captures']
 for r in records:
  p=docs/'assets/reference-site'/('original-'+r['id']+'.png')
  need(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==r['original_sha256'],'Original capture identity: '+r['id'])
 commerce=json.loads(read('docs/commerce-public.v1.json'));tiers=commerce.get('tiers',[])
 need([(x['name'],x['unitAmount']) for x in tiers]==[('Core',1999),('Trader',4999),('Quant',9999),('ApolloPro',15000)],'Four approved tier prices drifted')
 need(commerce['checkout']=={'enabled':False,'url':None,'reason':'Checkout opens after payment-to-entitlement provisioning is verified end to end.'},'Checkout boundary changed')
 html=read('docs/index.html');bridge=read('docs/assets/reference-site/integration.mjs');app=read('docs/assets/reference-site/app.js');journeys=read('docs/assets/reference-site/journeys.js')
 public_runtime=(html+'\n'+app+'\n'+journeys).lower()
 need('noindex' not in html.lower() and 'nofollow' not in html.lower(),'Public homepage must remain indexable')
 for marker in ['property="og:type"','property="og:site_name"','property="og:title"','property="og:description"','property="og:url"','name="twitter:card"','type="application/ld+json"']:
  need(marker in html,'Public homepage metadata missing: '+marker)
 for phrase in ['search this preview','about this preview','homepage proof','not a release candidate','under visual review','in this preview','explore this preview','this preview does not offer','this preview does not contain','the preview does not establish']:
  need(phrase not in public_runtime,'Internal review wording leaked to public surface: '+phrase)
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
