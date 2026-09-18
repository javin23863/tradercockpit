"""Keep structural page contracts separate from human visual approval."""
import copy,json

def refresh_contracts(original, *, owner_visual_approval=False, approved_at=None):
    data=copy.deepcopy(original)
    data['reviewed_at']='2026-09-18'
    data['audit_scope']='Structural contract generation does not grant visual approval. Current visual approval is owner-provided and recorded in .github/website-reference-readiness.json.'
    for row in data['pages']:
        row['audit']=({'status':'owner_visual_approved','visual_approval':True,'approved_at':approved_at,'source':'owner'} if owner_visual_approval else {'status':'pending_visual_review','visual_approval':False})
        if row['path']!='research-lab.html':
            row['visual_character']['color']='Warm dark surfaces, ivory text, restrained gold navigation and action accents. Analytical images retain their source colors.'
        if row['path']=='index.html':
            row['title']='TraderCockpit — Quant research environment'
            row['reviewed_h1']='A Complete Quant Research Environment'
            row['hierarchy']['focal_point']=row['reviewed_h1']
            row['hierarchy']['primary_action']='Explore access'
        if row['path']=='pricing/index.html':
            row['reviewed_h1']='Four monthly plans. One research environment.'
            row['hierarchy']['focal_point']=row['reviewed_h1']
            row['intent']['primary_job']='Compare the four published monthly plans and inspect access availability.'
            row['intent']['worst_mistake']='Believing checkout is open or treating a plan name as a verified feature entitlement.'
    return data

def serialize_contracts(value):
    return (json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
