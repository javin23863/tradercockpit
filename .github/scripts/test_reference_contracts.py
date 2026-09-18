import json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE))
from reference_contracts import refresh_contracts
class ContractTests(unittest.TestCase):
 def test_live_metadata_records_owner_visual_approval(self):
  value=json.loads((ROOT/'docs/ux-page-contracts.v1.json').read_text(encoding='utf-8'))
  readiness=json.loads((ROOT/'.github/website-reference-readiness.json').read_text(encoding='utf-8'))
  self.assertIn('does not grant visual approval',value.get('audit_scope',''))
  self.assertEqual(readiness['gates']['owner_visual_acceptance_of_integrated_result'],'complete; owner approved exact integrated visual candidate on 2026-09-18')
  expected={'status':'owner_visual_approved','visual_approval':True,'approved_at':'2026-09-18','source':'owner'}
  for row in value['pages']:self.assertEqual(row['audit'],expected)
 def test_structural_refresh_cannot_grant_visual_approval(self):
  baseline=json.loads((ROOT/'.github/reference-site/ux-contracts-before.json').read_text(encoding='utf-8'))
  refreshed=refresh_contracts(baseline)
  for row in refreshed['pages']:self.assertEqual(row['audit'],{'status':'pending_visual_review','visual_approval':False})
 def test_four_plan_metadata_is_current(self):
  value=json.loads((ROOT/'docs/ux-page-contracts.v1.json').read_text(encoding='utf-8'))
  pricing=next(row for row in value['pages'] if row['path']=='pricing/index.html')
  self.assertEqual(pricing['reviewed_h1'],'Four monthly plans. One research environment.')
 def test_public_authority_contract_is_split_and_does_not_duplicate_mutable_counts(self):
  readme=(ROOT/'README.md').read_text(encoding='utf-8')
  reference_readme=(ROOT/'.github/reference-site/README.md').read_text(encoding='utf-8')
  self.assertIn('docs/product-manifest.v1.json',readme)
  self.assertIn('docs/commerce-public.v1.json',readme)
  self.assertIn('docs/prelaunch-config.v1.json',readme)
  self.assertNotIn('the ONLY source of product availability, pricing, platform support and checkout state',readme)
  self.assertIn('public plan names, prices, and checkout state',readme)
  self.assertNotRegex(reference_readme,r'\b\d+ mutation tests\b')
 def test_transform_preserves_route_set_and_analytical_palette(self):
  value=json.loads((ROOT/'docs/ux-page-contracts.v1.json').read_text(encoding='utf-8'))
  baseline=json.loads((ROOT/'.github/reference-site/ux-contracts-before.json').read_text(encoding='utf-8'))
  copy=refresh_contracts(baseline,owner_visual_approval=True,approved_at='2026-09-18')
  self.assertEqual([x['path'] for x in copy['pages']],[x['path'] for x in value['pages']])
  old=next(x for x in value['pages'] if x['path']=='research-lab.html');new=next(x for x in copy['pages'] if x['path']==old['path'])
  self.assertEqual(old['visual_character'],new['visual_character'])
if __name__=='__main__':unittest.main(verbosity=2)
