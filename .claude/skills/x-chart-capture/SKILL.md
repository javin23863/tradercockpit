---
name: x-chart-capture
description: "Capture TradingView charts from the operator's own logged-in browser window using X automation (xdotool + scrot + ffmpeg) instead of CDP. Use when CDP symbol switching wedges, when the machine has no working GL driver, or whenever the capture must carry the operator's real layout and indicators."
---

# X-layer chart capture

`tools/visuals/x_chart_shot.py`. Use this **instead of** `cdp_chart_shot.mjs` /
`tv_ta_capture.py` when either is true:

- CDP symbol switching wedges — `state`/`quote` report the new symbol while the chart keeps
  serving the previous series.
- The capture must carry the operator's saved layout (SR-Dynamic, SMC, premium/discount zones).
  A CDP-drivable Chrome needs its own `--user-data-dir`, which has none of it.

```
python tools/visuals/x_chart_shot.py TVC:UKOIL out.png --settle 14
python tools/visuals/x_chart_shot.py - out.png          # shoot without changing symbol
```

## Why it exists (Lenox, 2026-07-25/26)

Three CDP runs produced 84 unusable frames. One had the search box on `SPX`, the legend on
`TVC:UKOIL` and Occidental's OHLC — three instruments in one frame. Root causes: no working GL
driver (`MESA-LOADER: failed to open swrast`) so the chart canvas never repainted, and Chrome
150 refuses to expose the default profile to CDP, so the only drivable browser was a fresh
profile with the wrong layout. X automation sidesteps both — it drives the window the operator
is already looking at.

## Contract

- **Reads the operator's live browser.** Touches the symbol box and nothing else. Never Save,
  never Publish. Leaves the chart on the last symbol captured.
- **Park the pointer before every frame** (`MOUSE_PARK`). Leaving it on the symbol button pops a
  "Symbol search" tooltip that covers the instrument name in the legend — and the legend is the
  only proof of which instrument the frame shows. Same scar as the CDP crosshair.
- **The legend must stay inside the crop.** `REGION` is measured so the legend row and the time
  axis are in frame, and the drawing toolbar and watchlist are out.
- **Pure charts.** Level lines need the CDP `draw` command; this path does not draw. That is in
  format — the weekend-review precedent is "pure charts + brand q-cards" and the operator layout
  carries its own zones.

## Mandatory frame check

**No frame is accepted until it is read back.** Filenames prove nothing — that is exactly how
three runs shipped wrong-instrument captures. Every frame must show:

1. the legend naming the requested instrument
2. the intended timeframe (`· 1W ·`)
3. OHLC matching the expected bar from the chart-read receipt
4. no TradingView signup modal (means the session is logged out — stop and log in)

Mismatch ⇒ reject the frame and re-shoot. Do not assemble unverified frames.

## Geometry

`REGION = (54, 158, 2154, 1240)` and `SYMBOL_BOX = (84, 133)` are measured for a 2560×1440
display with the TradingView web layout. Both are CLI-overridable. Different resolution or a
changed TradingView UI ⇒ re-measure by screenshotting and reading the image, then pass
`--region`.

## Assembly

Do **not** reuse `still()` from `tv_ta_capture.py` on these PNGs — its filter crops 40px off the
top for the CDP toolbar strip and would clip the legend. Scale to height 1080 and pad to 1920:

```
ffmpeg -y -loop 1 -i shot.png -t 10 \
  -vf "scale=-2:1080,pad=1920:1080:(ow-iw)/2:0:black,format=yuv420p" -r 30 \
  <encoder_args from tools/encoder.py> out.mp4
```
