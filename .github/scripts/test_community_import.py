import json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import generate_community_pages as g

A='a'*64;B='b'*64
def item(i,kind='idea',title='An idea',when='2026-11-01T00:00:00Z',**extra):
    row={'id':i,'kind':kind,'title':title,'description':'','author':{'name':'Pat','handle':'pat'},'published_at':when,'market':None,'timeframe':None,'image':None,kind:{'note':'x'} if kind=='idea' else {}}
    row.update(extra);return row
def response(*rows):return json.dumps({'schema':g.SCHEMA,'items':list(rows)}).encode()

class ImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=Path(tempfile.mkdtemp());self.saved=(g.COMMUNITY,g.ITEMS,g.fetch)
        g.COMMUNITY=self.tmp/'community';g.COMMUNITY.mkdir();g.ITEMS=g.COMMUNITY/'items.v1.json'
        g.ITEMS.write_text(json.dumps({'schema':g.SCHEMA,'items':[item(A,title='Old title')]}),encoding='utf-8')
    def tearDown(self):g.COMMUNITY,g.ITEMS,g.fetch=self.saved
    def items(self):return json.loads(g.ITEMS.read_text(encoding='utf-8'))['items']

    def test_local_merge_by_id_newest_first_with_beside_image(self):
        src=self.tmp/'in';(src/'img').mkdir(parents=True);(src/'img'/f'{B}.png').write_bytes(b'png')
        (src/'items.json').write_bytes(response(item(A,title='New title'),item(B,when='2026-11-05T00:00:00Z',image=f'img/{B}.png',extra='dropped')))
        self.assertEqual(g.import_items(str(src/'items.json')),2)
        rows=self.items()
        self.assertEqual([r['id'] for r in rows],[B,A])
        self.assertEqual(rows[1]['title'],'New title')
        self.assertEqual(rows[0]['image'],f'img/{B}.png');self.assertEqual((g.COMMUNITY/'img'/f'{B}.png').read_bytes(),b'png')
        self.assertNotIn('extra',rows[0])

    def test_remote_image_comes_from_service_origin(self):
        calls=[]
        def fake(url,limit):
            calls.append(url)
            return (response(item(B,image=f'/v1/community/items/{B}/image')),'application/json') if url.endswith('/items') else (b'jpg','image/jpeg')
        g.fetch=fake
        g.import_items('https://accounts.example.com/v1/community/items')
        self.assertEqual(calls[1],f'https://accounts.example.com/v1/community/items/{B}/image')
        self.assertEqual(next(r for r in self.items() if r['id']==B)['image'],f'img/{B}.jpg')

    def test_bad_rows_and_types_are_skipped(self):
        bad=self.tmp/'bad.json'
        for row in (item('A'*64),item(B,kind='video'),{**item(B),'author':{'name':'Pat','handle':'Pat!'}},item(B,kind='strategy',strategy={'rules':[1]}),item(B,market='m'*81)):
            bad.write_bytes(response(row,item('c'*64,market='m'*80)))
            self.assertEqual(g.import_items(str(bad)),1)
        g.fetch=lambda url,limit:(response(item(B,image=f'/v1/community/items/{B}/image')),'') if url.endswith('/items') else (b'<svg>','image/svg+xml')
        self.assertEqual(g.import_items('https://accounts.example.com/v1/community/items'),0)
        with self.assertRaises(SystemExit):g.import_items('http://accounts.example.com/v1/community/items')
        self.assertNotIn(B,[r['id'] for r in self.items()])

    def test_remote_import_drops_unpublished_service_items_and_keeps_seeds(self):
        g.fetch=lambda url,limit:(response(item(B)),'application/json')
        g.import_items('https://accounts.example.com/v1/community/items')
        self.assertEqual({r['id'] for r in self.items()},{A,B})
        g.fetch=lambda url,limit:(response(),'application/json')
        g.import_items('https://accounts.example.com/v1/community/items')
        self.assertEqual([r['id'] for r in self.items()],[A])

if __name__=='__main__':unittest.main(verbosity=2)
