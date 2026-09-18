import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class ReviewStateTests(unittest.TestCase):
 def test_mutable_github_review_state_is_not_committed(self):
  readiness=json.loads((ROOT/'.github/website-reference-readiness.json').read_text(encoding='utf-8'))
  self.assertNotIn('codex_review_requested',readiness)
  self.assertTrue(readiness.get('codex_review_required'))
  self.assertEqual(readiness.get('codex_review_state_source'),'github_pr_external')
 def test_verifier_cannot_reintroduce_mutable_request_snapshot(self):
  text=(ROOT/'.github/scripts/verify_reference_continuity.mjs').read_text(encoding='utf-8')
  self.assertNotIn('codex_review_requested',text)
  self.assertNotIn('reviewRequested:',text)
  self.assertIn("reviewStateSource:'github_pr_external'",text)
if __name__=='__main__':unittest.main(verbosity=2)
