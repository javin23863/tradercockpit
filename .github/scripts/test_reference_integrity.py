import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('reference_check',HERE/'check_reference_site.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class IntegrityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  shutil.copytree(ROOT/'docs',self.root/'docs')
  for file in ['.github/reference-import-receipt.json','.github/reference-site/provenance/product-captures.json','.github/reference-site/provenance/screen-placement.json','.github/reference-site/provenance/production-screen-layers.json','.github/reference-content-manifest.json','.github/reference-site/ux-contracts-before.json','.github/scripts/generate_reference_screen_layers.mjs']:
   p=self.root/file;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/file,p)
 def tearDown(self):self.tmp.cleanup()
 def alter(self,name,action):
  p=self.root/name;p.write_bytes(action(p.read_bytes()))
 def test_current_import_and_adaptations(self):self.assertEqual(module.validate(self.root),[])
 def test_scene_substitution_rejected(self):
  self.alter('docs/assets/reference-site/room-scene.webp',lambda b:b+b'changed');self.assertTrue(module.validate(self.root))
 def test_original_capture_substitution_rejected(self):
  self.alter('docs/assets/reference-site/original-models.png',lambda b:b[:-20]);self.assertTrue(module.validate(self.root))
 def test_screen_layer_substitution_rejected(self):
  self.alter('docs/assets/reference-site/room-screen.webp',lambda b:b+b'unverified');self.assertTrue(module.validate(self.root))
 def test_screen_layer_source_downgrade_rejected(self):
  p=self.root/'.github/reference-site/provenance/production-screen-layers.json';s=p.read_text(encoding='utf-8').replace('original-charts.png','product-charts.webp',1);p.write_text(s,encoding='utf-8');self.assertTrue(module.validate(self.root))
 def test_homepage_noindex_rejected(self):
  self.alter('docs/index.html',lambda b:b.replace(b'<meta name="theme-color" content="#080b0b">',b'<meta name="theme-color" content="#080b0b"><meta name="robots" content="noindex,nofollow">'));self.assertTrue(module.validate(self.root))
 def test_internal_preview_copy_rejected(self):
  self.alter('docs/assets/reference-site/app.js',lambda b:b+b"\n// Homepage proof under visual review\n");self.assertTrue(module.validate(self.root))
 def test_journey_preview_copy_rejected(self):
  self.alter('docs/assets/reference-site/journeys.js',lambda b:b+b"\n// This preview does not contain this route.\n");self.assertTrue(module.validate(self.root))
 def test_price_drift_rejected(self):
  self.alter('docs/commerce-public.v1.json',lambda b:b.replace(b'1999',b'2999'));self.assertTrue(module.validate(self.root))
 def test_signup_fail_open_rejected(self):
  self.alter('docs/index.html',lambda b:b.replace(b'class="reference-waitlist" method="post" hidden',b'class="reference-waitlist" method="post"'));self.assertTrue(module.validate(self.root))
 def test_unlisted_raw_artwork_rejected(self):
  (self.root/'docs/assets/reference-site/raw-mockup.png').write_bytes(b'unlisted artwork');self.assertTrue(module.validate(self.root))
 def test_article_text_change_rejected(self):
  self.alter('docs/docs/index.html',lambda b:b.replace(b'Three kinds of answer.',b'Changed article content.'));self.assertTrue(module.validate(self.root))
 def test_article_link_change_rejected(self):
  self.alter('docs/docs/index.html',lambda b:b.replace(b'../how-to/',b'../wrong-guide/'));self.assertTrue(module.validate(self.root))
 def test_reading_css_drift_rejected(self):
  self.alter('docs/assets/reference-site/content.css',lambda b:b+b'/* unreviewed */');self.assertTrue(module.validate(self.root))
if __name__=='__main__':unittest.main(verbosity=2)
