#!/usr/bin/env python3
"""Capture a TradingView chart from the OPERATOR'S OWN browser window, via X.

Why this exists: the CDP path (`cdp_chart_shot.mjs` + tradingview-mcp) wedges after the
first symbol switch on this box — `state`/`quote` report the new symbol while the chart
keeps serving the previous series, which produced frames whose search box, legend and
plotted data were three different instruments (2026-07-25, three runs, all quarantined).
And a CDP-drivable Chrome needs its own profile, which has none of the operator's layout —
no SR-Dynamic, no SMC, no zones — so even a correct capture is styled wrong.

The operator's real Chrome has the right layout and login but no debug port, and Chrome 150
refuses to expose the default profile to CDP. So drive it at the X layer instead: type the
symbol into TradingView's own search box, screenshot the real screen, crop the chart pane.

    python tools/visuals/x_chart_shot.py TVC:UKOIL out.png
    ... --settle 12 --region 54,158,2154,1240 --window 0x01e00004

THIS TYPES INTO A LIVE BROWSER. It touches the symbol box and nothing else — never Save,
never Publish. It leaves the chart on the last symbol captured.

NO FRAME IS TRUSTED UNTIL A HUMAN OR MODEL READS IT. The header must show the requested
symbol, the intended timeframe, and OHLC matching the expected bar. Filenames prove nothing.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

# Chart pane inside the operator's 2560x1440 TradingView web layout, measured 2026-07-25:
# left of it is the drawing toolbar, right is the watchlist panel, below is the 1D/5D/1M row.
# The legend row (symbol - timeframe - OHLC) is deliberately INSIDE, because it is the only
# thing that proves which instrument the frame actually shows.
REGION = (54, 158, 2154, 1240)
SYMBOL_BOX = (84, 133)          # the ticker button in the top-left of the TV toolbar
# Park the pointer in empty toolbar space before shooting. Leaving it on the symbol button
# pops a "Symbol search" tooltip that covers the instrument name in the legend — and the
# legend is the only proof of which instrument the frame shows. Same scar as the CDP path:
# never leave the cursor over the chart or a control.
# Below the chart pane (crop ends at y=1398) and clear of the toolbar. Parking INSIDE the
# chart leaves a crosshair, and a crosshair swaps the legend to the HOVERED bar — an OXY shot
# came back reading Oct-2024 values with the current week's price still on the axis.
MOUSE_PARK = (1200, 1432)
SETTLE_S = 10.0


def sh(*args: str, check: bool = True) -> str:
    p = subprocess.run(args, capture_output=True, text=True)
    if check and p.returncode != 0:
        sys.exit(f"{args[0]} failed: {(p.stderr or p.stdout).strip()[:200]}")
    return p.stdout.strip()


def find_window(explicit: str | None) -> str:
    if explicit:
        return explicit
    for wid in sh("xdotool", "search", "--name", "Google Chrome", check=False).splitlines():
        name = sh("xdotool", "getwindowname", wid, check=False)
        if "Chrome" in name:
            return wid
    sys.exit("no Chrome window found on this display")


def set_symbol(win: str, symbol: str, settle: float) -> None:
    sh("xdotool", "windowactivate", "--sync", win)
    time.sleep(1.5)
    x, y = SYMBOL_BOX
    sh("xdotool", "mousemove", "--sync", str(x), str(y), "click", "1")
    time.sleep(2.0)                       # symbol-search dialog opens
    sh("xdotool", "key", "--clearmodifiers", "ctrl+a")
    sh("xdotool", "type", "--clearmodifiers", "--delay", "45", symbol)
    time.sleep(2.5)                       # search is a network call - let results land
    sh("xdotool", "key", "--clearmodifiers", "Return")
    time.sleep(settle)                    # series load + repaint


def shoot(out: Path, region: tuple[int, int, int, int]) -> None:
    sh("xdotool", "mousemove", "--sync", str(MOUSE_PARK[0]), str(MOUSE_PARK[1]))
    time.sleep(1.5)                       # let any hover tooltip fade before the frame
    full = out.with_suffix(".full.png")
    sh("scrot", "-o", str(full))
    x, y, w, h = region
    sh("ffmpeg", "-y", "-loglevel", "error", "-i", str(full),
       "-vf", f"crop={w}:{h}:{x}:{y}", "-frames:v", "1", str(out))
    full.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol", help="e.g. TVC:UKOIL. Pass '-' to shoot without changing symbol.")
    ap.add_argument("out")
    ap.add_argument("--window")
    ap.add_argument("--settle", type=float, default=SETTLE_S)
    ap.add_argument("--region", help="x,y,w,h override")
    a = ap.parse_args()

    region = tuple(int(v) for v in a.region.split(",")) if a.region else REGION
    if len(region) != 4:
        sys.exit("--region needs x,y,w,h")

    win = find_window(a.window)
    if a.symbol != "-":
        set_symbol(win, a.symbol, a.settle)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    shoot(out, region)  # type: ignore[arg-type]
    print(f"shot {out} region={region} symbol={a.symbol}")
    print("VERIFY: read the frame — header symbol, timeframe and OHLC must match the "
          "expected bar, or reject it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
