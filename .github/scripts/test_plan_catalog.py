#!/usr/bin/env python3
"""The dollar check catches credit amounts in dollars and lets a pack's price through."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_plan_catalog import DOLLAR_CREDIT
from generate_product_pages import load
import json

def flagged(text):
    return any(' buys' not in text[m.start():m.end()+8] for m in DOLLAR_CREDIT.finditer(text))

class DollarCreditTests(unittest.TestCase):
    def test_flags_dollar_credit(self):
        for text in ('$4 of Apollo credit','$10 worth of credits','Apollo credit included $4 a month','$8 credit','credit: $30'):
            self.assertTrue(flagged(text),text)
    def test_allows_prices(self):
        for text in ('$10 buys 8,000 credits, $25 buys 20,000 credits','Apollo Pro $150 / month','4,000 credits a month'):
            self.assertFalse(flagged(text),text)

class BrokerTests(unittest.TestCase):
    def test_every_broker_is_named_once_and_counted(self):
        data=load();b=data['brokers']
        rows=json.loads((Path(__file__).resolve().parents[2]/'docs/brokers.v1.json').read_text(encoding='utf-8'))['institutions']
        opened=[r for r in rows.values() if any(v['enabled'] for v in r['routes'].values())]
        self.assertEqual(b['open'],len(opened));self.assertEqual(len(b['trade'])+len(b['read']),len(opened))
        self.assertEqual(len(set(b['trade']+b['read'])),len(opened))
        self.assertEqual(data['paidByArea']['brokers'],f'{len(opened)} brokers')
        named=' '.join(b['trade']+b['read']+b['closed'])
        for row in rows.values():self.assertIn(row['name'],named)
    def test_read_only_routes_never_show_as_trading(self):
        rows=json.loads((Path(__file__).resolve().parents[2]/'docs/brokers.v1.json').read_text(encoding='utf-8'))['institutions']
        for row in rows.values():
            if not any(v['trading'] for v in row['routes'].values()):
                self.assertFalse(any(n.startswith(row['name']) for n in load()['brokers']['trade']),row['name'])

if __name__=='__main__':unittest.main()
