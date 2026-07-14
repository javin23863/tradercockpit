# HANDOFF — video-02-hormuz-v4 (EXPANDED CUT, session 2026-07-14 resume)

Operator decision 2026-07-14: **expand to 10-12 min** ("8+mins always 10-12 best").
Script expanded 880 → 1779 words (~11.5 min @ 154 wpm). Deliverable = `build/master-clean.mp4`
(YouTube auto-captions, NO burned text). **NO UPLOAD without operator review.**

## State: DONE this session (all verified)

| Piece | State |
|---|---|
| TV wedge | FIXED — full quit (exact main PID) + relaunch, orphaned CDP targets gone |
| Script | vo.txt expanded sections 03/05/06/07/08/11/12. **Claims gate PASS (64 claims, 64 receipts)** |
| Claims | + clm-chart-xom-mon / cvx / us10y / jpm (all off replay-pinned feed 2026-07-14) |
| Charts | ALL 11 frame-verified: 03-oil, 05-spx (re-shot clean), 06-ixic, 06b-nvda, 07-xle, 07b-xom, 07c-cvx, 08-gold, 08b-us10y, 11-scen (re-shot w/ 100/110/120/130/150 lines — VO now speaks 130+150), 12b-jpm |
| Clips | ALL 11 chart clips rendered + spot-verified: 03-oil-ta, 05-spx-ta, 06-chips-a/b, 07-energy-a/b/c, 08-gold-a, 08-yield-b, 11-scenarios, 12-x-jpm (sorted-glob order inside sections) |
| User chart | RESTORED: drawings removed, autoscale on, replay stopped, TVC:UKOIL 1D, watchlist reopened |

New chart-true numbers (replay-pinned Monday bar):
XOM Fri 138.88 → Mon 144.51 (+4.05%, high 145.23). CVX Fri 176.40 → Mon 182.20 (+3.29%).
US10Y Fri 4.561 → Mon 4.624 (yields ROSE — gold-hedge-failed tell). JPM Fri 336.47 → Mon 334.53 (−0.58%).

## BUILD COMPLETE — awaiting operator review

- Final script 2009 words; measured clone rate ~191 wpm (NOT 154 — plan durations with 191).
  First 9.3-min cut was under the 10-12 band → sections 02/09/13 expanded (+300 words), gate re-PASS (64 claims, 67 receipts).
- All 13 wavs final text, vo-full 10.6 min. Captions stage done (447 cues).
- Assemble done. Section 13 padded with 13-a-scen + 13-b-jpm (copies of scenario/JPM clips)
  to kill the visible GE loop-restart (outro clip 23.7s vs 51.8s section).
- **`build/master-clean.mp4` = 10:35, 134 MB** — ffprobe verified + 5 spot frames Read
  (hook globe badge, Brent lines, Chevron, IEA news card, JPMorgan). No burned captions.
  master.mp4 = burned-caption twin, do NOT ship.
- **STOP: operator reviews master-clean.mp4. No upload, no channel writes.**

## New tool scars this session

- cdp_chart_shot: OHLC header + dashed crosshair contaminate shots when ANY pointer sits
  over canvas — including the operator's REAL mouse. Fix in tool: park synthetic pointer
  (800,15) after connect AND again right before screenshot. (5,5) hovers the account
  button → tooltip overlays header. Hands off TV while shooting.
- Operator right-click during shoot leaves a context menu in frame → `tv ui keyboard Escape`, re-shoot.
- Drawings do NOT survive app relaunch (not cloud-saved on Unnamed layout) — old .ids are dead after a restart.
- Price scale for off-screen levels (150 line): `tv ui eval` →
  `chart.getPanes()[0].getMainSourcePriceScale().setAutoScale(false); setVisiblePriceRange({from,to})`.
  Shoot WITHOUT --fit (Alt+R resets scale). Restore setAutoScale(true) after.
- Right watchlist panel eats ~290px of canvas → `tv ui panel watchlist close` before shooting, reopen at restore.
- Claims gate flags rhetorical number-words ("two lines", "re-price first", "a quarter that") —
  rephrase those instead of minting fake receipts; honest arithmetic (83.31→100 ≈ "twenty percent move") maps to the chart claim.

## Review checklist (operator's rejection history)

TA charts dominant ✓ (11 chart clips / 13 sections) · full price axis ✓ (right-crop) · news badges ✓ ·
GE sparingly ✓ (2 of 13) · portfolio-first voice ✓ · chart numbers == spoken numbers ✓ (claims gate) ·
timeframe said == shown ✓ (all daily, replay-pinned) · no stale dates ✓ · runtime 10-12 ✓ (~11.5 min).
