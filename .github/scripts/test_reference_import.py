"""Test exact source custody and non-destructive import. No visual sign-off."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('import_reference_site.py')
ARCHIVE = Path(os.environ.get('TC_REFERENCE_ARCHIVE', str(Path.home()/'Downloads/TraderCockpit-homepage-proof-source.zip')))

class ReferenceImportTests(unittest.TestCase):
    def test_implementation_is_available(self):
        self.assertTrue(SCRIPT.is_file(), 'The executable reference-site importer is missing.')

    def setUp(self):
        if self._testMethodName == 'test_implementation_is_available': return
        if not SCRIPT.is_file():
            self.skipTest('Import feature not implemented yet')
        spec = importlib.util.spec_from_file_location('reference_import', SCRIPT)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root/'docs/learn').mkdir(parents=True)
        (root/'docs/index.html').write_text('<!doctype html><title>Existing site</title>\n')
        (root/'docs/learn/index.html').write_bytes(b'Historical route: preserve exact bytes.\n')
        (root/'docs/product-manifest.v1.json').write_text(json.dumps({'schema':'product-manifest/v1','status':'waitlist','verifiedCapabilities':[]}))
        commerce = {'schema':'public-commerce/v1','status':'prelaunch','plan':{'name':'TraderCockpit Monthly','currency':'USD','unitAmount':15000,'interval':'month','stripeProductId':'prod_V6DR67MaZGMMH4','stripePriceId':'price_1U610SQtj95EgxLw0cdceJ4d'},'checkout':{'enabled':False,'url':None,'reason':'Checkout opens after payment-to-entitlement provisioning is verified end to end.'}}
        (root/'docs/commerce-public.v1.json').write_text(json.dumps(commerce))
        (root/'docs/prelaunch-config.v1.json').write_text('{"schema":"prelaunch-config/v1"}')
        return root

    def test_wrong_archive_rejected_before_writes(self):
        root=self.fixture(); bad=root/'wrong.zip'; bad.write_bytes(b'not the authorised archive')
        before=self.mod.tree_hashes(root/'docs')
        with self.assertRaisesRegex(ValueError, 'Source archive SHA-256'):
            self.mod.make_plan(root,bad)
        self.assertEqual(before,self.mod.tree_hashes(root/'docs'))

    def test_unavailable_archive_is_explicit(self):
        root=self.fixture()
        with self.assertRaisesRegex(FileNotFoundError,'source ZIP'):
            self.mod.make_plan(root,root/'missing.zip')

    @unittest.skipUnless(ARCHIVE.is_file(), 'Exact source ZIP not installed on this machine')
    def test_exact_import_preserves_art_and_other_routes(self):
        root=self.fixture(); plan=self.mod.make_plan(root,ARCHIVE)
        before=self.mod.tree_hashes(root/'docs')
        self.assertEqual(before,self.mod.tree_hashes(root/'docs'), 'Planning must not write')
        self.assertIn('docs/index.html',plan['outputs'])
        for forbidden in ['room.webp','laptop.webp','source.png']:
            self.assertFalse(any(p.endswith('/'+forbidden) for p in plan['outputs']))
        self.mod.apply_plan(root,plan)
        self.assertEqual((root/'docs/learn/index.html').read_bytes(),b'Historical route: preserve exact bytes.\n')
        self.assertEqual(json.loads((root/'docs/product-manifest.v1.json').read_text())['status'],'waitlist')
        self.assertEqual(before['product-manifest.v1.json'],self.mod.tree_hashes(root/'docs')['product-manifest.v1.json'])
        for scene in ['room-scene.webp','laptop-scene.webp','room-screen.webp','laptop-screen.webp']:
            path='docs/assets/reference-site/'+scene
            self.assertEqual(hashlib.sha256((root/path).read_bytes()).hexdigest(),plan['source_hashes']['assets/'+scene])
        html=(root/'docs/index.html').read_text()
        self.assertIn('rel="canonical"',html)
        self.assertIn('id="public-status"',html)
        self.assertIn('id="waitlist-form"',html)
        self.assertIn('id="commerce-snapshot"',html)
        self.assertIn('href="learn/" data-journey="#/learn"',html)
        self.assertIn('href="support/"',html)
        self.assertNotIn('site-webgl-v1.js',html)
        self.assertEqual(json.loads((root/'docs/commerce-public.v1.json').read_text())['tiers'][0]['unitAmount'],1999)
        self.assertTrue(self.mod.verify_installed(root,plan)['unchanged_existing_routes'])

    @unittest.skipUnless(ARCHIVE.is_file(), 'Exact source ZIP not installed on this machine')
    def test_conflicting_new_asset_is_never_overwritten(self):
        root=self.fixture(); folder=root/'docs/assets/reference-site'; folder.mkdir(parents=True)
        (folder/'app.js').write_text('someone else is editing here')
        with self.assertRaisesRegex(ValueError,'Destination already exists'):
            self.mod.make_plan(root,ARCHIVE)
        self.assertEqual((folder/'app.js').read_text(),'someone else is editing here')

    @unittest.skipUnless(ARCHIVE.is_file(), 'Exact source ZIP not installed on this machine')
    def test_source_output_drift_rejected(self):
        root=self.fixture(); plan=self.mod.make_plan(root,ARCHIVE)
        (root/'docs/index.html').write_text('another agent changed the homepage')
        with self.assertRaisesRegex(ValueError,'changed after planning'):
            self.mod.apply_plan(root,plan)
        self.assertFalse((root/'docs/assets/reference-site').exists())

    @unittest.skipUnless(ARCHIVE.is_file(), 'Exact source ZIP not installed on this machine')
    def test_unsupported_product_or_commerce_fails_closed(self):
        for change in ['available','checkout','payment-id']:
            root=self.fixture()
            if change=='available':
                (root/'docs/product-manifest.v1.json').write_text('{"status":"available"}')
            else:
                target=root/'docs/commerce-public.v1.json'; data=json.loads(target.read_text())
                if change=='checkout': data['checkout']['enabled']=True
                else: data['plan']['stripePriceId']='a-different-price'
                target.write_text(json.dumps(data))
            with self.assertRaises(ValueError): self.mod.make_plan(root,ARCHIVE)

    @unittest.skipUnless(ARCHIVE.is_file(), 'Exact source ZIP not installed on this machine')
    def test_verify_detects_tampering_without_upgrading_readiness(self):
        root=self.fixture(); plan=self.mod.make_plan(root,ARCHIVE); self.mod.apply_plan(root,plan)
        (root/'docs/assets/reference-site/room-scene.webp').write_bytes(b'changed scene')
        with self.assertRaisesRegex(ValueError,'Installed content differs'):
            self.mod.verify_installed(root,plan)
        receipt=json.loads((root/'.github/reference-import-receipt.json').read_text())
        self.assertFalse(receipt['visual_approval'])
        self.assertFalse(receipt['served_browser_acceptance'])

    @unittest.skipUnless(ARCHIVE.is_file(), 'Exact source ZIP not installed on this machine')
    def test_changed_tiers_are_not_silently_replaced(self):
        root=self.fixture(); path=root/'docs/commerce-public.v1.json'; data=json.loads(path.read_text())
        data['tiers']=[{'name':'Core','unitAmount':9999,'interval':'month'}]; path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'tier'):
            self.mod.make_plan(root,ARCHIVE)

    @unittest.skipUnless(ARCHIVE.is_file(), 'Exact source ZIP not installed on this machine')
    def test_unlisted_public_file_is_not_accepted(self):
        root=self.fixture(); plan=self.mod.make_plan(root,ARCHIVE); self.mod.apply_plan(root,plan)
        (root/'docs/assets/reference-site/unlisted.txt').write_text('unapproved file')
        with self.assertRaisesRegex(ValueError,'file set'):
            self.mod.verify_installed(root,plan)

if __name__=='__main__': unittest.main(verbosity=2)
