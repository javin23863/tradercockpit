# Pre-doctrine verbiage defects — 2026-07-20

**Status:** approval-only audit. No live profile, post, pin, website, or repository source was
changed by this sweep.

Sources checked: `social-ops/PROFILE-READINESS-2026-07-15.md`,
`social-ops/analytics-latest.json`, `tools/channel_seo.py`, and every `docs/*.html` file.

## 1. Live profile defects

| Surface | Verified current defect | Approval-ready replacement |
|---|---|---|
| YouTube | Display name is `Tradercockpit`; description is the old product/gauntlet pitch and contains the broken `https://javin23863.github.io/soical/` path. | Use the YouTube block in `profile-copy-2026-07-20.md`. |
| YouTube description source | `tools/channel_seo.py:26–30` would apply `No signals. No courses. No performance promises.` plus a simulated-product CTA, and does not carry the mandatory disclaimer byte for byte. | Replace the whole `DESCRIPTION` value with the copy-sheet description before any future authorized run. |
| YouTube keyword source | Live keywords were not exposed by the readiness artifact. The local applier still contains `trading strategy backtest`, `ICT trading tested`, `smart money concepts`, and `SMC`. | Use the market-news keyword line in the copy sheet; require Studio readback before approval. |
| Instagram | Name field is only `TraderCockpit`, so its best search surface omits `Market News`. The exact live bio was not captured, so the byte-exact disclaimer cannot be verified. | `TraderCockpit · Market News` plus the 146-character Instagram bio in the copy sheet. |
| TikTok | Display name is `trader cockpit`, omitting brand capitalization and the searchable topic. The exact live bio was not captured, so the byte-exact disclaimer cannot be verified. | `TraderCockpit · Market News`; 78-character mandatory disclaimer as the bio. |
| Facebook | Page name is `Tradercockpit`; no claimed username was visible. The intro is news-first, but its exact bytes were not captured and therefore the mandatory disclaimer is unverified. | Use the Facebook fields in the copy sheet. |

Handle differences are defects in parity, but no handle change is recommended without operator
authorization and a fresh availability/readback check.

## 2. Old slogan vocabulary

Every consumer-facing instance found in the supplied live analytics is listed below.

| Surface / evidence | Pre-doctrine string | Compliant replacement |
|---|---|---|
| YouTube title, `analytics-latest.json:141` | `Don't Trade the Siren. Trade the Pressure Chain. #Shorts` | `Oil +10%, Energy +4%: What Moved #Shorts` |
| YouTube title, `analytics-latest.json:186` | `The market is pricing the Strait, not the end of the world #Shorts` | `5 Tankers vs 130 a Day: What Hormuz Actually Closed #Shorts` |
| YouTube title, `analytics-latest.json:201` | `Iran Oil Deadline Day Meets a Cracking AI Trade` | `Iran Deadline Day and TSMC's $403.50 Floor` |
| YouTube title, `analytics-latest.json:216` | `The Nasdaq Broke. The S&P Held.` | `Nasdaq Broke 7431, S&P Held Its Band — The Divergence` |
| YouTube title, `analytics-latest.json:231` | `Iran War Widens as Oil Holds $84` | `Oil Holds $84 as the Risk Premium Sticks` |
| Facebook Reel caption, `analytics-latest.json:469` | `Don't trade the siren. Trade the pressure chain.` | `Oil +10%, energy shares +4%: the Hormuz move reached producer earnings.` |
| Instagram Reel caption, `analytics-latest.json:696` | `Don't trade the siren. Trade the pressure chain.` | `Oil +10%, energy shares +4%: the Hormuz move reached producer earnings.` |
| TikTok caption, `analytics-latest.json:801` | `clip-002-do-not-trade-the-siren.vertical` | `Oil +10% and producer earnings: what the Hormuz toll changed. #oil #hormuz #energystocks #markets #FinTok` |
| Internal next-action text, `analytics-latest.json:880` | `move the pressure-chain payoff before the first chart transition` | `move the oil-to-energy transmission before the first chart transition` |

No `pressure chain`, `pressure-chain`, or `siren` occurrence exists in `docs/*.html`.

## 3. Pinned-post state

The supplied analytics has no pinned-state field, and the July 20 live-copy audit says YouTube
pinned comments remain unused/unverified. Therefore **zero pinned strings can be certified as
current** from local evidence; that is a readback defect, not proof that no pin exists.

Approval-ready pinned comment for current videos, with no dead offer CTA:

```text
Sources and observation times are in the description. Which asset should I map next?

Research tooling, not financial advice. No performance is promised or implied.
```

Before applying it, inspect the live pin state and approve the exact target video and text.

## 4. Static HTML defects

### A. Home-page metadata — `docs/index.html:7–22`

Eight instances still describe a strategy-testing product instead of the market-news channel:

- Title, Open Graph title, and Twitter title: `TraderCockpit — Test the strategy before you buy the story`.
- Meta description: `A concept preview for testing published trading strategies through an evidence-first robustness pipeline before risking money on the claim.`
- Meta keywords: `trading strategy test, backtest robustness, strategy validation, Monte Carlo, walk-forward analysis`.
- Open Graph and Twitter descriptions: `Can the rules survive an evidence-first robustness pipeline? Concept preview; no performance promises.`
- JSON-LD description: `Media and product education for evidence-first trading-strategy research.`

Replace all title instances with:

```text
TraderCockpit — Market News Mapped to Portfolio Impact
```

Replace all description instances with:

```text
Sourced market analysis across oil, equities, rates, and geopolitics, mapped to portfolio impact.
```

Replace the keywords with:

```text
market news, stock market news, oil market news, interest rates, geopolitics and markets, S&P 500, Nasdaq, crude oil, market analysis
```

### B. Hero, simulator, and social dock — `docs/index.html:228–297`

| Current string | Replacement |
|---|---|
| `TRADERCOCKPIT // TEST THE CLAIM` | `TRADERCOCKPIT // MARKET NEWS` |
| `Before you buy the holy grail, make its rules survive the gauntlet.` | `Market news, mapped to portfolio impact.` |
| Strategy/robustness paragraph at lines 230–232 | `Sourced analysis of oil, equities, rates, and geopolitics. Watch the latest breakdowns on YouTube.` |
| `GAUNTLET // AWAITING CANDIDATE` | `MARKET MAP // CHOOSE A STORY` |
| `SIMULATED PRODUCT PREVIEW — NOT A LIVE RUN` | `ILLUSTRATED RESEARCH WORKFLOW` |
| Assistant-concept instruction at line 244 | `Choose a market story to preview how TraderCockpit maps it across assets.` |
| `LOCAL-FIRST VOICE · ONTOLOGY-GROUNDED · CONFIRM BEFORE FULL BATTERY` | `SOURCED INPUTS · CROSS-ASSET MAP · HUMAN APPROVAL` |
| `Review simulated run` | `Preview the market map` |
| Strategy-concept hint at line 261 | `Choose a market story. This illustration does not use live data.` |
| `Confirm the illustration` | `Review the illustration` |
| Visual-theater paragraph at line 264 | `This preview uses no live market data and produces no trading signal or performance result.` |
| `Run simulation` | `Run illustration` |
| `run another strategy through it` | `Choose another market story` |
| `PUBLIC SIGNAL ROUTER` | `PUBLIC CHANNELS` |
| `ONE RESEARCH DESK // FOUR DESTINATIONS` | `ONE MARKET DESK // FOUR PLATFORMS` |
| TikTok `DAILY SIGNAL BRIEFS` | `DAILY MARKET NEWS` |

### C. Product-first middle sections — `docs/index.html:304–340`

The headings and all three explanatory blocks remain a product/gauntlet explainer. Replace that
entire visible section with one market-news method block:

```text
HOW EACH BREAKDOWN WORKS
1. Start with dated sources.
2. Trace the event through affected assets.
3. Separate observed prices from editorial interpretation.
4. State the level or event that would change the read.
```

This single replacement covers `the claim becomes a test`, `Write the actual rules`, `Preview is
not a verdict`, `Keep the receipt`, the alpha/edge quote, `what the product preview demonstrates`,
its three cards, `the intended consumer workflow`, and its four strategy-testing steps.

### D. Dead-offer and disclaimer copy — `docs/index.html:344–375`

| Current string | Replacement / action |
|---|---|
| `TraderCockpit publishes market analysis and explains the consumer-product concept without promising a winner.` | `TraderCockpit maps sourced market news to portfolio impact.` |
| `DAILY MARKET MAP + PRODUCT WAITLIST` and `Join the product waitlist` | Keep hidden/remove from navigation until Buttondown passes submit → confirmation → subscriber readback. Today use `Watch the latest market breakdowns`. |
| `Research only—not financial advice.` | `Research tooling, not financial advice. No performance is promised or implied.` |
| `Watch the research` | `Watch market breakdowns` |
| `RESEARCH INSTRUMENT — NOT FINANCIAL ADVICE. NO PERFORMANCE IS PROMISED OR IMPLIED.` | `Research tooling, not financial advice. No performance is promised or implied.` |
| `The gauntlet above is a simulation for illustration, not a product run or performance result.` | `The illustration above uses no live market data and produces no performance result.` |

### E. Other static pages

| Evidence | Current string | Replacement / action |
|---|---|---|
| `docs/thanks.html:6` | `Click the confirmation link to join the daily market map and product waitlist.` | Until the list is live: `Email signup is not open yet. Watch TraderCockpit on YouTube.` |
| `docs/confirmed.html:6` | `Your email is confirmed. Expect sourced market maps; no individualized financial advice and no invented product claims.` | Keep unreachable until the list is live. Then: `You're subscribed. Expect the sourced daily market map.` followed by the mandatory disclaimer. |
| `docs/confirmed.html:7` | `Watch the research` | `Watch market breakdowns` |
| `docs/refund-policy.html:23–24` | `It is not investment advice and no trading performance is promised or implied.` | `Research tooling, not financial advice. No performance is promised or implied.` |

`docs/strategy-claim-audit-checklist.html:116` already carries the mandatory disclaimer byte for
byte. No replacement is needed there.

### F. Runtime-generated home-page strings — `docs/index.html:531–642`

These strings are declared in JavaScript but are visible to visitors, so they are static public
copy for this sweep. The boot text (`honest ledger`, `gate array`, `product manifest`, `loading
gauntlet`), the six strategy chips (`ICT / Smart Money`, `SMC Order Blocks`, `Supply & Demand`,
`MA Golden Cross`, `RSI Reversal`, `Breakout + Volume`), all 12 gauntlet phases, and the runtime
`candidate`, `breeding 1,024 parameter variants`, and `gauntlet complete` logs are pre-doctrine
product language.

Replace the boot labels with:

```text
TRADERCOCKPIT // MARKET MAP
loading dated sources
loading affected assets
loading cross-asset checks
operator approval required
publishing disabled
```

Replace the six strategy chips with:

```text
Oil
Equities
Rates
Currencies
Geopolitics
Economic data
```

Replace the 12 phase names with:

```text
source check
event time
market snapshot
affected assets
transmission map
cross-asset check
base case
escalation case
relief case
invalidation
next catalyst
approval gate
```

Replace the runtime log language with:

```text
story: {selected topic}
mapping affected assets
illustration complete — no trading signal
```

## Gate status

Gate command used `OpenMontage\.venv\Scripts\python.exe` and
`tools.script_style_gate.audit_text()` on every direct replacement line separately. Final receipt:
**66/66 PASS; 0 BLOCK.** The mandatory disclaimer was also tested separately in the profile-copy
receipt and passed byte for byte. Advisory warnings were limited to neutral-copy heuristics
(`missing editorial owner`, `automatic summary ending`, and list-shape warnings); none was a
performance/claims block.
