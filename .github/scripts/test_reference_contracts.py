import json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE))
from reference_contracts import refresh_contracts
class ContractTests(unittest.TestCase):
 def test_live_metadata_does_not_claim_visual_approval(self):
  value=json.loads((ROOT/'docs/ux-page-contracts.v1.json').read_text(encoding='utf-8'))
  self.assertIn('Structural contracts only',value.get('audit_scope',''))
  for row in value['pages']:self.assertEqual(row['audit'],{'status':'pending_visual_review','visual_approval':False})
 def test_four_plan_metadata_is_current(self):
  value=json.loads((ROOT/'docs/ux-page-contracts.v1.json').read_text(encoding='utf-8'))
  pricing=next(row for row in value['pages'] if row['path']=='pricing/index.html')
  self.assertEqual(pricing['reviewed_h1'],'Four monthly plans. One research environment.')
 def test_transform_preserves_route_set_and_analytical_palette(self):
  value=json.loads((ROOT/'docs/ux-page-contracts.v1.json').read_text(encoding='utf-8'))
  copy=refresh_contracts(value)
  self.assertEqual([x['path'] for x in copy['pages']],[x['path'] for x in value['pages']])
  old=next(x for x in value['pages'] if x['path']=='research-lab.html');new=next(x for x in copy['pages'] if x['path']==old['path'])
  self.assertEqual(old['visual_character'],new['visual_character'])
if __name__=='__main__':unittest.main(verbosity=2)
