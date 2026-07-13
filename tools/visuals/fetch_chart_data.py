#!/usr/bin/env python3
"""Fetch daily history for video-02-hormuz charts -> build/chart-data.json.

Run with the venv that has yfinance 1.5.1:
  OpenMontage/.venv/Scripts/python.exe tools/visuals/fetch_chart_data.py
"""
import json
import sys
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent
HUB = HERE.parent.parent
OUT = HUB / "productions" / "video-02-hormuz" / "build" / "chart-data.json"

# ticker -> (period, output key)
SERIES = {
    "BZ=F": ("6mo", "brent"),
    "^GSPC": ("6mo", "spx"),
    "^VIX": ("6mo", "vix"),
    "GC=F": ("13mo", "gold"),
}

# verified fact-pack annotations (FACTS-2026-07-13.md) -- do not alter.
STATIC = {
    "brent_sun_reopen": 78.67,
    "brent_fri_close": 76.56,
    "brent_mar_peak": 126,
    "spx_fri": 7575.39,
    "vix_fri": 15.03,
    "gold_ath": 5595,          # dated 2026-01-28
    "gold_now": 4100,
    "dxy": 100.94,
    "ust10y": 4.56,
}


def fetch_one(ticker, period):
    df = yf.download(ticker, period=period, interval="1d", progress=False,
                      multi_level_index=False)
    if df is None or df.empty:
        sys.exit(f"FAIL: empty history for {ticker} (period={period})")
    closes = df["Close"].dropna()
    if closes.empty:
        sys.exit(f"FAIL: no Close data for {ticker}")
    return {
        "dates": [d.strftime("%Y-%m-%d") for d in closes.index],
        "closes": [round(float(v), 4) for v in closes.values],
    }


def main():
    data = {}
    for ticker, (period, key) in SERIES.items():
        print(f"[fetch] {ticker} period={period} -> {key}")
        data[key] = fetch_one(ticker, period)
        n = len(data[key]["closes"])
        print(f"  {n} bars, last={data[key]['dates'][-1]} close={data[key]['closes'][-1]}")

    data["static"] = STATIC

    # sanity: latest Brent close should be in the 70s-80s
    brent_last = data["brent"]["closes"][-1]
    if not (60 <= brent_last <= 100):
        sys.exit(f"FAIL sanity check: latest Brent close {brent_last} outside 60-100 range")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
