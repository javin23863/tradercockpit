import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DOCS=ROOT/'docs'
class PrivacyRuntimeContractTests(unittest.TestCase):
 def test_privacy_page_matches_research_notes_storage_runtime(self):
  runtime=(DOCS/'assets/reference-site/journeys.js').read_text(encoding='utf-8').lower()
  privacy=(DOCS/'trust/privacy.html').read_text(encoding='utf-8').lower()
  self.assertIn('localstorage',runtime)
  self.assertNotIn('current public code does not call <code>document.cookie</code>, <code>localstorage</code>',privacy)
  for marker in ('research-notes','localstorage','save on this device','clearing browser data'):
   self.assertIn(marker,privacy,marker)
 def test_privacy_page_does_not_claim_notes_are_sent_to_server(self):
  privacy=(DOCS/'trust/privacy.html').read_text(encoding='utf-8').lower()
  self.assertIn('nothing is sent to a server', (DOCS/'assets/reference-site/journeys.js').read_text(encoding='utf-8').lower())
  self.assertNotIn('research notes are sent',privacy)
if __name__=='__main__':unittest.main(verbosity=2)
