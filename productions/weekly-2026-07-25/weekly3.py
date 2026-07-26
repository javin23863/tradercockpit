#!/usr/bin/env python3
"""Weekly 1W read with a stale-carry guard.

The failure mode seen twice: after a symbol switch, `quote`/`ohlcv` keep serving the
PREVIOUS symbol's bar while `state` already reports the new symbol. It shows up as the
identical close repeating across unrelated instruments (every symbol returned 333.02).

Guard: accept a read only when the quote's own symbol matches the request AND the bar
differs from the previously accepted bar. Anything else is retried, then recorded FAILED.
"""
import json
import subprocess
import time
from datetime import datetime, timezone

TV = "/root/tradingview-mcp/src/cli/index.js"
SYMBOLS = [
    ("TVC:UKOIL", "Brent"), ("SP:SPX", "S&P 500"), ("NASDAQ:NDX", "Nasdaq 100"),
    ("TVC:US10Y", "US 10Y"), ("TVC:DXY", "Dollar index"), ("TVC:GOLD", "Gold"),
    ("TVC:VIX", "VIX"), ("AMEX:XLE", "Energy (XLE)"),
    ("NASDAQ:MU", "Micron"), ("NASDAQ:AAPL", "Apple"), ("NYSE:OXY", "Occidental"),
]


def tv(*a, timeout=90):
    try:
        return json.loads(subprocess.run(["node", TV, *a], capture_output=True,
                                         text=True, timeout=timeout).stdout)
    except Exception:
        return {"success": False}


out, seen = {}, set()
for sym, label in SYMBOLS:
    ticker = sym.split(":")[-1]
    tv("symbol", sym)
    rec = {"label": label, "requested": sym, "ok": False}
    for _ in range(10):
        time.sleep(6)
        q = tv("quote")
        if not q.get("success") or q.get("symbol", "").split(":")[-1] != ticker:
            continue
        bars = tv("ohlcv", "--count", "3")
        b = bars.get("bars") or []
        if len(b) < 2:
            continue
        last, prev = b[-1], b[-2]
        fp = (last["open"], last["high"], last["low"], last["close"])
        if fp in seen:                      # stale carry-over from the previous symbol
            continue
        if abs(last["close"] - float(q["close"])) > 1e-6:
            continue                        # quote and bar must be the same series
        seen.add(fp)
        rec.update(ok=True, state_symbol=q["symbol"],
                   week_start_utc=datetime.fromtimestamp(last["time"], timezone.utc).strftime("%Y-%m-%d %a"),
                   bar={k: last[k] for k in ("open", "high", "low", "close")},
                   prev_close=prev["close"],
                   chg_pct=round((last["close"] - prev["close"]) / prev["close"] * 100, 2) if prev["close"] else None)
        break
    out[sym] = rec
    if rec["ok"]:
        print(f'{label:14} {rec["state_symbol"]:18} O {rec["bar"]["open"]:>10} H {rec["bar"]["high"]:>10} '
              f'L {rec["bar"]["low"]:>10} C {rec["bar"]["close"]:>10}  {rec["chg_pct"]:>7}%  wk {rec["week_start_utc"]}', flush=True)
    else:
        print(f'{label:14} FAILED (stale or unverifiable) — no number recorded', flush=True)

p = "/tmp/claude-0/-root-Desktop/e00498aa-26e3-4a88-b28c-f105f1fcf7b8/scratchpad/weekly-final.json"
json.dump({"retrieved_at": datetime.now(timezone.utc).isoformat(),
           "feed": "TradingView Desktop 3.3.0 via tradingview-mcp CDP 9222 (unauthenticated session)",
           "guard": "quote-symbol match + distinct-bar (stale-carry) + quote==bar close",
           "series": out}, open(p, "w"), indent=2)
print("\nwrote", p)
