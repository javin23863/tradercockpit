#!/usr/bin/env python3
"""Emit the daily chart plan from the session feed + swing receipts.

Draws exactly what the script is expected to speak, because `editorial_gate` binds the two:
every horizontal line drawn must be spoken and every level spoken must be drawn. Three
session levels plus the nearest swing level is what fits on a readable chart -- more lines
means more sentences owed, and the recital cap caps those at five per instrument anyway.
Trendlines are exempt from the binding (swing anchors are not quoted figures), so they are
free depth.

    python tools/visuals/build_daily_chart_plan.py productions/daily-<date>
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

# out-name -> symbol, in the order the video walks them
CHARTS = [("03-spx", "SP:SPX"), ("04-nasdaq", "NASDAQ:IXIC"), ("05-xlk", "AMEX:XLK"),
          ("06-nvda", "NASDAQ:NVDA"), ("07-vix", "CBOE:VIX")]
PRIOR, HIGH, LOW, SWING = "#FFB000", "#F23645", "#22AB94", "#B8B8B8"
# Trendlines get their OWN two colours. Reusing PRIOR/LOW put the resistance line in the same
# orange as the prior-close level and the support line in the same green as the session low,
# so the two things the viewer is asked to tell apart were drawn identically.
TL_RESISTANCE, TL_SUPPORT = "#B14BF4", "#4B9BF4"


def line(price, colour):
    return {"type": "horizontal_line", "price": round(float(price), 4),
            "overrides": {"linecolor": colour, "linewidth": 2}}


def build(production):
    root = Path(production)
    feed = json.loads(next(iter(sorted(glob.glob(str(root / "ohlcv-feed-receipts*.json")))
                               ), "")and Path(sorted(glob.glob(str(root / "ohlcv-feed-receipts*.json")))[0]).read_text(encoding="utf-8"))
    swing = json.loads(Path(sorted(glob.glob(str(root / "swing-receipts*.json")))[0]).read_text(encoding="utf-8"))
    plan = []
    for out, symbol in CHARTS:
        bar = feed["dashboard"][symbol]
        entry = swing["instruments"][symbol]
        close = bar["session"]["close"]
        session_ts = entry["barsWindow"]["to"]   # last bar in the window == the session charted
        # The four the script quotes, and nothing more. `session_close` is a level predicate,
        # so quoting the close obliges drawing it; four levels plus the day's return is
        # exactly the recital cap of five per (section, instrument), which is the point --
        # the section has to earn its length with mechanism instead of more digits.
        # Swing levels stay OFF the chart and reach the script as trendline projections,
        # which are exempt from the drawn/spoken binding.
        levels = [line(bar["prior"]["close"], PRIOR),
                  line(bar["session"]["high"], HIGH),
                  line(bar["session"]["low"], LOW),
                  line(close, SWING)]
        # Second anchor is TODAY at the projected price, not the last touch. Drawn to its last
        # touch, the SPX support line stopped on 2026-06-26 while the script said it "sits at
        # 7,383.41 today" and that Monday's low stopped a point short of it -- the central
        # visual claim of the video, and the line did not reach the candle it was about.
        lines = [{"type": "trend_line", "price": t["price"], "time": t["time"],
                  "price2": t["projectedNow"], "time2": session_ts,
                  "overrides": {"linecolor": TL_RESISTANCE if t["kind"] == "resistance"
                                else TL_SUPPORT, "linewidth": 2}}
                 for t in entry["trendlines"]]
        plan.append({
            "out": out, "symbol": symbol, "tf": "1D",
            "purpose": f"{symbol} closed at {close}; session range and the swing structure around it",
            # ONE stage, fully annotated. A staged reveal does not survive the assembler:
            # every beat trims the clip from its start, so a three-stage clip showed the
            # CLEAN chart on most beats -- including the beat that says "the rising line
            # comes in at 193.87" (caught in build/frame-review on 2026-07-28). The level
            # gate passed anyway because it reads the plan, not the pixels. Draw everything
            # up front and any beat, at any length, lands on the annotated chart.
            "stages": [{"holdSec": 70, "draw": levels + lines}],
        })
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("production")
    parser.add_argument("--out", default="chart-plan-daily.json")
    args = parser.parse_args()
    plan = build(args.production)
    path = Path(args.production) / args.out
    path.write_text(json.dumps(plan, indent=1), encoding="utf-8")
    for shot in plan:
        shapes = shot["stages"][0]["draw"]
        levels = [s["price"] for s in shapes if s["type"] == "horizontal_line"]
        print(f"  {shot['out']:10} {shot['symbol']:14} levels={levels} "
              f"trendlines={sum(1 for s in shapes if s['type'] == 'trend_line')}")
    print(f"  -> {path}")


if __name__ == "__main__":
    main()
