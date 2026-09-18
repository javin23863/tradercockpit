"""Verify additive reading-shell migration; never award visual readiness."""
from pathlib import Path
import hashlib,json
from reference_content import unwrap_html
from reference_contracts import refresh_contracts,serialize_contracts
sha=lambda b:hashlib.sha256(b).hexdigest()
GUARD="    if (document.body.hasAttribute('data-reference-content')) return;\n"
ESCAPE_BLOCK="    dialog.addEventListener('keydown', (event) => {\n      if (event.key !== 'Escape') return;\n      event.preventDefault();\n      event.stopPropagation();\n      closeDialog();\n    });\n"
def validate_content(root):
    root=Path(root);docs=root/'docs';errors=[]
    try:
        m=json.loads((root/'.github/reference-content-manifest.json').read_text(encoding='utf-8'))
        receipt=json.loads((root/'.github/reference-import-receipt.json').read_text(encoding='utf-8'))
        if m.get('schema')!='tradercockpit.reference-reading-shell/v1':errors.append('Unknown reading-shell manifest')
        if sha((docs/'index.html').read_bytes())!=m['home_sha256']:errors.append('Homepage changed during content migration')
        for name,row in m['files'].items():
            p=docs/name
            if not p.resolve().is_relative_to(docs.resolve()):raise ValueError('Unsafe reading-shell path')
            raw=p.read_bytes();text=raw.decode('utf-8')
            restored=unwrap_html(text) if row['kind']=='reading_shell' else text.replace(GUARD,'',1).replace(ESCAPE_BLOCK,'',1) if row['kind']=='search_guard' else None
            if row['kind']=='ux_contracts':
                baseline=(root/'.github/reference-site/ux-contracts-before.json').read_bytes()
                if sha(baseline)!=row['before_sha256'] or serialize_contracts(refresh_contracts(json.loads(baseline)))!=raw:errors.append('UX contract migration differs: '+name)
            elif restored is None or sha(restored.encode('utf-8'))!=row['before_sha256']:errors.append('Article or behavior preservation failed: '+name)
            if sha(raw)!=row['after_sha256']:errors.append('Unreviewed reading-shell change: '+name)
            if name!='pricing/index.html' and receipt['unchanged'].get(name)!=row['before_sha256']:errors.append('Unexpected previous content identity: '+name)
        for name,digest in m['new_assets'].items():
            if name!='assets/reference-site/content.css' or sha((docs/name).read_bytes())!=digest:errors.append('Reading stylesheet changed: '+name)
    except (OSError,ValueError,KeyError,TypeError) as exc:errors.append(str(exc))
    return errors
