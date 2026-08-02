# Edgeful's underlying concept: conditional market statistics for a concept library

**Date:** 2026-08-02
**Amended:** 2026-08-02 — R1 from the Claude review (REVISE): example artifact dates brought inside the Futures data ceiling
**Scope:** Public Edgeful videos, first-party Edgeful documentation, primary statistical references, and the governed research surfaces already present in this repository. This is not a review of Edgeful as software and does not inspect or modify Futures or Register.
**Method:** A bounded sample of report demonstrations was checked against what was visible on screen and said in the accompanying captions. Product claims that could not be reconstructed from public row-level data are labeled as claims or inferences, not independently validated results.

## Bottom line

The useful idea is simpler than it first appears. Edgeful has put a **conditional event-study layer** on top of a library of market concepts:

1. Define a market event precisely, such as an initial-balance break, overnight gap, prior-day-high break, or daily-range threshold.
2. Detect every eligible historical occurrence under a declared symbol, session, time zone, and lookback.
3. Measure what happened next, or how the event completed, using a fixed outcome definition.
4. Slice the occurrences by pre-event context such as weekday, direction, size, session, or volatility state.
5. Report the count, denominator, empirical rate, and often the underlying dates.
6. At decision time, map today's known context to the corresponding historical cohort.

In notation, most of the headline cards are estimates of:

\[
\hat p = \frac{\#\{\text{eligible observations where setup }X\text{ and outcome }Y\}}{\#\{\text{eligible observations where setup }X\}}
\]

The missing layer for a concept library is therefore not a new indicator and not an AI prediction engine. It is a **versioned behavior dossier for each concept**: exact event semantics, an event ledger, conditional outcome distributions, uncertainty, point-in-time safety, and validation state.

The most important qualification is that a displayed `70%` does **not** automatically mean “this trade has a 70% chance of winning.” Depending on the report, it can mean:

- 70% of eligible sessions exhibited a pattern;
- 70% of days that eventually became a particular type completed by a stated time;
- price touched a level on 70% of qualifying days;
- the average realized range was 70% of a benchmark;
- or 70% of a selected historical subgroup had a binary outcome.

Those have different denominators, decision-time usefulness, and economic meaning.

## What the reports are actually doing

Edgeful's [platform guide](https://www.edgeful.com/blog/posts/what-is-edgeful) describes the reports as historical probabilities rather than signals. Its public [subreport reference](https://help.edgeful.com/en/articles/14198526-subreports) shows that one base concept can be regrouped by weekday, size, close, direction, extension, retracement, level, risk/reward, time, fill time, double break, rejection, spike, prior candle, gap type, color, overnight state, or streak.

That implies four separate objects:

| Object | Example | What must be frozen |
|---|---|---|
| Eligibility universe | All NQ New York sessions with complete bars | Instrument/contract mapping, calendar, session, time zone, data-quality exclusions |
| Event or setup | First break of the first 60-minute range | Range window, boundary equality, first/all occurrence rule, known-at timestamp |
| Context | Tuesday, up gap, small range, prior candle green | Feature formula, bucket edges, and when each feature became knowable |
| Outcome | Opposite side also breaks before session close | Horizon, success/failure/unresolved states, and outcome-available timestamp |

Every filter changes the cohort and usually the denominator. A credible result must travel with all four objects; a percentage detached from the current selectors is not reproducible.

The public reports also mix several statistical shapes:

- **Binary:** filled/not filled, respected/exceeded, green/red close.
- **Multinomial:** single break, double break, or no break.
- **Time-to-event:** first break before or after a clock time.
- **Magnitude:** maximum extension, retracement, actual range as a fraction of ADR.
- **Path-dependent:** which boundary formed or broke first, then what happened next.

Those should not all be flattened into a generic “win rate.”

## Representative demonstrations

The following bounded sample covers the mechanics most relevant to a concept library:

| Date | Video | What was demonstrated |
|---|---|---|
| 2026-07-29 | [A New IB Timeframe: How to Trade the 2-3pm Initial Balance on NQ](https://www.youtube.com/watch?v=6HYJD3SEcLk) | A custom-session 60-minute initial balance, outcome classes, raw counts, and extension touches |
| 2026-05-06 | [How I caught a 146-point NQ move using 4 data-backed reports](https://www.youtube.com/watch?v=lhU2wiJfWs0) | Several conditional rates used together as directional confluence |
| 2026-02-25 | [NEW Edgeful AI v1: connect & combine reports](https://www.youtube.com/watch?v=eebhWxnEbHA) | Joining report rows by date, then asking exploratory questions across the joined observations |
| 2026-01-25 | [How to use Edgeful's reports: step-by-step guide](https://www.youtube.com/watch?v=ihe71f_H12A) | Report selectors, lookbacks, tables, filters, and report-specific definitions |
| 2026-01-13 | [ES Average Daily Range: The 70% Probability Most Traders Ignore](https://www.youtube.com/watch?v=LyRdL7hM8sE) | Point-in-time ADR construction, binary respect/exceed rates, and continuous range ratios |
| 2025-12-02 | [Price will break this key level 98% of the time before 10:30AM on ES](https://www.youtube.com/watch?v=O-G2j2D7vvM) | ORB timing conditioned on days that eventually had a single break |
| 2025-11-27 | [Pinpoint breakouts to the hour using the initial balance breakout-by-time report](https://www.youtube.com/watch?v=Y58EDr8gFow) | Time distribution for eventual single- and double-break days |

### 1. A normal frequency table: NQ 2–3 p.m. initial balance

At approximately [05:05](https://www.youtube.com/watch?v=6HYJD3SEcLk&t=305s), the visible report uses a custom 2–4 p.m. session, with the 2–3 p.m. range as its initial balance. Over 124 sessions in the selected six-month window it shows:

- 103 single-break sessions: 83.06%;
- 12 double-break sessions: 9.68%;
- 9 no-break sessions: 7.26%.

This is a transparent multinomial frequency table. A Wilson 95% interval around 103/124 is approximately **75.5%–88.6%**, which is more honest than treating 83.06% as a stable constant. Later, a roughly 70% figure refers to price touching a particular negative range extension. That is a level-touch frequency, not a 70% profitable-trade rate.

There is also a subtle live-use gap. Once one boundary has broken, the trader really wants an as-of question such as:

> Among sessions identical on information available at this minute, after the first boundary has broken in this direction and at this elapsed time, how often does the opposite boundary break before the session ends?

The unconditional session share of “single-break days” is not automatically the answer to that risk-set question.

### 2. Eventual-outcome conditioning: ORB and IB by time

At approximately [03:47](https://www.youtube.com/watch?v=O-G2j2D7vvM&t=227s), the visible ORB report is set to YM and shows 62 of 65 eventual single-break days breaking before 10:30, or 95.38%. The video's title names ES and 98%, demonstrating why a claim must retain the symbol, lookback, filters, and live selector state rather than borrowing a number from the title.

The denominator is the larger issue: the 65 observations are days already known, after the close, to have become single-break days. Thus the report estimates:

\[
P(\text{first break before 10:30}\mid\text{day eventually classified single-break})
\]

It does not estimate:

\[
P(\text{a break before 10:30}\mid\text{all information available at the open})
\]

Similarly, the [IB-by-time demonstration](https://www.youtube.com/watch?v=Y58EDr8gFow&t=112s) says that about 82% of eventual single-break days broke their first side before 12:30, while roughly two-thirds of eventual double-break days completed the other side after 12:30. These are valid descriptions of historical timing. They become look-ahead-biased if the eventual day type is silently treated as known during the live session.

The same warning applies to any “by retracement,” “by spike,” or subtype report whose public definition excludes days that later failed to complete the defining outcome. The historical description is not wrong; the live interpretation must use an as-of denominator.

### 3. Several marginal rates are not a joint probability

The four-report NQ video shows approximately:

- 47/71 = 66% green closes after the prior-day high was broken;
- 74% first-high breaks when the initial-balance low formed first;
- 52/69 = 75.36% green sessions after a green first 60-minute candle;
- 120/126 = 95.24% of sessions with at least one initial-balance boundary break, derived from 100 single breaks plus 20 double breaks.

These are separate historical rates with overlapping dates, features, and outcomes. The video uses them as narrative confluence but does not show the intersection cohort where all four predicates were true simultaneously. Therefore it does not establish a combined probability. Averaging, multiplying, or voting these percentages would falsely assume independence and compatible denominators.

The correct question is row-level:

\[
P(Y\mid X_1 \cap X_2 \cap X_3 \cap X_4)
\]

That requires joining the event rows by session date, applying only features known by the decision timestamp, reporting the remaining sample size, and comparing the result with each simpler nested model. Edgeful's AI video and its [YM initial-balance case study](https://www.edgeful.com/blog/posts/ym-initial-balance-strategy) show that date-level joins are possible. The public YM example reports 37/38 = 97.4% among days that broke, versus 37/39 = 94.9% among all eligible rows; it also surfaces an exploratory 19/19 subgroup. Their approximate Wilson 95% intervals are **86.5%–99.5%**, **83.1%–98.6%**, and **83.2%–100%**, respectively. Even perfect 19/19 is still a small, selected historical cell.

### 4. AI is a query surface, not the statistical authority

At approximately [08:27](https://www.youtube.com/watch?v=eebhWxnEbHA&t=507s), the AI demonstration joins Tuesday double-break observations with attributes from other reports. A later slice is only 2 of 12 observations, with an approximate Wilson 95% interval of **4.7%–44.8%**. The video also shows the model being asked to find commonalities and suggests it can lose conversational context after a UI action.

The durable mechanism is not the language model. It is the row-level, date-aligned event data. AI can translate a question into a constrained query and summarize returned receipts. It should not invent event definitions, choose an unlogged favorable slice, calculate outside the validated reducer, or promote an exploratory pattern as evidence.

### 5. Point-in-time safety can be designed correctly

The ADR video explicitly calculates the current benchmark from completed prior days and excludes the still-forming current day. That is the correct point-in-time pattern: features used for a decision must be computed only from data available then.

The screen segment verified in that video is YM over six months, showing 54/131 days exceeding a five-day ADR and 77/131 respecting it. Another ADR output is a continuous comparison such as average realized range as a percentage of ADR. “92% of ADR” means a magnitude ratio, not a 92% probability. As with the ORB example, the visible YM selector differs from the ES/70 framing in the title; the cohort belongs in the claim.

### 6. The selector itself is part of the experiment

The report-guide video shows a selectable lookback from short windows through five years/custom dates and, in one visible gap example, NQ gap-up fills of 45/78 = 58% and gap-down fills of 30/50 = 60%. Edgeful's current [API FAQ](https://help.edgeful.com/en/articles/15808219-the-edgeful-api-faq) describes plan-dependent access from six months to eight years of row-level history. Many demonstrations use six months. Historical depth is therefore report-, market-, and access-dependent, not one universal “years of proof” value.

A separate inside-bar demonstration shows a Tuesday slice of 13/15 = 87% next to 68/79 = 86% for a broader cohort. Their wide, overlapping Wilson intervals—approximately **62.1%–96.3%** and **76.8%–92.0%**—show why a higher displayed percentage in a thin slice may add no reliable information.

## What a percentage can and cannot support

| Displayed result | Defensible interpretation | Unsupported leap |
|---|---|---|
| 103/124 single-break sessions | 83.1% of the declared historical sessions finished in that class | The next trade wins with 83.1% probability |
| 62/65 before 10:30 among single-break days | Timing distribution conditional on the eventual day class | At the open, there is a 95.4% chance of a break before 10:30 |
| 52/69 green after a green opening candle | Conditional close-direction frequency in that sample | A 75.4% profitable long strategy without entry, stop, exit, and costs |
| Average Monday range is 92% of ADR | Mean/median magnitude relative to a benchmark, depending on the report definition | 92% of Mondays respect ADR |
| Four cards show 66%, 74%, 75%, 95% | Four marginal historical summaries | A combined 77.5% average, a product, or four independent confirmations |
| An AI finds 19/19 | A discovered, thin historical subgroup | A forward 100% law |

Occurrence frequency is only one ingredient of trading edge. Economic usefulness additionally requires a point-in-time entry rule, exit/stop rule, slippage and fees, adverse/favorable excursion, payoff distribution, and capacity. A 70% target-touch rate can still lose money; a 40% event can be valuable with favorable payoff asymmetry.

## How to replicate the useful layer honestly

### 1. Freeze the question before counting

Each statistic begins with a versioned specification containing:

- instrument and continuous-contract/roll rule;
- venue, source, bar type, time zone, session, and holiday calendar;
- event formula and equality/tie handling;
- first occurrence versus all occurrences;
- features and the timestamp when each becomes knowable;
- outcome, horizon, and success/failure/unresolved policy;
- allowed subgroup dimensions and bucket boundaries;
- lookback, validation partition, and minimum sample policy.

Changing any one produces a new version, not an in-place refresh of the old claim.

### 2. Build one point-in-time event ledger

The detector should emit one auditable row per independent eligible session or event, including the raw source hashes. Do not pre-aggregate away the dates. Row-level data is necessary for deduplication, joins, leakage audits, clustered uncertainty, regime analysis, and reproducing every card.

For intraday use, every row needs both `observed_at` and `outcome_available_at`. A live query may use only fields whose availability timestamp is no later than the query's `as_of` timestamp.

### 3. Make the denominator explicit

Use all opportunities actually eligible at the decision time. Keep `success`, `failure`, `unresolved/censored`, and `excluded-data-quality` counts separate. If a report intentionally conditions on an eventual class—useful for retrospective path analysis—label it `descriptive_posthoc` and block it from forecast language.

For “what usually happens from this moment?” use a risk set: historical events that had reached the same observable state by the same elapsed time, whether or not they later completed the desired pattern.

### 4. Report uncertainty and the independent sample size

For a binary result, return `k`, `n`, `k/n`, and an interval such as the Wilson score interval documented by [NIST](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm). For multinomial results, return every class count. For magnitude and time-to-event, return median, quantiles, dispersion, and censored observations rather than only an average.

Multiple events on one session are not necessarily independent. Neither are overlapping forward-return windows. The independent unit should normally be the session or non-overlapping episode; use session clustering, a block bootstrap, or an autocorrelation-consistent estimator such as [Newey–West](https://doi.org/10.2307/1913610) where appropriate. Display both raw event count and effective/independent count.

### 5. Compare with a baseline and simpler nested cohorts

Every conditional rate should show:

- unconditional/base rate;
- conditional rate;
- absolute and relative lift;
- sample loss caused by the condition;
- a simpler model using fewer conditions.

If Tuesday inside bars produce 87% while all inside bars produce 86%, the useful finding may be “no demonstrated incremental Tuesday effect,” especially with only 15 Tuesday observations.

### 6. Keep discovery away from proof

Trying many concepts, symbols, weekdays, thresholds, sessions, and AI-generated combinations creates a large hidden trial family. The maximum discovered rate is biased upward even when every calculation is mechanically correct. Log every tested query, freeze the family, and use an appropriate family-wise/FDR method or a data-snooping procedure such as [White's Reality Check](https://doi.org/10.1111/1468-0262.00152). The [Probability of Backtest Overfitting](https://ssrn.com/abstract=2326253) is a useful portfolio-selection framing.

Use chronological partitions:

1. discovery/training;
2. calibration or model selection;
3. untouched out-of-sample holdout;
4. forward/live shadow observations.

Edgeful documents a chronological holdout for its separate [algo optimizer](https://help.edgeful.com/en/articles/15254090-understanding-holdout-in-sample-and-out-of-sample-in-the-algo-optimizer). I found no public evidence establishing that every standard report card is itself a holdout estimate. That optimizer feature should not be imputed to the report library.

### 7. Measure stability and calibration, not only the all-history rate

A market relationship can drift. Return fixed, predeclared rolling windows and subperiod tables rather than selecting whichever lookback currently looks best. Monitor rate, interval, count, and lift by period and regime. Freeze any recency weighting before viewing outcomes.

To call a number a forecast probability, store each probability issued before the outcome, then compare forecast buckets with realized frequencies. Use reliability tables/curves and a proper score such as the [Brier score](https://journals.ametsoc.org/view/journals/mwre/78/1/1520-0493_1950_078_0001_vofeit_2_0_co_2.xml). If recalibration is needed, fit it only on training/calibration data and re-test on untouched observations; [Niculescu-Mizil and Caruana](https://icml.cc/Conferences/2005/proceedings/papers/079_GoodProbabilities_NiculescuMizilCaruana.pdf) provide the standard calibration framing.

### 8. Fail closed at the current chart

For a present-time question, compute a context vector using only currently known data, map it to a preregistered cohort, and return the exact count and uncertainty. If the cell is thin, drifting, not decision-time-safe, or found only through exploratory slicing, return `insufficient_evidence` or `descriptive_only` rather than a confident percentage.

## Mapping to this repository's governed concept work

The closest fit is an enrichment layer, not a replacement for the concept or hypothesis library:

```text
frozen concept definition
        ↓
point-in-time event detector
        ↓
dated event ledger
        ↓
conditional statistics panels
        ↓
holdout / walk-forward / forward evidence state
        ↓
human-readable report or as-of lookup
```

The local [indicator-confluence research note](indicator-confluence-primary-sources-2026-07-30.md) already requires frozen universe, asset class, timeframe/session, closed-bar semantics, separate in-sample/out-of-sample results, signal count, forward returns, drawdown/MAE, and costs. The [adversarial confluence review](confluence-automation-adversarial-review-2026-07-30.md) adds point-in-time-safe higher-timeframe inputs, source hashes, trial-family control, dependence from nested timeframes and overlapping horizons, instrument/feed/session/roll identity, and simpler baselines. The [strategy-claim audit checklist](../docs/strategy-claim-audit-checklist.html) requires preregistration, receipts, a family lockbox, burned-data tracking, and forward evidence before promotion.

Those surfaces are stricter than what can be established from Edgeful's public report UI. They should remain the authority. The transferable idea is to attach **empirical behavior panels** to each already-governed concept:

- unconditional prevalence;
- outcome distribution;
- context-conditioned prevalence and lift;
- time-to-event and path shape;
- MAE/MFE and costed payoff when a strategy rule exists;
- stability, calibration, and evidence status.

TraderCockpit's [market-analysis doctrine](../MARKET-ANALYSIS-DOCTRINE.md) is a separate public reporting lane: pre-release information must be point-in-time safe, numerical claims need receipts, and scenarios are not predictions. An experimental concept percentage should not enter public market commentary as forecast authority until it passes the governed evidence lifecycle.

Because Futures and Register were explicitly out of scope, this report makes no claim about their current schema or integration points. The mapping above is conceptual and limited to repository surfaces inspected here.

## Limitations of this investigation

- Public videos and first-party pages expose report definitions, selectors, sample counts, and examples, but not a complete reproducible dataset.
- No paid API, credentials, source data, private methodology, or current account was accessed.
- Video captions can mis-transcribe numbers; key examples above were cross-checked against visible cards where possible.
- A title can describe a different ticker/filter cut than the visible segment. The note therefore treats the on-screen selectors as the evidence for that segment.
- Edgeful's exact vendors, corrections, futures roll/back-adjustment, missing-bar rules, exchange calendar treatment, stock corporate-action treatment, universe/delisting policy, and full scoring formula are not publicly established by the sources reviewed.
- Public documentation does not establish confidence-interval methodology, cluster correction, multiple-testing correction, calibration, or holdout status for every standard report.
- This is a design analysis, not a validation of any Edgeful percentage or a recommendation to trade it.

## Minimal replication architecture

Ponytail principle: do not begin with a dashboard, chatbot, new service mesh, or new database. Reuse the existing governed concept specifications and market-data authority, then add the smallest deterministic path:

1. **Concept spec:** one versioned file declaring eligibility, event, as-of features, outcomes, subgroup family, and validation partitions.
2. **Detector:** one deterministic batch function that reads point-in-time normalized bars and emits event rows.
3. **Event ledger:** appendable Parquet/JSON/table rows keyed by concept version, instrument, session date, and event ID, with timestamps and source hashes.
4. **Reducer:** one tested grouping function producing counts, rates/distributions, intervals, baseline lift, effective sample size, and stability slices.
5. **Validation ledger:** discovery/holdout/forward role, tested-query family, multiple-testing method, walk-forward window, leakage result, and promotion state.
6. **As-of lookup:** a thin report that can only query preregistered dimensions and returns receipts or `insufficient_evidence`. AI, if added later, only compiles natural language to this constrained query.

One concept and one report family should prove the end-to-end contract before generalization. Initial-balance single/double/no-break is a good test case because it is multinomial, path-dependent, session-sensitive, and exposes the eventual-class denominator trap.

## Proposed artifact contract

```json
{
  "schema": "conditional-market-stat/v1",
  "stat_id": "nq-ny-ib60-first-break-direction/v1",
  "concept_id": "initial_balance_60m",
  "concept_version": "sha256:<spec-hash>",
  "question": "After an upside first break known by 11:00 ET, does the opposite boundary break by session close?",
  "as_of": "2025-12-30T11:00:00-05:00",
  "eligibility": {
    "instrument": "NQ",
    "contract_rule": "<versioned-rule>",
    "session": "09:30-16:00 America/New_York",
    "event_rule": "<versioned-expression>",
    "known_by": "first_break_timestamp"
  },
  "cohort": {
    "filters": {"first_break_direction": "up", "elapsed_bucket": "<=11:00"},
    "start": "2021-01-01",
    "end": "2025-12-31",
    "n_sessions": 0,
    "n_events_raw": 0,
    "n_independent": null,
    "unresolved": 0,
    "exclusions": []
  },
  "outcome": {
    "definition": "opposite_boundary_touched_by_session_close",
    "success_count": 0,
    "failure_count": 0
  },
  "estimate": {
    "rate": null,
    "ci_method": "wilson-95",
    "lower": null,
    "upper": null,
    "baseline_rate": null,
    "absolute_lift": null
  },
  "validation": {
    "role": "discovery",
    "decision_time_safe": false,
    "family_id": "ib60-v1",
    "trials_seen": 0,
    "multiple_test_method": null,
    "walk_forward_window": null,
    "leakage_check": "pending",
    "state": "descriptive_only"
  },
  "economics": {
    "entry_rule": null,
    "exit_rule": null,
    "cost_model": null,
    "expectancy": null
  },
  "provenance": {
    "source_ids": [],
    "source_hashes": [],
    "code_commit": "<commit>",
    "generated_at": "<timestamp>"
  }
}
```

In the Futures implementation target, every validation window in an artifact like this must respect the standing data ceiling (`packages/esq/governance/data_ceiling.py`; holdout ceiling 2025-12-31) — the example dates above are chosen inside it deliberately.

`null` means unknown or not measured; it must never be silently converted to zero. Continuous reports should replace binary success/failure with declared units and distribution quantiles. A promoted probability must be `decision_time_safe`, based on a frozen family, and carry holdout or forward evidence; otherwise it remains descriptive.

## Compact evidence-versus-inference ledger

| Status | Finding |
|---|---|
| **Observed** | Edgeful report demonstrations calculate empirical rates from historical occurrences under selectable ticker, session, date range, and report-specific filters, and they usually show raw counts/sample size. |
| **Observed** | Reports include binary, multinomial, timing, magnitude, and path-dependent outcomes; a displayed percentage is not always a probability of profit. |
| **Observed** | Some timing/retracement/subtype reports condition on an eventual end-of-session class, which is useful descriptively but unsafe as an ex-ante denominator unless rebuilt as an as-of risk set. |
| **Observed** | Edgeful can expose/join date-level rows, and its AI feature queries those joined rows; thin exploratory cells occur in public examples. |
| **Observed** | The four-report confluence example presents separate marginal rates and does not publicly calculate the joint intersection probability. |
| **Observed** | Current first-party documentation describes plan-dependent historical depth and row-level access; many demonstrations use a six-month slice. |
| **Not publicly established** | Exact data vendors, corrections, futures roll construction, corporate-action/universe policy, missing-data rules, confidence intervals, dependence adjustments, standard-report holdout status, multiple-testing controls, calibration, and the discovery-score formula. |
| **Inference** | The reproducible core is a concept detector plus dated event ledger plus conditional reducer; AI and visualization are optional interfaces. |
| **Recommendation** | Add versioned behavior dossiers to the governed concept library, preserve the repository's stricter preregistration/holdout/forward gates, and return `insufficient_evidence` rather than a percentage when the as-of cohort is thin, selected, drifting, or leaked. |
