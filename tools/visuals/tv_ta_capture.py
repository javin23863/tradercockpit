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
CDP_SHOT_TIMEOUT_S = 45
SETTLE_SYMBOL_S = 5   # data load after symbol/timeframe switch
SETTLE_DRAW_S = 1.5

# TV desktop injects Google safeframe broker ads over the chart (v3 defect: "Trading
# Analytics" card burned into captures). Hide them before every shot — they reload.
AD_HIDE_JS = ("(()=>{let n=0;for(const f of document.querySelectorAll("
              "'iframe[src*=\"safeframe\"],iframe[src*=\"googlesyn\"],iframe[src*=\"doubleclick\"]'"
              ")){let node=f;for(let i=0;i<6&&node.parentElement;i++){const cs=getComputedStyle("
              "node.parentElement);if(cs.position==='fixed'||cs.position==='absolute'){node="
              "node.parentElement}else break}node.style.display='none';n++}return n})()")

# Operator ruling 2026-07-28: capture the operator's OWN chart — his dark theme and his
# two daily indicators, untouched. The 2026-07-17 white-background override is deleted;
# forcing a theme also fought the layout the indicators were tuned on.

# The drawn identity card is GONE (operator ruling 2026-07-28). It existed only because
# still()'s right-anchored crop sliced TradingView's own symbol off the far left, which
# is exactly what the operator complained about: "no one can see the ticker symbol, so
# you have to create your own in the top right-hand corner". still() now fit-scales the
# whole pane, so the NATIVE legend -- 'S&P 500 Index . 1D . SP' plus OHLC -- is in frame
# and no substitute label is drawn. A generated label must never stand in for the real
# one; same principle as the AP masthead fix earlier the same day.

sys.path.insert(0, str(HERE))
from fetch_tv_charts import TV_CLI, record_chart_capture, tv  # noqa: E402  (same CLI bridge + receipt writer)


# Now ZERO, and it must stay zero: cdp_chart_shot.mjs clips from the pane canvas itself, so
# no app chrome reaches the PNG and there is nothing left to crop. Cropping here as well
# would eat the symbol legend -- the identity the whole 07-28 chart fix exists to preserve.
# The old value (64, measured at one window size) was scale-dependent and silently stopped
# covering the toolbar the moment the app relaunched at 1707x874: Replay / Save / Trade were
# burned into every chart of the first re-shoot.
APP_CHROME_PX = 0


# Pane fill: the vertical share of the plot area the candles actually span. TradingView
# autoscales to the visible data, so candles fill the pane UNLESS something else is driving
# the price scale -- which is exactly the 2026-07-27 squash, where price sat in the top fifth
# and the axis ran 5,800-7,800 for an index at 7,413.
# Floor MEASURED, never invented: the five clean 245-day captures score 0.959-0.989; the
# squashed 100-day captures of 2026-07-23 score 0.702-0.880. 0.90 separates them cleanly and
# still passes the two 07-23 charts that were genuinely fine (0.963, 0.967).
CANDLE_RGB = ((242, 54, 69), (8, 153, 129))   # solid body colours of the operator's dark theme
CANDLE_TOL = 26
HEADER_PX, AXIS_PX, SCALE_PX = 100, 80, 95    # OHLC legend, date axis, right price gutter
PANE_FILL_FLOOR = 0.90


def pane_fill(png: Path) -> float:
    """Share of the plot area spanned by candle-coloured pixels, 0.0 when none are found."""
    from PIL import Image

    image = Image.open(png).convert("RGB")
    width, height = image.size
    pixels = image.load()
    top, bottom = HEADER_PX, height - AXIS_PX
    rows = []
    for y in range(top, bottom):
        for x in range(0, width - SCALE_PX, 2):
            r, g, b = pixels[x, y]
            if any(abs(r - cr) < CANDLE_TOL and abs(g - cg) < CANDLE_TOL and abs(b - cb) < CANDLE_TOL
                   for cr, cg, cb in CANDLE_RGB):
                rows.append(y)
                break
    return (max(rows) - min(rows) + 1) / (bottom - top) if rows else 0.0


def still(png: Path, out: Path, dur: float, dry: bool) -> None:
    """Static hold, NO zoom — zoompan pushed the price axis out of frame (v2 defect).
    Fit-pad at any pane aspect: the whole chart is letterboxed into 1920x1080 so nothing
    is ever cropped away."""
    # Fit the WHOLE pane, never crop it. The old right-anchored crop kept the price axis
    # but sliced the symbol off the far left, which is why a substitute identity card had
    # to be drawn — the operator's 2026-07-28 complaint ("no one can see the ticker symbol,
    # so you have to create your own"). Letterboxing costs some height and keeps the
    # symbol, the OHLC legend, the price axis and the date axis all in frame, which is
    # what his reference screenshot shows.
    vf = (f"crop=iw:ih-{APP_CHROME_PX}:0:{APP_CHROME_PX},"    # drop the dark app toolbar strip
          "scale=1920:1080:force_original_aspect_ratio=decrease,"
          "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,format=yuv420p")
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
    ap.add_argument("prod", nargs="?")
    ap.add_argument("plan", nargs="?")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="capture only the shot with this out name")
    ap.add_argument("--reuse-png", action="store_true",
                    help="re-render mp4s from cached stage PNGs (no TradingView, no re-shoot)")
    ap.add_argument("--pane-fill-floor", type=float, default=PANE_FILL_FLOOR,
                    help=f"minimum share of the plot area the candles must span "
                         f"(default {PANE_FILL_FLOOR}, measured from clean captures)")
    ap.add_argument("--measure-fill", metavar="PNG",
                    help="print the pane fill of one PNG and exit; use to re-derive the floor")
    ap.add_argument("--expect-last-bar", metavar="YYYY-MM-DD",
                    help="abort a shot if the feed's last bar is not this session "
                         "(bar open-date may stamp the prior calendar day; both accepted). "
                         "Catches replay landing on the wrong date per symbol (2026-07-20 incident).")
    ap.add_argument("--range-days", type=int, default=245, metavar="N",
                    help="zoom every shot to the last N calendar days (+4d right pad) before "
                         "shooting, and pin the price scale to the visible bars' hi/lo. Mobile "
                         "legibility ruling 2026-07-21: a full-history chart is unreadable on a "
                         "phone. Requires --expect-last-bar for the anchor date. ~100 recommended.")
    a = ap.parse_args()

    if a.measure_fill:
        print(f"{a.measure_fill}: pane fill {pane_fill(Path(a.measure_fill)):.3f} "
              f"(floor {a.pane_fill_floor:.2f})")
        return 0
    if not (a.prod and a.plan):
        ap.error("prod and plan are required unless --measure-fill is used")

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

    # --reuse-png renders from cached PNGs only; TradingView never has to be up
    tv(["status"], a.dry_run or a.reuse_png)

    receipt_path = prod / "chart-capture-receipts.json"
    existing_captures = (json.loads(receipt_path.read_text(encoding="utf-8")).get("captures", [])
                         if receipt_path.exists() else [])

    for shot in plan:
        if a.only and shot["out"] != a.only:
            continue
        out_mp4 = visuals / f"{shot['out']}.mp4"
        if out_mp4.exists():
            print(f"[{shot['out']}] exists, skip")
            continue
        # --reuse-png: re-render the mp4 from the cached stage PNGs. No TradingView, no
        # re-shoot, so a fixed video filter (e.g. the APP_CHROME_PX correction) can be
        # applied to an already-captured session deterministically.
        stage_pngs = [work / f"{shot['out']}-s{si}.png" for si in range(len(shot["stages"]))]
        if a.reuse_png and all(p.is_file() for p in stage_pngs):
            print(f"[{shot['out']}] reuse cached PNGs")
            clips = []
            for si, (stage, png) in enumerate(zip(shot["stages"], stage_pngs)):
                clip = work / f"{shot['out']}-s{si}.mp4"
                still(png, clip, float(stage.get("holdSec", 8)), a.dry_run)
                clips.append(clip)
            if not a.dry_run:
                concat_clips(clips, out_mp4)
                # Re-receipt with the ORIGINAL capture time: re-rendering changes the
                # artifact hash but not when the pixels came off the chart. Forging a
                # fresh capturedAt here would claim a capture that did not happen.
                rel = out_mp4.relative_to(prod).as_posix()
                prior = next((c for c in existing_captures if c.get("path") == rel), None)
                captured_at = (datetime.fromisoformat(prior["capturedAt"].replace("Z", "+00:00"))
                               if prior else
                               datetime.fromtimestamp(stage_pngs[0].stat().st_mtime, tz=timezone.utc))
                record_chart_capture(prod, out_mp4, captured_at)
                print(f"  -> {out_mp4} (re-receipted, capturedAt {captured_at.isoformat()})")
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
                    timeout=CDP_SHOT_TIMEOUT_S,
                )
                captured_at = datetime.now(timezone.utc)
                # Fail HERE, not in visual_qa: a squashed chart caught after the render is a
                # tombstone 90 minutes later, and the operator sees it before the gate does.
                fill = pane_fill(png)
                if fill < a.pane_fill_floor:
                    raise SystemExit(
                        f"[tv-ta] {name}: candles span {fill:.3f} of the plot area, floor "
                        f"{a.pane_fill_floor:.2f}. Something other than price is driving the "
                        f"scale -- check the price scale is set to 'Scale price chart only' "
                        f"before re-shooting. PNG kept at {png}"
                    )
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
