from pathlib import Path
from html.parser import HTMLParser
import unittest
ROOT=Path(__file__).resolve().parents[2];DOCS=ROOT/'docs'
class P(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':
   a=dict(attrs)
   if 'data-access-plan' in a:self.links.append(a)
class PricingFallbackTests(unittest.TestCase):
 def test_plan_links_have_static_waitlist_fallback(self):
  p=P();p.feed((DOCS/'pricing/index.html').read_text(encoding='utf-8'))
  self.assertEqual([x['data-access-plan'] for x in p.links],['Core','Trader','Quant','ApolloPro'])
  for link in p.links:self.assertEqual(link.get('href'),'../#public-status')
 def test_pricing_enhancement_is_explicit_and_local(self):
  text=(DOCS/'pricing/index.html').read_text(encoding='utf-8')
  self.assertIn("data-access-plan",text)
  self.assertIn("#/access?plan=",text)
  self.assertNotIn('href="../#/access?plan=',text)
if __name__=='__main__':unittest.main(verbosity=2)
