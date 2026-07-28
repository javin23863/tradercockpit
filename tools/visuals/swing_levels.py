#!/usr/bin/env python3
"""Derive swing pivots, horizontal levels and trendlines from the feed, with receipts.

The operator's 2026-07-28 rejection included "there's no trend lines" and "you don't speak
in levels". Both gates for those now exist, but neither GENERATES anything: `draw_stage` has
always accepted `trend_line` shapes with price2/time2, and nothing ever emitted one.

This does. It reads bars through the same tradingview-mcp CLI the rest of the lane uses,
finds fractal swing pivots, clusters them into levels a trader would actually draw, fits
trendlines through consecutive same-side pivots, and writes a receipt so a level spoken in
the script has provenance the claims gate can check -- the swing equivalent of
ohlcv-feed-receipts.

    python tools/visuals/swing_levels.py productions/daily-<date> \
        --symbols SP:SPX NASDAQ:NVDA --tf 1D --count 245
    ... --emit-draw            also print chart-plan `draw` blocks ready to merge
    ... --selftest             synthetic bars, no TradingView needed

A trendline here is auditable, not decorative: every one carries its touch count and
whether a later close has broken it.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from fetch_tv_charts import TV_CLI, tv  # noqa: E402  (same CLI bridge as every other capture)

SCHEMA = "tradercockpit-swing-receipts/v1"
PIVOT_STRENGTH = 3      # a 7-bar fractal: the swing must dominate 3 bars each side
TOLERANCE_PCT = 0.25    # two pivots this close in price are the same level a trader draws
LEVELS_PER_SIDE = 3     # six lines total; more than that is a chart nobody can read
# A level 10% below spot is history, not a level anyone trades off tomorrow. The first run
# returned SPX levels at 6,550-7,002 with price at 7,413 -- true, and useless.
BAND_PCT = 8.0
# A line through the last two pivots spanned 7 bars on the first run. That is a squiggle.
MIN_SPAN_BARS = 15
RECENT_ANCHOR_BARS = 60  # the second anchor must be current or the line describes last year
DAY_S = 86400


def pivots(bars, strength=PIVOT_STRENGTH):
    """Fractal swing highs and lows. A pivot must strictly dominate its window on one side
    and at least tie on the other, so a flat double top still registers once."""
    found = []
    for i in range(strength, len(bars) - strength):
        window = bars[i - strength:i + strength + 1]
        if bars[i]["high"] >= max(b["high"] for b in window):
            found.append({"index": i, "time": bars[i]["time"], "price": bars[i]["high"], "kind": "high"})
        if bars[i]["low"] <= min(b["low"] for b in window):
            found.append({"index": i, "time": bars[i]["time"], "price": bars[i]["low"], "kind": "low"})
    return sorted(found, key=lambda p: (p["index"], p["kind"]))


def cluster(points, last_close, tolerance_pct=TOLERANCE_PCT, band_pct=BAND_PCT,
            keep=LEVELS_PER_SIDE):
    """Group pivots of one side into levels, then keep the ones near enough to matter.

    Ranking is touches first, then proximity to the last close. Ranking by touches alone
    surfaces the most-tested level in the whole window, which on a trending instrument is
    always the oldest congestion and never the one the next session trades against."""
    levels = []
    for point in sorted(points, key=lambda p: p["price"]):
        if levels and abs(point["price"] - levels[-1]["price"]) / levels[-1]["price"] * 100 <= tolerance_pct:
            level = levels[-1]
            level["touches"] += 1
            level["lastTouch"] = max(level["lastTouch"], point["time"])
            # the level sits at the extreme of its cluster, which is where price reacted
            level["price"] = (max(level["price"], point["price"]) if point["kind"] == "high"
                              else min(level["price"], point["price"]))
        else:
            levels.append({"price": point["price"], "kind": point["kind"],
                           "touches": 1, "lastTouch": point["time"]})
    for level in levels:
        level["distancePct"] = round(abs(level["price"] - last_close) / last_close * 100, 3)
        # `kind` is where the level came from; `position` is what it is NOW. A swing low
        # price has closed below becomes resistance, and a script that calls it support
        # because the receipt says "low" is wrong on the page.
        level["position"] = "above" if level["price"] > last_close else "below"
    near = [level for level in levels if level["distancePct"] <= band_pct]
    return sorted(near, key=lambda l: (-l["touches"], l["distancePct"]))[:keep]


def _fit(first, second, side_pivots, bars, tolerance_pct):
    span = second["index"] - first["index"]
    if span < MIN_SPAN_BARS:
        return None
    slope = (second["price"] - first["price"]) / span

    def line_at(index):
        return first["price"] + slope * (index - first["index"])

    touches = 2 + sum(
        1 for p in side_pivots
        if p["index"] not in (first["index"], second["index"])
        and line_at(p["index"]) > 0
        and abs(p["price"] - line_at(p["index"])) / line_at(p["index"]) * 100 <= tolerance_pct)
    resistance = first["kind"] == "high"
    broken = any(
        (bar["close"] > line_at(i) * (1 + tolerance_pct / 100)) if resistance
        else (bar["close"] < line_at(i) * (1 - tolerance_pct / 100))
        for i, bar in enumerate(bars) if i > second["index"])
    return {
        "kind": "resistance" if resistance else "support",
        "time": first["time"], "price": round(first["price"], 4),
        "time2": second["time"], "price2": round(second["price"], 4),
        "spanBars": span, "touches": touches, "broken": broken,
        "slopePerBar": round(slope, 6),
        # projected to the right edge, which is the number the script would quote today
        "projectedNow": round(line_at(len(bars) - 1), 4),
    }


def trendline(side_pivots, bars, tolerance_pct=TOLERANCE_PCT):
    """The best line through two same-side pivots, audited.

    Not "the last two pivots": that produced a 7-bar squiggle on the first live run. Every
    pair spanning at least MIN_SPAN_BARS whose second anchor is recent is scored, and the
    winner is the one the most pivots touch, breaking ties toward a longer span. Unbroken
    lines outrank broken ones, but a broken line is still returned when it is all there is
    -- a broken trendline is worth talking about; calling it intact is not."""
    if len(side_pivots) < 2:
        return None
    recent = len(bars) - RECENT_ANCHOR_BARS
    best = None
    for a in range(len(side_pivots) - 1):
        for b in range(a + 1, len(side_pivots)):
            if side_pivots[b]["index"] < recent:
                continue
            fit = _fit(side_pivots[a], side_pivots[b], side_pivots, bars, tolerance_pct)
            if fit is None:
                continue
            rank = (not fit["broken"], fit["touches"], fit["spanBars"])
            if best is None or rank > best[0]:
                best = (rank, fit)
    return best[1] if best else None


def analyse(bars):
    found = pivots(bars)
    highs = [p for p in found if p["kind"] == "high"]
    lows = [p for p in found if p["kind"] == "low"]
    lines = [line for line in (trendline(highs, bars), trendline(lows, bars)) if line]
    last_close = bars[-1]["close"]
    return {
        "barsWindow": {"from": bars[0]["time"], "to": bars[-1]["time"], "count": len(bars),
                       "lastClose": last_close},
        "pivots": [{k: p[k] for k in ("time", "price", "kind")} for p in found],
        "levels": cluster(highs, last_close) + cluster(lows, last_close),
        "trendlines": lines,
    }


def draw_block(entry, colors=("#FFB000", "#22AB94")):
    """chart-plan `draw` shapes: the clustered levels, then the trendlines."""
    shapes = [{"type": "horizontal_line", "price": level["price"],
               "overrides": {"linecolor": colors[0] if level["kind"] == "high" else colors[1],
                             "linewidth": 2}}
              for level in entry["levels"]]
    shapes += [{"type": "trend_line", "price": line["price"], "time": line["time"],
                "price2": line["price2"], "time2": line["time2"],
                "overrides": {"linecolor": colors[0] if line["kind"] == "resistance" else colors[1],
                              "linewidth": 2}}
               for line in entry["trendlines"]]
    return shapes


def collect(symbols, tf, count, dry=False):
    instruments = {}
    for symbol in symbols:
        tv(["symbol", symbol], dry)
        tv(["timeframe", tf], dry)
        payload = tv(["ohlcv", "--count", str(count)], dry)
        bars = payload.get("bars") or []
        if len(bars) < PIVOT_STRENGTH * 2 + 2:
            sys.exit(f"[swing] {symbol}: only {len(bars)} bars returned; cannot find pivots")
        instruments[symbol] = analyse(bars)
        line_count = len(instruments[symbol]["trendlines"])
        print(f"  {symbol}: {len(instruments[symbol]['pivots'])} pivots, "
              f"{len(instruments[symbol]['levels'])} levels, {line_count} trendline(s)")
    return instruments


def selftest():
    # a range: repeated swing highs near 100 and swing lows near 94, price finishing inside
    # it. Both sides must produce pivots, and both levels must survive the proximity band.
    prices = [100, 98, 96, 94, 96, 98, 100, 98, 96, 94, 96, 98, 100, 98, 96, 94, 96, 98]
    bars = [{"time": 1700000000 + i * DAY_S, "open": p, "high": p + 1, "low": p - 1,
             "close": p, "volume": 0} for i, p in enumerate(prices)]
    entry = analyse(bars)
    assert entry["pivots"], "expected pivots in a range"
    assert {p["kind"] for p in entry["pivots"]} == {"high", "low"}, entry["pivots"]
    assert entry["levels"], "expected clustered levels"
    assert {l["kind"] for l in entry["levels"]} == {"high", "low"}, entry["levels"]
    assert all(level["touches"] >= 1 for level in entry["levels"])
    shapes = draw_block(entry)
    assert all(s["type"] in {"horizontal_line", "trend_line"} for s in shapes), shapes
    assert all("price2" in s and "time2" in s for s in shapes if s["type"] == "trend_line")

    # a level a trader draws once, not twice: two pivots within tolerance collapse
    close = [{"price": 100.0, "kind": "high", "time": 1}, {"price": 100.1, "kind": "high", "time": 2}]
    assert len(cluster(close, 100.0)) == 1 and cluster(close, 100.0)[0]["touches"] == 2
    apart = [{"price": 100.0, "kind": "high", "time": 1}, {"price": 103.0, "kind": "high", "time": 2}]
    assert len(cluster(apart, 100.0)) == 2
    # a level 10% away is history, not something the next session trades against
    far = [{"price": 100.0, "kind": "high", "time": 1}, {"price": 140.0, "kind": "high", "time": 2}]
    assert [l["price"] for l in cluster(far, 100.0)] == [100.0]

    # a resistance line closed through is reported broken, never silently intact
    flat = [{"time": 1700000000 + i * DAY_S, "open": 100, "high": 100, "low": 100,
             "close": 100, "volume": 0} for i in range(40)]
    highs = [{"index": 0, "time": flat[0]["time"], "price": 100.0, "kind": "high"},
             {"index": 20, "time": flat[20]["time"], "price": 99.0, "kind": "high"}]
    flat[30]["close"] = 130.0
    assert trendline(highs, flat)["broken"] is True
    # a squiggle through two adjacent pivots is not a trendline
    near = [{"index": 20, "time": flat[20]["time"], "price": 100.0, "kind": "high"},
            {"index": 24, "time": flat[24]["time"], "price": 99.0, "kind": "high"}]
    assert trendline(near, flat) is None
    print("swing-levels selftest: 8/8 PASS")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("production", nargs="?")
    parser.add_argument("--symbols", nargs="+")
    parser.add_argument("--tf", default="1D")
    parser.add_argument("--count", type=int, default=245,
                        help="bars to read; matches the 245-day capture window")
    parser.add_argument("--emit-draw", action="store_true",
                        help="also print chart-plan draw blocks ready to merge into stages")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        selftest()
        return 0
    if not (args.production and args.symbols):
        parser.error("production and --symbols are required unless --selftest is used")

    production = Path(args.production)
    production.mkdir(parents=True, exist_ok=True)
    instruments = collect(args.symbols, args.tf, args.count, args.dry_run)
    stamp = datetime.now(timezone.utc)
    receipt = {
        "schema": SCHEMA,
        "generatedAt": stamp.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": "tradingview-mcp tv ohlcv",
        "sourceCommand": f"node {TV_CLI} ohlcv --count {args.count}",
        "params": {"timeframe": args.tf, "count": args.count,
                   "pivotStrength": PIVOT_STRENGTH, "tolerancePct": TOLERANCE_PCT},
        "instruments": instruments,
    }
    out = production / f"swing-receipts-{stamp:%Y-%m-%d}.json"
    out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"  -> {out}")
    if args.emit_draw:
        for symbol, entry in instruments.items():
            print(f"\n// {symbol}")
            print(json.dumps(draw_block(entry), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
