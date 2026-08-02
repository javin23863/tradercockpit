# Adversarial review — indicator-confluence automation

Date: 2026-07-30  
Reviewed: `indicator-confluence-primary-sources-2026-07-30.md`, `vix-vvix-multitimeframe-primary-sources-2026-07-30.md`, and the proposed RSI/MACD/DMI/location/VIX/VVIX multi-timeframe rule.  
Boundary: pre-implementation review only. No code or live-order capability was reviewed.

## Verdict

**Do not enable live order submission.** The research supports a candidate stress-and-confluence hypothesis, but it does not establish a tradeable edge, cross-asset portability, or Pine/thinkScript equivalence. The safe first release is a closed-bar study/strategy that plots, scans, alerts, and simulates orders. Thinkorswim conditional orders and any TradingView alert-to-broker bridge remain disabled until the acceptance criteria below pass out of sample.

## Severity-ranked findings

### Critical 1 — the daily evidence cannot validate an intraday strategy

The official free Cboe file supplies daily VVIX history. It cannot show whether a 5-minute or 15-minute VVIX threshold was known at an intraday entry. Applying day `t`'s final VVIX close to bars earlier on day `t` is look-ahead leakage. The only point-in-time-safe public-data rule is to use the prior confirmed daily close throughout the next session. A genuine intraday VVIX rule requires timestamped historical index-feed observations and a predeclared common trading window. Cboe's methodology says VVIX is disseminated during a defined U.S. session, while futures and bitcoin trade longer hours. ([Cboe methodology](https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Selected_Broad_Based_Index_Equity_and_ETF_Volatility_Indices.pdf))

**Consequence:** none of the current daily forward-return tables validate 5m, 15m, 1h, or 4h entries.

### Critical 2 — there is no single reproducible result artifact

The research note reports a 2016–2026 Cboe/FRED sample with 2,512 common sessions and 50 cooldown crossings. The user-facing summary reported a 2007–2026 Cboe sample with 4,921 observations and 72 non-overlapping crossings. It also introduced bootstrap, maximum-adverse-excursion, cross-volatility, and RSI-stratified conclusions that are not reproduced in either reviewed note with a versioned calculation script, input hashes, event ledger, seed, or full output.

Those numbers may each be legitimate under different definitions, but they are not yet one auditable result. Sample, source, event spacing, missing-value handling, horizon, and return convention must be reconciled before any number becomes a strategy premise.

**Consequence:** claims such as “VVIX crossings plus RSI below 40 did better” must not be encoded until the exact calculation is reproducible.

### Critical 3 — “automation” means different things on the two platforms

TradingView Pine strategies place hypothetical orders in a broker emulator. Pine cannot directly place orders with TradingView-connected brokers; external software must interpret alerts and execute them. Alerts are separate UI objects, and TradingView snapshots the script, inputs, symbol, and timeframe when an alert is created, so later script/input changes do not update an existing alert. ([TradingView strategy FAQ](https://www.tradingview.com/pine-script-docs/faq/strategies/); [TradingView alerts](https://www.tradingview.com/pine-script-docs/concepts/alerts/))

Thinkorswim `AddOrder` strategies also generate hypothetical orders and cannot send real orders. Thinkorswim can submit or cancel a **preconfigured** conditional order when a one-plot study condition becomes true, but that is not a general autonomous portfolio engine. The order must first be constructed, reviewed, and sent by the operator. ([Schwab strategy tutorial](https://toslc.thinkorswim.com/center/reference/thinkScript/tutorials/Basic/Chapter-7---Creating-Strategies); [thinkScript conditional orders](https://toslc.thinkorswim.com/center/howToTos/thinkManual/Trade/Order-Entry-Tools/Order-Types/thinkScript-in-Conditional-Orders))

**Consequence:** the first implementation may accurately claim “signals, alerts, scans, and simulated orders.” It may not claim unattended cross-platform execution.

### High 1 — the hypothesis family is already heavily shopped

The candidate family contains at least:

- VVIX levels 90/100/110/120/130 or a rolling percentile;
- VIX rising/falling and VVIX rising/falling;
- RSI state, crossing, failed reclaim, and slope around 40/50/60;
- MACD 7/28/7 crossover, zero line, histogram, regular divergence, and hidden divergence;
- ADX 20 or 25, rising/falling, and DI spread;
- premium/equilibrium/discount plus several support/resistance interpretations;
- five timeframes, several timeframe pairs, multiple sessions, long/short states, seven exposures, and several holding horizons.

Selecting a profitable-looking combination after viewing these outcomes is multiple testing. “Four of five timeframes,” “RSI above 60,” and “VVIX above 110” are research choices, not market constants. The absolute 110 threshold is especially regime-dependent: the reviewed research found it on 56.1% of sessions in 2020–2022 but only 4.5% in 2006–2009.

**Required control:** freeze one primary ruleset, one comparator, one event definition, one cost schedule, and one holdout before further results are inspected. Adjust inference for the full declared family; do not promote an isolated uncorrected cell.

### High 2 — multiple timeframes are nested observations, not independent votes

Five-minute bars compose 15-minute bars, which compose hourly and daily bars. A “four of five agree” vote counts the same underlying price path several times and creates a variable latency: the daily component updates far less often than the 5-minute component. It also makes a universal implementation difficult because 4-hour bars may be anchored differently by feed and session.

**Required control:** test one anchor/trigger pair per holding style—15m/5m, 1h/15m, or 1D/4h. The anchor must be strictly higher than the trigger and must use only its last confirmed bar. Results for one pair do not validate another.

### High 3 — higher-timeframe and pivot logic can silently leak future data

In Pine, an unoffset higher-timeframe `request.security()` value can repaint. TradingView's documented non-repainting pattern is an expression offset by one requested bar together with `lookahead = barmerge.lookahead_on`; using lookahead without the offset leaks the final higher-timeframe value into historical bars. ([TradingView other timeframes](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/); [TradingView repainting](https://www.tradingview.com/pine-script-docs/concepts/repainting/))

In thinkScript, a secondary aggregation cannot be lower than the chart's primary aggregation, and mixing primary-context functions into a secondary-aggregation expression can silently make the whole expression use the primary context. ([Schwab secondary aggregation](https://toslc.thinkorswim.com/center/reference/thinkScript/tutorials/Advanced/Chapter-11---Referencing-Secondary-Aggregation))

Regular/hidden divergence and pivot support/resistance add another confirmation delay. If a pivot needs right-side bars, the signal is knowable only after those bars close. Back-plotting the marker on the pivot bar is visually useful but is an invalid entry timestamp.

### High 4 — the support/resistance and “premium/discount” component is not portable

LuxAlgo's proprietary chart zones describe context, but the reviewed material does not contain a formula that can be reproduced exactly in Pine and thinkScript. “At support,” “near discount,” “reclaimed equilibrium,” and “rejected premium” have no fixed swing algorithm, lookback, width, confirmation delay, or boundary tolerance. Different discretionary drawings can turn the same bar into a buy, sell, or no-trade observation.

**Required control:** either obtain an authorized, exact formula or clearly substitute one deterministic public rule. The substitute must freeze swing selection, confirmation delay, zone width/tolerance, and reclaim/rejection definition. It must not be labeled “LuxAlgo parity.”

### High 5 — instrument, feed, and session substitutions can change the signal

VIX and VVIX are SPX/VIX-option-derived indices, not directly tradeable instruments. ES, SPY, SPX, and a continuous futures chart have different sessions, rolls, dividends, and prices. Similar problems apply to spot/ETF/futures choices for gold, crude, Treasuries, DXY, and bitcoin. TradingView and thinkorswim may use different continuous-contract construction, exchange timezone, extended-hours setting, and historical corrections.

After VVIX stops disseminating, carrying its last value into an overnight ES or bitcoin bar is a stale-regime convention, not a fresh confirmation. That convention must be visibly labeled and tested separately. No result may switch proxy, contract, session, or roll rule after outcomes are known.

### High 6 — entry and exit economics are unspecified

The concept defines filters but not a complete strategy. Missing items include:

- executable instrument and order type;
- next-bar versus same-close entry;
- stop/invalidation calculation;
- target or trailing exit;
- maximum holding time;
- position sizing and maximum exposure;
- pyramiding and simultaneous-signal policy;
- daily-loss/kill-switch behavior;
- duplicate-alert and reconnect handling;
- spread, commissions, slippage, gaps, partial fills, and futures roll costs.

TradingView warns that historical strategy fills are simulated and normally occur on a later tick/bar; changing intrabar recalculation can change behavior and introduce repainting. ([TradingView strategies](https://www.tradingview.com/pine-script-docs/concepts/strategies/))

**Consequence:** win rate or gross forward return alone cannot justify order automation. The optimization objective must be frozen as expectancy after costs subject to a maximum drawdown or risk limit—not “make as much money as possible.”

### Medium 1 — indicator semantics still conflict

The user hypothesis says RSI below 60 usually trends down, while the research protocol defines bullish `>60`, bearish `<40`, and neutral in between. Those are different rules. MACD “positive/negative divergence” must distinguish regular reversal divergence from hidden continuation divergence. MACD MA types and pivot confirmation must be explicit. ADX is directionless; +DI/−DI are directional-movement measures, not money flow. ([TradingView RSI](https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/); [TradingView MACD](https://www.tradingview.com/support/solutions/43000502344-moving-average-convergence-divergence-macd-indicator/); [TradingView DMI](https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/))

### Medium 2 — platform parity cannot be assumed from matching input lengths

EMA/Wilder initialization, warm-up history, missing bars, session boundaries, corporate-action adjustments, and feed corrections can make Pine and thinkScript disagree even with identical nominal inputs. ThinkScript's EMA/Wilder functions prefetch historical bars, which affects early values. ([Schwab past offset and prefetch](https://toslc.thinkorswim.com/center/reference/thinkScript/tutorials/Advanced/Chapter-12---Past-Offset-and-Prefetch))

The systems therefore need a signal-parity receipt, not merely successful compilation.

## Acceptance criteria for Pine and thinkScript

### A. Frozen specification

- One versioned truth table defines `long`, `short`, `exit`, and `no_trade`.
- Defaults freeze symbol/proxy, session, trigger timeframe, anchor timeframe, RSI rule, MACD MA types and divergence handling, DMI/ADX rule, VVIX rule, location rule, entry timing, exits, sizing, cooldown, and costs.
- The first test uses only one anchor/trigger pair. Other pairs and assets are separate declared experiments.
- Any omitted component is labeled omitted. In particular, do not approximate LuxAlgo zones or divergence without saying so.

### B. Point-in-time safety

- Signals use closed trigger bars only.
- Anchor values are from the last confirmed anchor bar; Pine uses the documented offset-plus-lookahead pattern and rejects an anchor that is not higher than the chart timeframe.
- ThinkScript runs on the trigger chart and requests only same-or-higher aggregations. Secondary values remain isolated from primary-context expressions until the final Boolean combination.
- Daily VVIX mode uses the prior confirmed daily close for the entire next session. Intraday VVIX mode is unavailable unless timestamped intraday history exists.
- Pivot/divergence signals occur on the confirmation bar and are never backdated to the pivot.
- Reloading the Pine script and replaying the same data produces the same timestamped signals. No signal disappears or moves earlier.

### C. Data and session integrity

- TradingView and thinkorswim symbols are explicit inputs with verified defaults (for example, each platform's actual VVIX identifier); unavailable or stale data produces a visible `NO DATA/STALE` state and blocks entries.
- RTH/extended-hours choice and exchange timezone are explicit and identical in the comparison.
- Futures use one documented continuous-contract/roll convention, or exact dated contracts. Results identify which was used.
- A stale carried-forward VVIX observation cannot be described as a new intraday confirmation.

### D. Cross-platform signal parity

- Both implementations expose the component states—RSI, MACD, DI direction, ADX strength, VVIX regime, anchor state, location state—and the final decision, not only arrows.
- On a locked comparison set covering at least one calm period, one high-VVIX period, and one session boundary, every final signal matches direction and first-knowable bar after accounting for documented feed differences.
- Any mismatch is explained bar by bar. “Close enough” visual agreement is not a pass.
- Warm-up bars remain ineligible until every indicator and higher-timeframe input has sufficient confirmed history.

### E. Strategy and execution realism

- Backtests enter no earlier than the first executable tick/bar after the condition becomes known. Same-bar close fills are not assumed unless a real order path can demonstrate them.
- Commission, spread/slippage, roll, and gap assumptions are explicit; results include gross and net returns, maximum adverse excursion, maximum drawdown, turnover, and independent episode count.
- One signal ID can create at most one intended order. Entry, exit, reversal, pyramiding, and conflicting-timeframe behavior are deterministic.
- Position size is capped and derived from a frozen risk rule; stop/invalidation exists before an entry signal is emitted.
- Pine outputs alerts only. Alert messages include strategy version, signal ID, symbol, timeframe, closed-bar timestamp, side, intended entry type, invalidation, and stale-data status. No credentials are embedded.
- ThinkScript strategy orders remain hypothetical. A separate conditional-order study has exactly one Boolean plot, as Schwab requires, and is not armed until the operator reviews the exact order ticket and the holdout gate passes.

### F. Evidence gate

- One versioned analysis script or notebook produces the canonical event ledger and every reported table from source files with recorded URL, download timestamp, hash, timezone, and missing-value handling.
- Results are reported by asset and timeframe, not pooled into a universal claim.
- Controls include unconditional/matched sessions and a simpler baseline that removes each confluence component. The full rule must add net value beyond the simpler baseline.
- Evaluation is chronological with a frozen holdout; stress episodes, not bars, are the inference unit. Overlapping horizons use episode-clustered or block-bootstrap intervals.
- The declared asset/timeframe/horizon family receives a multiple-testing correction. At least 30 independent episodes are required per promoted cell; otherwise the result is `underpowered`.
- The primary rule must remain positive after costs, avoid sign reversal across major subperiods, and pass a genuine future-data holdout before any live conditional order is armed.

## Minimum acceptable release

Release 1 should be two non-repainting, closed-bar **signal studies** plus simulated strategies:

1. one TradingView Pine v6 script for plots, alerts, and broker-emulator testing; and
2. one thinkScript study/strategy pair for plots, local alerts/scans, and hypothetical orders.

Use a deterministic, disclosed location rule; prior-daily VVIX only; one anchor/trigger pair; and no live order path. That is enough to test parity and collect forward observations without pretending the hypothesis is already validated.

## Runtime re-review — 2026-07-31

After reviewing the OnDemand receipts recorded in
`tools/indicators/README.md`, the independent reviewer updated the verdict:

- **Research study use: PASS.**
- **Continued OnDemand hypothetical testing: PASS.**
- **paperMoney conditional-order testing: GO to begin, not yet accepted.**
  Start only from an unmistakable paperMoney banner with no live working
  orders.
- **Live use: BLOCK.**

The explicit `TC SHORT TIME` path is now proven by two `/GC`
15-minute/1-hour OnDemand report rows. The remaining gates are a verified
one-plot condition-to-native-OCO paperMoney lifecycle (including duplicate,
rearm, and cancel behavior); explicit STOP and TARGET receipts with frozen
entry-time levels plus a same-bar collision proving stop precedence; and a
chronological net-cost holdout with independent episode count, expectancy,
drawdown/MAE, and subperiod stability. The zero-trade `/ES`, TSLA, and AAPL
15-minute/1-hour results must not be “fixed” by relaxing thresholds. NVDA's
price-scaling discontinuity disqualifies that OnDemand window as evidence.
