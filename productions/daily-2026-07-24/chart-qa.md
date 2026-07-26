# Chart QA — 2026-07-24

Reviewed final pixels and compared every narrated value with the TradingView 1D main-series
receipt.

## Accepted

- `visuals/spx-daily-2026-07-24.png` — full S&P 500 identity, 1D timeframe,
  7,411.98 close, 7,460.98 high and 7,396.53 low; side panel says `Market closed`.
- `visuals/dji-daily-2026-07-24.png` — full Dow identity, 1D timeframe,
  51,947.25 close, 52,118.19 high and 51,682.36 low; side panel says `Market closed`.
- `visuals/aapl-daily-2026-07-24.png` — full Apple identity, 1D timeframe and
  regular-session 333.02 close. The separately labeled post-market quote is not used.
- `visuals/mu-daily-2026-07-24.png` — full Micron identity, 1D timeframe and
  regular-session 920.95 close. The separately labeled post-market quote is not used.
- `visuals/avgo-daily-2026-07-24.png` — technically valid but not selected for the story,
  which already uses the maximum two single names: Apple and Micron.

All five technically valid images have readable identity, OHLC header, volume, axis, and newest
session candle. No modal, open menu, replay watermark, crosshair, or live countdown obscures
the evidence. The first four are the selected working set.

## Rejected but preserved

- `visuals/ndx-daily-2026-07-24.png` — the current-bar label displayed a countdown and
  the side panel said `Market open`.
- `visuals/ukoil-daily-2026-07-24.png` — the current-bar label displayed a countdown,
  the side panel said `Market open`, and the TVC CFD quote is not AP's Brent settlement.

Capture receipts remain unchanged because they prove what was captured; they do not grant
editorial acceptance.

Verdict: **PASS for the four-chart working set; AVGO is valid but unselected, and rejected
images are barred from chart narration.**
