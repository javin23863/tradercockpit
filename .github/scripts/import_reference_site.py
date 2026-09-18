#!/usr/bin/env python3
"""Import the exact owner-review archive without restyling its scene composition.

Default: plan only. --apply changes only the explicit paths in the plan, after
all source and destination checks succeed. This does not enable review/release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile
import zipfile

SOURCE_SHA = '0b0ee403e7f21773a1fb1c61520f467c39987a1dce44c7ed69aca8e5599f3a4c'
BRANCH = 'codex/website-reference-integration-20260918'
ZIP_ROOT = 'TraderCockpit-homepage-proof/'
ASSET_ROOT = 'docs/assets/reference-site/'
HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent/'reference-site'
RUNTIME = ['styles.css','journeys.css','app.js','journeys.js','capture-overrides.js']
IMAGES = ['mark.svg','room-scene.webp','room-screen.webp','laptop-scene.webp','laptop-screen.webp',
          'builder.webp','apollo.webp','data.webp','projects.webp','product-charts.webp','product-models.webp']
REFERENCES = ['asset-provenance.json','product-captures.json','screen-placement.json','journey-sources.json']
sha = lambda value: hashlib.sha256(value).hexdigest()

def tree_hashes(root: Path) -> dict[str,str]:
    return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}

def safe_target(root: Path, name: str) -> Path:
    candidate = root/name
    if not candidate.resolve().is_relative_to(root.resolve()): raise ValueError('Unsafe destination path')
    cursor = candidate
    while cursor != root:
        if cursor.is_symlink(): raise ValueError('Symlink destination is not allowed: '+name)
        cursor = cursor.parent
    return candidate

def read_source(archive: Path) -> dict[str,bytes]:
    if not archive.is_file(): raise FileNotFoundError('The exact source ZIP is missing: '+str(archive))
    if archive.stat().st_size > 24_000_000: raise ValueError('Source archive exceeds size limit')
    raw = archive.read_bytes()
    if sha(raw) != SOURCE_SHA: raise ValueError('Source archive SHA-256 does not match the approved input')
    wanted = {'index.html','commerce-snapshot.json',*RUNTIME,*('assets/'+n for n in IMAGES),*('reference/'+n for n in REFERENCES)}
    with zipfile.ZipFile(archive) as z:
        members = z.infolist()
        if len(members)>200 or sum(i.file_size for i in members)>32_000_000: raise ValueError('Archive expansion limit')
        if len({i.filename for i in members}) != len(members): raise ValueError('Duplicate archive member')
        for entry in members:
            p = PurePosixPath(entry.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in entry.filename: raise ValueError('Unsafe archive member')
            if stat.S_ISLNK(entry.external_attr >> 16): raise ValueError('Archive symlink not allowed')
        # Never extract the archive. Read only allowlisted members into memory.
        return {name:z.read(ZIP_ROOT+name) for name in sorted(wanted)}

def update_journeys(text: str) -> str:
    start = text.index('  let data = {};')
    end = text.index('  const price = name =>',start)
    new = '''  let data = {}, validCommerce = false;
  const plans = ['Core', 'Trader', 'Quant', 'ApolloPro'];
  document.addEventListener('tc:commerce', event => {
    const value = event.detail;
    validCommerce = value?.schema === 'public-commerce/v1' && value.status === 'prelaunch' &&
      value.plan?.currency === 'USD' && value.checkout?.enabled === false && value.checkout.url === null &&
      Array.isArray(value.tiers) && value.tiers.length === plans.length && plans.every((name,index) =>
        value.tiers[index]?.name===name && value.tiers[index].interval==='month' &&
        Number.isSafeInteger(value.tiers[index].unitAmount) && value.tiers[index].unitAmount>0);
    data = validCommerce ? value : {};
    if (location.hash.startsWith('#/access')) render(false);
  });
'''
    text = text[:start]+new+text[end:]
    text = text.replace('Preview snapshot · Prelaunch', "${validCommerce ? 'Prelaunch · Local record verified' : 'Availability unverified'}")
    text = text.replace('href="https://javin23863.github.io/tradercockpit/#public-status" target="_blank" rel="noopener noreferrer"', 'href="#public-status"')
    text = text.replace('Visit official access page', 'Open waitlist and availability')
    text = text.replace('External page. It may show the older public website design.', 'The waitlist is separate from paid access. Review its email-submission notice before joining.')
    text = text.replace('The prices in this saved preview are a snapshot, not a live quote.', 'Prices load from the local public commerce record. No payment service is enabled here.')
    return text

def transform_html(html: str, commerce: dict) -> str:
    html = html.replace('class="skip"', 'class="skip skip-link"',1)
    html = html.replace('<title>', '<link rel="canonical" href="https://javin23863.github.io/tradercockpit/">\n  <title>',1)
    html = html.replace('content="TraderCockpit homepage visual proof.', 'content="TraderCockpit quantitative research.')
    html = re.sub(r'(?P<prefix>\b(?:src|href)=")assets/',r'\g<prefix>assets/reference-site/',html)
    for name in RUNTIME:
        html = html.replace('"'+name+'"','"assets/reference-site/'+name+'"')
    html = html.replace('</head>', '  <link rel="stylesheet" href="assets/reference-site/integration.css">\n  <script type="module" src="assets/reference-site/integration.mjs"></script>\n</head>')
    html = re.sub(r'(<script id="commerce-snapshot" type="application/json">)[\s\S]*?(</script>)',
        lambda m:m[1]+json.dumps(commerce,separators=(',',':')).replace('<','\\u003c')+m[2],html)
    # Upgrade static anchors only at runtime; without JS they open real public pages.
    def route_link(match):
        route=match[1]
        destination='learn/' if route.startswith('#/learn') else 'pricing/'
        return 'href="'+destination+'" data-journey="'+route+'"'
    html=re.sub(r'href="(#/(?:learn|access)[^"]*)"',route_link,html)
    html=html.replace('No trading, payment, or account service runs in this preview.',
        'No trading or payment service runs on this page. Email is sent to Kit only when you submit the waitlist form.')
    html=html.replace('</footer>', '</footer>\n'+(TEMPLATES/'access-panel.html').read_text(encoding='utf-8'),1)
    html=html.replace('Navigation links still work.', 'Use the Documentation, Learning library, Pricing, Support and Privacy links below. Interactive screen inspection and notes require JavaScript.')
    return html

def make_plan(root: Path, archive: Path) -> dict:
    root=root.resolve()
    source=read_source(archive)
    docs=root/'docs'
    if not (docs/'index.html').is_file(): raise ValueError('Target must contain the existing docs/index.html')
    product=json.loads((docs/'product-manifest.v1.json').read_text(encoding='utf-8-sig'))
    existing=json.loads((docs/'commerce-public.v1.json').read_text(encoding='utf-8-sig'))
    commerce=json.loads(source['commerce-snapshot.json'])
    if product.get('status')!='waitlist' or product.get('verifiedCapabilities')!=[]:
        raise ValueError('Product authority changed; reconcile before import')
    if existing.get('schema')!='public-commerce/v1' or existing.get('checkout',{}).get('enabled') is not False or existing['checkout'].get('url') is not None:
        raise ValueError('Commerce authority changed; checkout must stay disabled')
    if 'tiers' in existing and existing['tiers'] != commerce['tiers']:
        raise ValueError('Existing tier record changed; reconcile before import')
    for field in ['currency','unitAmount','interval','stripeProductId','stripePriceId']:
        if existing.get('plan',{}).get(field)!=commerce['plan'].get(field):
            raise ValueError('Existing payment identity changed: '+field)
    outputs={ASSET_ROOT+n:source['assets/'+n] for n in IMAGES}
    for name in RUNTIME:
        text=source[name].decode('utf-8')
        if name=='journeys.js': text=update_journeys(text)
        if name in ['app.js','journeys.js','capture-overrides.js']:
            text=text.replace('assets/','assets/reference-site/')
        if name=='app.js':
            text=text.replace('The public website and PR #51 have not been changed.', 'This implementation is under visual review. The illustrative setting and development captures are not release approval.')
            text=text.replace('href="https://javin23863.github.io/tradercockpit/docs/" target="_blank" rel="noopener noreferrer"','href="docs/"')
        outputs[ASSET_ROOT+name]=text.encode('utf-8')
    for name in ['integration.mjs','integration.css']:
        outputs[ASSET_ROOT+name]=(TEMPLATES/name).read_bytes()
    outputs['docs/index.html']=transform_html(source['index.html'].decode('utf-8'),commerce).encode('utf-8')
    outputs['docs/commerce-public.v1.json']=(json.dumps(commerce,indent=2)+'\n').encode()
    for name in REFERENCES:
        value=json.loads(source['reference/'+name])
        value.pop('source_library_file_id',None)
        outputs['.github/reference-site/provenance/'+name]=(json.dumps(value,indent=2)+'\n').encode()
    before={}
    for name in outputs:
        target=safe_target(root,name)
        if target.exists():
            if name not in {'docs/index.html','docs/commerce-public.v1.json'}: raise ValueError('Destination already exists: '+name)
            before[name]=sha(target.read_bytes())
        else: before[name]=None
    if (root/'.github/reference-import-receipt.json').exists(): raise ValueError('An import receipt already exists; use --check')
    return {'schema':'tradercockpit.reference-import-plan/v1','source_archive_sha256':SOURCE_SHA,
        'source_hashes':{k:sha(v) for k,v in source.items()},'before':before,
        'unchanged':{k:v for k,v in tree_hashes(docs).items() if 'docs/'+k not in outputs},'outputs':outputs}

def public_plan(plan: dict) -> dict:
    return {**{k:v for k,v in plan.items() if k!='outputs'},
        'outputs':{name:{'sha256':sha(data),'bytes':len(data)} for name,data in plan['outputs'].items()},
        'visual_approval':False,'served_browser_acceptance':False,'status':'NOT_READY_FOR_CODEX_REVIEW'}

def apply_plan(root: Path, plan: dict) -> None:
    root=root.resolve()
    for name,expected in plan['before'].items():
        target=safe_target(root,name)
        actual=sha(target.read_bytes()) if target.exists() else None
        if actual!=expected: raise ValueError('Destination changed after planning: '+name)
    current_public=tree_hashes(root/'docs')
    if any(current_public.get(k)!=v for k,v in plan['unchanged'].items()):
        raise ValueError('Existing public routes changed after planning')
    receipt_path=safe_target(root,'.github/reference-import-receipt.json')
    if receipt_path.exists(): raise ValueError('Destination already exists: import receipt')
    payloads={**plan['outputs'],'.github/reference-import-receipt.json':(json.dumps(public_plan(plan),indent=2)+'\n').encode()}
    backups={name:(root/name).read_bytes() if (root/name).exists() else None for name in payloads}
    written=[]
    # All inputs and current destinations are validated before touching public files.
    try:
        for name,data in payloads.items():
            target=safe_target(root,name);target.parent.mkdir(parents=True,exist_ok=True)
            fd,temp=tempfile.mkstemp(prefix='.reference-import-',dir=target.parent)
            try:
                with os.fdopen(fd,'wb') as output: output.write(data)
                os.replace(temp,target);written.append(name)
            finally:
                if os.path.exists(temp): os.unlink(temp)
        verify_installed(root,plan)
    except Exception:
        for name in reversed(written):
            target=root/name
            if backups[name] is None: target.unlink(missing_ok=True)
            else: target.write_bytes(backups[name])
        raise

def verify_installed(root: Path, plan: dict|None=None) -> dict:
    receipt=public_plan(plan) if plan else json.loads((root/'.github/reference-import-receipt.json').read_text(encoding='utf-8'))
    if receipt.get('source_archive_sha256')!=SOURCE_SHA: raise ValueError('Wrong source receipt')
    for name,item in receipt['outputs'].items():
        target=safe_target(root,name)
        if not target.is_file() or sha(target.read_bytes())!=item['sha256']:
            raise ValueError('Installed content differs: '+name)
    for name,digest in receipt['unchanged'].items():
        target=safe_target(root,'docs/'+name)
        if not target.is_file() or sha(target.read_bytes())!=digest: raise ValueError('Existing route changed: '+name)
    expected_public = set(receipt['unchanged']) | {n[5:] for n in receipt['outputs'] if n.startswith('docs/')}
    if set(tree_hashes(root/'docs')) != expected_public:
        raise ValueError('Public file set differs from the import plan')
    return {'status':'SOURCE_IMPORTED_NOT_REVIEW_READY','files':len(receipt['outputs']),
        'unchanged_existing_routes':True,'visual_approval':False,'served_browser_acceptance':False}

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path)
    p.add_argument('--root',type=Path,default=HERE.parents[1])
    group=p.add_mutually_exclusive_group();group.add_argument('--apply',action='store_true');group.add_argument('--check',action='store_true')
    args=p.parse_args(); root=args.root.resolve()
    try:
        if args.check: print(json.dumps(verify_installed(root),indent=2));return 0
        if args.apply:
            branch=subprocess.check_output(['git','-C',str(root),'branch','--show-current'],text=True).strip()
            if branch!=BRANCH: raise ValueError('Refusing to import outside the isolated integration branch')
            delta=subprocess.check_output(['git','-C',str(root),'diff','--name-only','d544de3f058d4541ab31441371ddb0656acf73a3','--','docs'],text=True).strip()
            if delta: raise ValueError('Publishing tree changed from the isolated main base; reconcile first')
        source=args.source or Path.home()/'Downloads/TraderCockpit-homepage-proof-source.zip'
        plan=make_plan(root,source)
        if args.apply: apply_plan(root,plan)
        print(json.dumps(verify_installed(root,plan) if args.apply else public_plan(plan),indent=2))
        return 0
    except (ValueError,FileNotFoundError,OSError,KeyError,zipfile.BadZipFile) as e:
        print('REFERENCE IMPORT BLOCKED: '+str(e));return 1

if __name__=='__main__': raise SystemExit(main())
