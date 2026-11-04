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
    def rows(self):
        return json.loads((Path(__file__).resolve().parents[1]/'product/brokers.v1.json').read_text(encoding='utf-8'))['institutions']
    def test_every_broker_is_named_once_and_counted(self):
        data=load();b=data['brokers'];rows=self.rows()
        self.assertEqual(b['open'],len(rows));self.assertEqual(len(set(b['trade']+b['read'])),len(rows))
        self.assertEqual(data['paidByArea']['brokers'],f'{len(rows)} brokers')
        named=' '.join(b['trade']+b['read'])
        for row in rows.values():self.assertIn(row['name'],named)
    def test_chart_orders_name_trading_routes_only(self):
        data=json.loads((Path(__file__).resolve().parents[1]/'product/brokers.v1.json').read_text(encoding='utf-8'))
        for key in data['chartOrders']:self.assertTrue(any(v['trading'] for v in data['institutions'][key]['routes'].values()),key)
    def test_view_only_routes_never_show_as_trading(self):
        trade=load()['brokers']['trade']
        for row in self.rows().values():
            if not any(v['trading'] for v in row['routes'].values()):
                self.assertFalse(any(n.startswith(row['name']) for n in trade),row['name'])

if __name__=='__main__':unittest.main()
