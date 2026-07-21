#!/usr/bin/env python3
"""Capture annotated TradingView TA sequences for format v2 (StockedUp model).

Drives the live TradingView Desktop app (CDP :9222 via tradingview-mcp `tv` CLI):
per shot set symbol/timeframe, then step through STAGES — each stage optionally
draws shapes (levels/zones/trendlines from the day's claims), screenshots the
chart (full price axis, user's own indicators visible), and the stage PNGs are
assembled into one clip: Ken-Burns zoom per stage, hard cut between stages, so
annotations "appear" as the VO discusses them.

Plan JSON (array of shots):
  [{"out": "05a-oil-ta", "symbol": "TVC:UKOIL", "tf": "1D",
    "stages": [
      {"holdSec": 8},
      {"holdSec": 8, "draw": [{"type": "horizontal_line", "price": 90.96,
                               "overrides": {"linecolor": "#FF3D5E", "linewidth": 2}}]},
      {"holdSec": 8, "draw": [{"type": "rectangle", "price": 108, "time": 1749772800,
                               "price2": 112, "time2": 1752451200}]}
    ]}]

Usage:
  python tools/visuals/tv_ta_capture.py productions/video-02-hormuz tools/visuals/ta-hormuz.json
  ... --dry-run   (validate plan + tv CLI reachable, no capture)

Our drawings are removed after each shot (ids tracked); the user's own drawings
and indicators are never touched.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
HUB = HERE.parents[1]
CDP_SHOT = HERE / "cdp_chart_shot.mjs"
SETTLE_SYMBOL_S = 5   # data load after symbol/timeframe switch
SETTLE_DRAW_S = 1.5

# TV desktop injects Google safeframe broker ads over the chart (v3 defect: "Trading
# Analytics" card burned into captures). Hide them before every shot — they reload.
AD_HIDE_JS = ("(()=>{let n=0;for(const f of document.querySelectorAll("
              "'iframe[src*=\"safeframe\"],iframe[src*=\"googlesyn\"],iframe[src*=\"doubleclick\"]'"
              ")){let node=f;for(let i=0;i<6&&node.parentElement;i++){const cs=getComputedStyle("
              "node.parentElement);if(cs.position==='fixed'||cs.position==='absolute'){node="
              "node.parentElement}else break}node.style.display='none';n++}return n})()")

# Operator ruling 2026-07-17: chart background must be white to match white news pages.
# Overrides reset on symbol change, so reapply per shot after the symbol settles.
WHITE_JS = ("(()=>{try{const w=TradingViewApi._chartWidgetCollection.activeChartWidget.value();"
            "w.applyOverrides({'paneProperties.background':'#FFFFFF',"
            "'paneProperties.backgroundType':'solid',"
            "'paneProperties.vertGridProperties.color':'#E8E8E8',"
            "'paneProperties.horzGridProperties.color':'#E8E8E8',"
            "'scalesProperties.textColor':'#131722'});return 'white'}"
            "catch(e){return 'ERR '+e.message}})()")

sys.path.insert(0, str(HERE))
from fetch_tv_charts import TV_CLI, record_chart_capture, tv  # noqa: E402  (same CLI bridge + receipt writer)


def still(png: Path, out: Path, dur: float, dry: bool) -> None:
    """Static hold, NO zoom — zoompan pushed the price axis out of frame (v2 defect).
    Wider than 16:9 (maximized app, ~2.0): full-height RIGHT-anchored crop keeps the
    price axis, trims oldest candles. Narrower (unmaximized relaunch, seen 1304x1187):
    fit-pad instead — scaling a narrow crop straight to 1920x1080 squashes candles."""
    vf = ("crop=iw:ih-40:0:40,"                               # drop the dark app toolbar strip (visible on white theme)
          "scale=-2:1080,"                                    # height always 1080
          "crop='min(iw,1920)':1080:'max(iw-1920,0)':0,"      # wide -> right-crop (keep axis)
          "pad=1920:1080:(ow-iw)/2:0:white,format=yuv420p")   # narrow -> side pads; white world
    if dry:
        print(f"  [dry] ffmpeg still {png.name} -> {out.name} ({dur:.0f}s)")
        return
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(png), "-t", f"{dur:.2f}",
                    "-vf", vf, "-r", "30", "-c:v", "h264_nvenc", "-cq", "19",
                    "-preset", "p5", str(out)], check=True, capture_output=True)


def draw_stage(shapes: list[dict], dry: bool) -> list[str]:
    """Draw shapes, return the ids we created (for cleanup)."""
    ids = []
    for s in shapes:
        args = ["draw", "shape", "--type", s["type"]]
        # TV's createShape requires a time even for horizontal_line — default to now
        if s.get("time") is None:
            s = {**s, "time": int(time.time())}
        for k, flag in (("price", "--price"), ("time", "--time"),
                        ("price2", "--price2"), ("time2", "--time2"), ("text", "--text")):
            if s.get(k) is not None:
                args += [flag, str(s[k])]
        if s.get("overrides"):
            args += ["--overrides", json.dumps(s["overrides"])]
        res = tv(args, dry)
        sid = res.get("id") or res.get("shape_id") or res.get("entity_id")
        if sid:
            ids.append(str(sid))
        elif not dry:
            print(f"  [warn] no id returned for {s['type']} — cannot auto-remove later")
    return ids


def remove_drawings(ids: list[str], dry: bool) -> None:
    for sid in ids:
        try:
            tv(["draw", "remove", "--id", sid], dry)
        except SystemExit:
            print(f"  [warn] failed to remove drawing {sid} — remove manually")


def concat_clips(clips: list[Path], out: Path) -> None:
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(out)], check=True, capture_output=True)
    lst.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prod")
    ap.add_argument("plan")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="capture only the shot with this out name")
    ap.add_argument("--expect-last-bar", metavar="YYYY-MM-DD",
                    help="abort a shot if the feed's last bar is not this session "
                         "(bar open-date may stamp the prior calendar day; both accepted). "
                         "Catches replay landing on the wrong date per symbol (2026-07-20 incident).")
    ap.add_argument("--range-days", type=int, default=0, metavar="N",
                    help="zoom every shot to the last N calendar days (+4d right pad) before "
                         "shooting, and pin the price scale to the visible bars' hi/lo. Mobile "
                         "legibility ruling 2026-07-21: a full-history chart is unreadable on a "
                         "phone. Requires --expect-last-bar for the anchor date. ~100 recommended.")
    a = ap.parse_args()

    prod = (HUB / a.prod) if not Path(a.prod).is_absolute() else Path(a.prod)
    visuals = prod / "visuals"
    visuals.mkdir(parents=True, exist_ok=True)
    work = prod / "ta-work"
    work.mkdir(exist_ok=True)

    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    for i, shot in enumerate(plan):
        for key in ("out", "symbol", "tf", "stages"):
            if key not in shot:
                sys.exit(f"plan[{i}] missing '{key}'")

    tv(["status"], a.dry_run)

    for shot in plan:
        if a.only and shot["out"] != a.only:
            continue
        out_mp4 = visuals / f"{shot['out']}.mp4"
        if out_mp4.exists():
            print(f"[{shot['out']}] exists, skip")
            continue
        print(f"[{shot['out']}] {shot['symbol']} {shot['tf']} — {len(shot['stages'])} stages")
        tv(["symbol", shot["symbol"]], a.dry_run)
        tv(["timeframe", shot["tf"]], a.dry_run)
        if not a.dry_run:
            time.sleep(SETTLE_SYMBOL_S)
        if a.expect_last_bar and not a.dry_run:
            from datetime import date, timedelta
            expected = date.fromisoformat(a.expect_last_bar)
            raw = subprocess.run(
                ["node", str(TV_CLI), "ohlcv", "--count", "1"],
                check=True, capture_output=True, text=True).stdout
            bars = json.loads(raw)
            bar = (bars.get("bars") or [bars])[-1] if isinstance(bars, dict) else bars[-1]
            bar_date = datetime.fromtimestamp(bar["time"], tz=timezone.utc).date()
            # session-open stamping: a Monday session can stamp Sunday (futures/CFD feeds)
            if bar_date not in (expected, expected - timedelta(days=1)):
                sys.exit(f"[{shot['out']}] last bar is {bar_date}, expected session "
                         f"{expected} — wrong bar on screen (replay pinned? stale feed?). "
                         "Nothing captured for this shot.")
        if a.range_days and not a.dry_run:
            if not a.expect_last_bar:
                sys.exit("--range-days needs --expect-last-bar as the anchor date")
            from datetime import date, timedelta
            anchor = date.fromisoformat(a.expect_last_bar)
            frm = int(datetime(anchor.year, anchor.month, anchor.day, tzinfo=timezone.utc).timestamp()) \
                - a.range_days * 86400
            to = int(datetime(anchor.year, anchor.month, anchor.day, tzinfo=timezone.utc).timestamp()) \
                + 4 * 86400
            tv(["range", "--from", str(frm), "--to", str(to)], a.dry_run)
            time.sleep(1.5)
            # ponytail: price-scale pinning was tried and REVERTED — setPriceRangeInPrice takes
            # internal units, not prices, and blanked the pane (2026-07-21). The range zoom is
            # the win; indicator zones below price squashing candles somewhat is accepted.
        tv(["ui", "eval", "--js", AD_HIDE_JS], a.dry_run)
        tv(["ui", "eval", "--js", WHITE_JS], a.dry_run)
        # Mobile ruling 2026-07-21: axis text must read on a phone.
        tv(["ui", "eval", "--js",
            "(()=>{try{TradingViewApi._chartWidgetCollection.activeChartWidget.value()"
            ".applyOverrides({'scalesProperties.fontSize':17});return 'font'}"
            "catch(e){return 'ERR '+e.message}})()"], a.dry_run)
        if not a.dry_run:
            time.sleep(1)

        drawn: list[str] = []
        clips: list[Path] = []
        captured_at = None
        try:
            for si, stage in enumerate(shot["stages"]):
                if stage.get("draw"):
                    drawn += draw_stage(stage["draw"], a.dry_run)
                    if not a.dry_run:
                        time.sleep(SETTLE_DRAW_S)
                name = f"{shot['out']}-s{si}"
                if a.dry_run:
                    print(f"  [dry] cdp chart shot {name}.png")
                    continue
                png = work / f"{name}.png"
                subprocess.run(
                    ["node", str(CDP_SHOT), str(png), "2560", "1440", "--dsf", "2"],
                    check=True,
                )
                captured_at = datetime.now(timezone.utc)
                clip = work / f"{name}.mp4"
                still(png, clip, float(stage.get("holdSec", 8)), a.dry_run)
                clips.append(clip)
        finally:
            remove_drawings(drawn, a.dry_run)

        if not a.dry_run:
            concat_clips(clips, out_mp4)
            # Receipt the scene-plan artifact, not CDP's disposable per-stage PNGs.
            record_chart_capture(prod, out_mp4, captured_at)
            print(f"  -> {out_mp4}")

    print("\nDRY RUN OK" if a.dry_run else "\nDONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
