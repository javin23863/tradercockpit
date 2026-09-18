import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DOCS=ROOT/'docs'
class PublicJourneySourceTests(unittest.TestCase):
 def test_public_journey_source_links_use_current_local_site(self):
  text=(DOCS/'assets/reference-site/journeys.js').read_text(encoding='utf-8')
  self.assertNotIn('github.com/javin23863/tradercockpit/blob/',text)
  self.assertNotIn('const SOURCE =',text)
  for rel in ['learn/concepts/monte-carlo.html','strategy-claim-audit-checklist.html','commerce-public.v1.json']:
   self.assertTrue((DOCS/rel).is_file(),rel)
 def test_public_runtime_does_not_expose_rejected_website_commit(self):
  for p in (DOCS/'assets/reference-site').glob('*.js'):
   self.assertNotIn('8e596f6f5c57fd56a07cb8875db27ac18c76333d',p.read_text(encoding='utf-8'),p.as_posix())
if __name__=='__main__':unittest.main(verbosity=2)
