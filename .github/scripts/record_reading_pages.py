#!/usr/bin/env python3
"""Record the current public page fingerprints in .github/reference-content-manifest.json.

Every page whose bytes changed gets the stated reason appended to its correction note, so a
change is never recorded silently. Run it after editing published pages, then rerun
check_reference_site.py. It records structure only; it never grants visual approval.

usage: record_reading_pages.py "reason" [--add docs-relative-path ...] [--drop docs-relative-path ...]
"""
from pathlib import Path
import argparse,hashlib,json,shutil,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from reference_content import unwrap_html
ROOT=Path(__file__).resolve().parents[2];DOCS=ROOT/'docs';MANIFEST=ROOT/'.github/reference-content-manifest.json'
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('reason');ap.add_argument('--add',nargs='*',default=[]);ap.add_argument('--drop',nargs='*',default=[])
    args=ap.parse_args();reason=args.reason.strip()
    if not reason:raise SystemExit('A reason is required')
    m=json.loads(MANIFEST.read_text(encoding='utf-8'));changed=[]
    home=(DOCS/'index.html').read_bytes()
    if sha(home)!=m['home_sha256']:changed.append('index.html')
    m['home_sha256']=sha(home);shutil.copyfile(DOCS/'index.html',ROOT/'.github/reference-site/homepage.html')
    for name,row in m['files'].items():
        raw=(DOCS/name).read_bytes()
        if sha(raw)==row['after_sha256']:continue
        changed.append(name);row['after_sha256']=sha(raw)
        if row['kind'] in {'reading_shell','corrected_reading_shell'}:
            row['kind']='corrected_reading_shell'
            row['corrected_unwrapped_sha256']=sha(unwrap_html(raw.decode('utf-8')).encode('utf-8'))
            note=row.get('correction','').strip()
            row['correction']=note if reason in note else (note+' '+reason).strip()
    for name,row in m.get('approved_updates',{}).items():
        p=DOCS/name
        if p.is_file() and sha(p.read_bytes())!=row['after_sha256']:
            changed.append(name);row['after_sha256']=sha(p.read_bytes())
            if reason not in row['reason']:row['reason']=(row['reason'].strip()+' '+reason).strip()
    added=m.setdefault('added_files',{})
    for name in args.drop:
        added.pop(name,None);m.get('new_assets',{}).pop(name,None);m.get('approved_updates',{}).pop(name,None)
    for name in list(added)+args.add:
        p=DOCS/name
        if not p.is_file():raise SystemExit('Missing added file: '+name)
        if added.get(name)!=sha(p.read_bytes()):changed.append(name)
        added[name]=sha(p.read_bytes())
    for name in list(m.get('new_assets',{})):
        if not (DOCS/name).is_file():raise SystemExit('Listed reading asset is gone; pass --drop '+name)
    MANIFEST.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
    print('Recorded '+str(len(changed))+' changed public files')
    for name in changed:print('- '+name)

if __name__=='__main__':main()
