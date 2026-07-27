# Chart QA — 2026-07-27

Current verdict: **PARTIAL PASS FOR SCRIPTING** — five completed cash/VIX
charts are accepted; Brent and the US 10-year remain excluded.

The fixed TradingView dashboard completed for Brent, S&P 500, Nasdaq Composite,
US 10-year yield, DXY, gold, VIX, XLK, and Nvidia. Raw feed values remain
preserved in `ohlcv-feed-receipts-2026-07-27.json`.

## Accepted

Each accepted `1D` frame was read directly after capture. Instrument identity,
newest referenced candle, price axis, settled OHLC header, and drawn levels are
visible together. No Replay watermark, crosshair, dialog, or obstructing menu is
present. Each MP4 hash matches `chart-capture-receipts.json`.

| Chart | Header OHLC | Pixel check |
|---|---|---|
| `03-spx` | O 7,464.20 / H 7,480.57 / L 7,382.74 / C 7,413.18 | S&P 500 identity, 1D, newest candle, full axis, prior/low tags visible |
| `04-nasdaq` | O 25,236.19 / H 25,261.91 / L 24,774.87 / C 24,932.08 | Nasdaq Composite identity, 1D, newest candle, full axis, prior/low tags visible |
| `05-xlk` | O 177.83 / H 178.30 / L 171.73 / C 174.30 | XLK identity, 1D, newest regular-session candle, full axis, prior/low tags visible |
| `06-nvda` | O 208.20 / H 208.75 / L 195.44 / C 196.51 | Nvidia identity, 1D, newest regular-session candle, full axis, prior/low tags visible |
| `07-vix` | O 17.62 / H 19.93 / L 17.53 / C 18.67 | VIX identity, 1D, newest candle, full axis, prior/high tags visible |

These five captures were completed before `vo.txt` existed, satisfying the
charts-before-script timestamp order.

## Rejected

- `ta-work/01-brent-s0.png` — readable Brent identity, `1D` timeframe, and full
  price axis were present, but the frame displayed a live countdown and header
  close `85.41`; the saved feed close was `85.34`. SHA-256:
  `857127ae3492d2e57a2a58315c736e940dab28327cd11cb82b7b77f0ec13d316`.

The frame is not completed-session evidence and remains barred from the analysis
brief, script, claims ledger, and scene plan.

## Uncaptured

- `02-us10y` — no accepted pixels.

Its feed row is retained as historical dashboard evidence but cannot supply a
narrated chart claim.

## First-attempt blocker preserved

TradingView CDP became unavailable after the controlled restart. The installed
MSIX could not be relaunched from that session: packaged-app activation failed
with `0x80070520`, the Windows-control native host was unavailable, and the
documented local-copy fallback exited with `0xFFFF7003`.

Later recovery produced the five accepted cash/VIX captures above. It did not
repair or replace the rejected Brent frame.
