#!/usr/bin/env python3
"""The dollar check catches credit amounts in dollars and lets a pack's price through."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_plan_catalog import DOLLAR_CREDIT

def flagged(text):
    return any(' buys' not in text[m.start():m.end()+8] for m in DOLLAR_CREDIT.finditer(text))

class DollarCreditTests(unittest.TestCase):
    def test_flags_dollar_credit(self):
        for text in ('$4 of Apollo credit','$10 worth of credits','Apollo credit included $4 a month','$8 credit','credit: $30'):
            self.assertTrue(flagged(text),text)
    def test_allows_prices(self):
        for text in ('$10 buys 8,000 credits, $25 buys 20,000 credits','Apollo Pro $150 / month','4,000 credits a month'):
            self.assertFalse(flagged(text),text)

if __name__=='__main__':unittest.main()
