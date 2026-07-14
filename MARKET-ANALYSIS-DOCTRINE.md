# TraderCockpit — Market Analysis Doctrine

The one repeatable process for turning a market day into a script. Any agent (or human) who
runs this process on the same day's facts should land on materially the same analysis, the
same charts, and the same story structure — no matter who is writing.

Peer docs: `BRAND.md` (identity), `GROWTH-AUTHORITY-PLAYBOOK.md` (platform doctrine),
vault `[[TradingView TA Runbook]]` (chart craft), `[[Script Voice Guide — StockedUp Decode]]`
(voice), `[[Claims Ontology]]` (verification). This doc owns the REASONING between the
headline and the script. Written 2026-07-14.

---

## 0. The lens (why we look at anything)

**Portfolio-first.** Every story is judged by exactly one question: *what does this do to a
viewer's portfolio?* Not "is this interesting", not "is this important geopolitically".
The standing topic litmus (operator, 2026-07-13): **name the affected asset class in one
sentence, or skip the topic.**

We are reporters of price and transmission, not forecasters. We say what moved, why it
moved, who gets paid, and what levels would change the story. We never predict, never
advise, always give ranges and conditions.

---

## 1. The fixed watchlist (which markets, and why we look)

Check these EVERY session, in this order. Each exists to answer one specific question.
Levels come off the TradingView feed (`ohlcv`/`quote`), never from memory or a headline.

| # | Instrument | The question it answers |
|---|---|---|
| 1 | **Brent / WTI crude** | Is there a supply/geopolitical premium being priced? Oil is the fastest geopolitics gauge. |
| 2 | **ES / S&P 500** | What is broad risk appetite doing? Everything else is read against this. |
| 3 | **NQ / Nasdaq** | Is the move rate-driven? Growth/duration-sensitive tech exaggerates rate shocks. |
| 4 | **US10Y yield** | The anchor. Rates reprice everything; every equity story gets a rates cross-check. |
| 5 | **DXY (dollar)** | Global liquidity + haven flow. Strong dollar = tightening for the world. |
| 6 | **Gold** | Tug-of-war gauge: real yields (down-gold) vs fear (up-gold). Divergence from yields = fear is winning. |
| 7 | **VIX** | Is the fear PRICED? A big headline with a flat VIX is a story about complacency. |
| 8 | **Sector ETF for the story** (XLE, XLF, XLK, XLU…) | Did the sector confirm the single-name move, or is it idiosyncratic? |
| 9 | **≤2 single names** | Only the names that carry the day's story (largest cap or largest mover in the affected sector). |

Rule of thumb: 1–7 are the *dashboard*, 8–9 are the *story*. A video references the dashboard
but is BUILT on the story instruments.

---

## 2. Shock taxonomy (classify the headline first)

Before asking "what does this mean", classify WHAT KIND of shock it is. The class determines
the transmission channels you check. Every headline is one (occasionally two) of:

1. **Supply shock** — a commodity or good gets scarcer/dearer (war, blockade, OPEC, weather,
   sanctions). First market: the commodity. Second: its producers (up) and its consumers (down).
2. **Demand shock** — growth expectations move (GDP, PMI, retail sales, China data).
   First market: cyclicals + copper/oil (demand side). Second: yields (growth ⇄ rates).
3. **Rates / liquidity shock** — Fed, CPI, jobs, auctions, QT. First market: US10Y + front-end.
   Second: NQ (duration), banks (curve), gold (real yields), DXY.
4. **Policy / regulatory shock** — tariffs, taxes, bans, antitrust. First market: the named
   sector/companies. Second: trade partners' currencies, substitutes/competitors (who wins).
5. **Geopolitical risk premium** — conflict risk without physical disruption *yet*.
   First market: oil + gold + VIX (premium trio). Second: defense names, haven FX (USD, CHF).
   Key discipline: distinguish *premium* (fear priced) from *disruption* (barrels actually missing).
6. **Earnings / micro shock** — one company's numbers. First market: the name. Second: its
   suppliers/customers/peers (read-through). A micro shock is only a video topic if the
   read-through touches an asset class (litmus rule).
7. **Positioning / flows shock** — no new information, but crowded trades unwinding (CTA
   flips, gamma, month-end). The tell: a big move with NO headline. Say so plainly — "this is
   positioning, not news" is itself the story.

---

## 3. The transmission map (the core repeatable step)

For the classified shock, walk the chain **shock → channel → asset → magnitude → duration**,
out loud, in this exact shape:

```
[EVENT] → [what physically/financially changes] → [first asset repriced]
       → [second-order: who earns more / pays more]
       → [third-order: the macro variable it feeds (inflation, growth, rates)]
       → [what that macro variable reprices]
```

Worked example (Hormuz, v4): *20% toll on Hormuz transits* → shipping cost up + supply risk
premium → **Brent +10%** (first order) → producer earnings up: **XOM +4%, CVX +3%**; airlines,
chemicals margin squeeze (second order) → energy CPI expectations up → **US10Y up**, Fed-cut
odds down (third order) → duration-heavy **NQ lags ES** (fourth order).

Rules:
- Chains have **≤4 links** in a script. Deeper is analysis theater; viewers hold three.
- Every link must be **checkable on a chart today**. If a link didn't actually reprice
  (XLE flat on an oil pop), the BROKEN link is the story — see §4.
- State the *mechanism* in plain words ("refiners pay more for crude, so their margin
  shrinks"), never just the correlation ("XLE up because oil up").

---

## 4. Cross-asset confirmation (when is a move a story?)

**A move is a story only when ≥2 correlated assets confirm the same mechanism.**
One asset moving alone is noise, positioning, or a single-name event.

Confirmation cheat-sheet (the pairs we check every time):

| Observation | Confirmed story | If the partner DOESN'T confirm |
|---|---|---|
| Oil ↑ + XLE ↑ | Supply premium flowing to producers | Oil ↑, XLE flat → market doubts it lasts (that's the story) |
| Oil ↑ + US10Y ↑ | Inflation transmission priced | Yields flat → market sees demand destruction, not inflation |
| US10Y ↑ + NQ ↓ | Rates-driven equity move | NQ up anyway → earnings/AI story overpowering rates |
| US10Y ↑ + gold ↑ | Fear overriding real yields — risk-off | Gold down → orderly repricing, not fear |
| VIX ↑ + ES ↓ | Priced fear, coherent risk-off | Headline scary + VIX flat → complacency is the story |
| DXY ↑ + EM/commodities ↓ | Dollar-liquidity squeeze | Both up → idiosyncratic, dig for the real driver |
| Single name ↑ + its sector ETF ↑ | Sector-wide repricing | ETF flat → idiosyncratic, frame it as such |

**Divergence is the better story.** When the cheat-sheet says two things should move together
and they don't, that tension is the most watchable, most expert segment of the video — lead
with it or make it the mid-video re-hook.

---

## 5. What's priced in (the discipline that prevents hindsight scripts)

Before writing a scenario, answer: *how much of this is already in the price?*

- Compare today's level to the pre-event level (chart, not memory). "Oil is up 10% ON this
  news" vs "oil was already up 8% into it" are different stories.
- Recorded pre-release consensus (desk forecasts, published estimates, prior closes) is
  point-in-time-safe — cite it. Post-hoc narratives are not.
- If the market barely moved on a "huge" headline, the pricing-in IS the story
  ("markets had this one figured out weeks ago — here's when they started").

---

## 6. Scenario protocol (how we talk about the future without predicting)

Scripts never predict. They map. Always exactly **three scenarios**, always with chart levels:

- **Base** — what current pricing implies (the market's own forecast, e.g. futures curve,
  desk consensus range).
- **Escalation/bull** — the named trigger + the level that confirms it ("a close above X").
- **De-escalation/bear** — the named trigger + the level that confirms it.

Rules: levels come OFF the chart (runbook accuracy discipline); ranges not single prices
("100 to 150 across desks", never "oil goes to 120"); every scenario names its *trigger*
(an event or a level), because a scenario without a trigger is a prediction wearing a costume.
Named desk numbers (Goldman, JPM, EIA) beat our own — we report the map, we don't draw it.

---

## 7. The 7-question brainstorm (run verbatim, every video)

The fixed script. Answer all seven IN ORDER, in writing, before one line of VO is drafted.
Same questions every time = same analytical spine no matter who writes.

1. **What moved?** Asset, size, timeframe — read off the feed. (No move ≥ noise threshold?
   Check §2.7 positioning, or there is no video today.)
2. **Why did it move?** One shock class from §2 + the transmission chain from §3, ≤4 links.
3. **Who gets paid, who gets hurt?** Winners and losers by sector/asset, each with its
   mechanism in one plain sentence.
4. **What confirms it?** The §4 cross-asset check. List which partners confirmed and which
   diverged. Divergence found → promote it in the story order.
5. **What's already priced?** The §5 check against pre-event levels and recorded consensus.
6. **What's the map?** The §6 three-scenario protocol with chart levels and triggers.
7. **What does the viewer watch next?** Concrete: dates (prints, meetings, earnings),
   levels (the §6 triggers), and the one chart that settles it.

**Output artifact:** `analysis-brief.md` in the production folder — the seven answers, each
sourced. Every claim in it feeds `claims.yaml` (fact gate) and the chart shot list (each
§3 link + §6 level = one chart shot). The script is then WRITTEN FROM THE BRIEF, not from
the headlines — that's what makes two different writers produce the same video.

---

## 8. Verification boundary (what this doctrine may not override)

- Every number through the claims gate (`claims.yaml` + receipts); UNVERIFIED = banned from script.
- Chart = source of truth for LEVELS; news = source of truth for EVENTS (v3 died on live drift).
- Stated timeframe == chart timeframe; symbol shown == asset discussed.
- Not financial advice, no predictions, no hype — persona reports.
- Every asset named in VO gets its own chart shot, full price axis (runbook).
