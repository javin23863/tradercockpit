# Analysis Brief — Weekly Review: The Oil Shock Nobody Bought — 2026-07-25 (Saturday)

Week of Mon 2026-07-20 → Fri 2026-07-24. Levels are chart reads
(`ohlcv-weekly-2026-07-25.json`, last completed 1W bar); events are dated primary sources.
Anything in `FACTS-2026-07-25.md` §7 is banned from script.

**Thesis in one line:** Brent ran 11.8% on an attack on shipping, and every asset that
should have confirmed it — energy equities, volatility, the index — refused.

## 1 What moved

| | Close | Week |
|---|---|---|
| Brent | 98.69 (high 102.00) | **+11.80%** |
| XLE | 59.62 | +3.36% |
| Occidental | 57.30 | +4.45% |
| S&P 500 | 7,411.98 | −0.61% |
| Nasdaq 100 | 28,128.34 | −1.62% |
| VIX | 18.57 | **−1.01%** |
| Micron | 920.95 | +8.48% |
| Apple | 333.02 | −0.22% |
| US 10Y | 4.681 | +2.90% |
| Gold | 4,052.60 | +0.85% |
| Dollar index | 101.465 | +0.71% |

The barrel was the biggest mover on the board by a factor of three. The index fell.

## 2 Why

Attacks on two Saudi oil tankers put a second Middle East shipping route at risk, and Brent
settled **$100.69** on Thursday — AP owns the event and the settlement. By Friday it was back
under $100 and Treasury yields eased. This is a **geopolitical risk-premium** shock in the
§2 taxonomy — fear priced, not barrels missing — and the tape treated it that way.

## 3 Paid / hurt

**Paid:** the barrel itself (+11.80%), and Micron (+8.48%) for reasons that have nothing to do
with oil — South Korean export data driving AI-memory demand, with Sandisk +14% and AMD +8%
alongside it on Tuesday.

**Hurt:** the index (SPX −0.61%, NDX −1.62%). Energy equity holders were paid, but far less
than the commodity — XLE captured under a third of the crude move. Anyone positioned for an
oil shock to lift the energy complex got a fraction of it.

## 4 Confirmation

**The confirmation failed, and that is the story.** Doctrine §4's cheat-sheet says Oil↑ should
bring XLE↑; the non-confirm reading is *"market doubts it lasts."*

- Early week it DID confirm: Tuesday Brent closed 91.63 through Monday's 91.42 rejection high,
  and XLE closed 58.50 through its own 58.385 prior high.
- Then it broke. On the day Brent settled $100.69, **XLE opened 60.244 and closed 59.38** —
  gave the gap back, as did Occidental. Our own Thursday title says it: *"Energy Stocks Barely
  Moved."*
- **VIX fell 1.01% on the week.** An 11.8% oil spike and an attack on shipping, and volatility
  closed lower than it opened. §2's tell is explicit: *"Headline scary + VIX flat →
  complacency is the story."*

Two independent non-confirmations pointing the same way. Under §4 divergence gets promoted, so
this leads the video.

## 5 Priced in

The market priced the premium and then priced it out inside four sessions — 102.00 intraweek to
98.69 by Friday. The Friday tell is the sharpest: oil down and yields down is the textbook
risk-on setup, and the S&P still finished almost flat, the Dow up while the Nasdaq fell. Relief
arrived and was not taken.

## 6 Map

`Tanker attacks on a second shipping route → war-risk premium into Brent (settles 100.69) →
producers do NOT follow (XLE gives back its gap, closes 59.38) → volatility does not bid
(VIX −1.01% on the week) → index leadership narrows to single names (SMCI +19.84% vs GEV −8.69%
Wednesday; AAPL +3.53% vs MU −6.99% Friday)`

Four links, each checkable on a chart. The broken link — producers not following — **is** the
story, exactly as §3 says.

## 7 Watch next

- **FOMC 2026-07-28/29** (federalreserve.gov). The one forward date with a standing primary
  source.
- Brent's **100.69** settle and the **102.00** weekly high are the levels that invalidate the
  complacency read if reclaimed on a close.
- **XLE 60.45** is the line that says producers finally believe it; a close back under **57.30**
  — the trigger named on July 17 — says the whole premium is gone.
- Whether the Section 122 global 10% tariff lapsed or was replaced on 07-24 is **unresolved**
  and must be checked before broadcast.

## Feeds

**Claims → `claims.yaml` candidates:** every figure in §1 from `ohlcv-weekly-2026-07-25.json`
(chart-read, weekly bar); Brent 100.69 settle + tanker event from AP; XLE 60.244/59.38 and
NDX −0.54% / XLI +0.11% / SMCI +19.84% / GEV −8.69% from our own published receipts — **all
require chart re-read before they are spoken**; Mon/Tue figures already receipted in
`daily-2026-07-20` and `-07-21`.

**Charts → shot list:** `chart-plan.json`, five weekly charts —
`03-brent-1w` (102.00 / 100.69 / 98.69), `04-xle-1w` (60.45 / 59.62 / 57.30),
`05-vix-1w` (20.31 / 18.90 / 18.57), `06-spx-1w` (7,504.02 / 7,411.98 / 7,376.00),
`07-mu-1w` (1,011.77 / 970.82 / 920.95).

**Capture status: COMPLETE — all five captured and verified 2026-07-26** on the operator's own
logged-in browser via `tools/visuals/x_chart_shot.py` (X-layer automation; the CDP path wedges
after the first symbol switch and loses the operator layout). Every frame was read back and its
legend + timeframe + OHLC matched the expected bar:

| shot | legend in frame | OHLC in frame |
|---|---|---|
| `03-brent-1w` | CFDs on Brent Crude Oil · 1W · TVC | O 89.30 H 102.00 L 86.12 C 98.69 (+11.80%) |
| `04-xle-1w` | State Street Energy Select Sector SPDR ETF · 1W · NYSE Arca | O 57.56 H 60.45 L 57.41 C 59.62 (+3.36%) |
| `05-vix-1w` | Volatility S&P 500 Index · 1W · TVC | O 18.90 H 20.31 L 16.64 C 18.57 (−1.01%) |
| `06-spx-1w` | S&P 500 Index · 1W · SP | O 7,489.18 H 7,525.94 L 7,376.00 C 7,411.98 (−0.61%) |
| `07-mu-1w` | Micron Technology, Inc. · 1W · NASDAQ | O 885.57 H 1,011.77 L 858.90 C 920.95 (+8.48%) |

Operator layout present in all five (Premium / Equilibrium / Discount zones, standing levels,
EQH/EQL marks). `SP:SPX` confirms an authenticated session, not `SP_NAUTH`. Clips assembled to
1920×1080 / 30fps / 10s in `visuals/`. **Pure charts, no drawn overlays** — the V03 weekend-review
precedent; levels are spoken and carried by q-cards.

**Not yet written:** `vo.txt`. Under the format-v2 edit contract the script comes after the
captures exist, not before.
