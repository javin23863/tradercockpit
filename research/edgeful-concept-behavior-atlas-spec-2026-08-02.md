# Concept Behavior Atlas v1 specification

**Date:** 2026-08-02
**Status:** Proposed normative contract for Claude Code review
**Related plan:** [Implementation plan](edgeful-concept-behavior-atlas-plan-2026-08-02.md)
**Evidence basis:** [Edgeful conditional market-statistics report](edgeful-conditional-market-statistics-2026-08-02.md)

## 1. Purpose

This specification defines the minimum interface and evidence contracts for attaching reproducible conditional behavior statistics to governed market concepts.

It answers:

> Among all historically eligible observations matching a frozen concept and point-in-time context, what outcomes occurred, with what uncertainty, stability, evidence state, and provenance?

The specification does not define a trading strategy, data vendor, chart interface, AI model, or repository-specific path. Those are separate decisions governed by the implementation target's current authority.

The words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

## 2. Terms

- **Concept:** A versioned deterministic definition of a market event or state.
- **Eligible observation:** A session or event that satisfies the frozen universe and data-quality rules before its outcome is considered.
- **Decision timestamp:** The time at which the question is asserted to be answerable live.
- **Known-at timestamp:** The earliest time a feature value is available to the decision process.
- **Outcome-available timestamp:** The earliest time the complete outcome label is available.
- **Context:** Preregistered feature predicates applied to eligible observations using only values known at the decision timestamp.
- **Cohort:** The exact set of independent eligible event identifiers remaining after scope, context, and evidence-partition filters.
- **Observed conditional rate:** `success_count / eligible_resolved_count` under the declared denominator policy.
- **Post-hoc subtype:** A class knowable only after the outcome horizon, such as an eventual single-break day.
- **Trial family:** Every concept, market, threshold, bucket, horizon, and filter combination examined during one discovery campaign.
- **Evidence state:** A machine-readable assessment of what interpretation the result supports.
- **Module:** The `ConceptBehaviorAtlas` implementation behind the interface in section 4.

## 3. Invariants

1. An event definition MUST be frozen and hash-addressed before outcomes are counted.
2. A decision-time query MUST NOT use a feature whose `known_at` is later than the query's decision timestamp.
3. Eligibility MUST be determined without inspecting the requested outcome.
4. Success, failure, unresolved/censored, and data-quality exclusion MUST remain distinguishable.
5. Every reported cohort MUST be reconstructable from stable dated event identifiers or a hash-addressed event-set receipt.
6. A percentage MUST travel with `k`, `n`, denominator policy, uncertainty, market scope, lookback, context, and evidence state.
7. Separate marginal statistics MUST NOT be combined by averaging, multiplication, voting, or narrative confluence.
8. A joint statistic MUST be calculated from the row-level intersection of the exact predicates.
9. Same-sample discovery MUST NOT receive out-of-sample or calibrated status.
10. Event frequency MUST NOT imply strategy profitability when entry, exit, costs, and execution are undefined.
11. Unknown or unmeasured values MUST be `null`, never fabricated or silently converted to zero.
12. Definition changes MUST create a new concept/report version and invalidate inherited evidence status.

## 4. Module and interface

The implementation MUST expose one deep `ConceptBehaviorAtlas` module. Its external interface contains only:

```text
materialize(spec_ref, data_ref) -> LedgerReceipt | AtlasError
evaluate(BehaviorQuery) -> BehaviorReport | AtlasError
```

### 4.1 `materialize`

`materialize` MUST:

- resolve a governed concept version and declared data authority;
- detect eligible events with point-in-time semantics;
- attach context and later outcome labels;
- write or return a hash-addressed event ledger through existing repository storage;
- return counts, date range, input hashes, output hash, code commit, exclusions, and validation results.

It MUST be deterministic for identical specifications, inputs, and implementation versions.

### 4.2 `evaluate`

`evaluate` MUST:

- validate the query against the concept and ledger versions;
- reject unavailable, unregistered, future-known, or disallowed predicates;
- construct the exact independent cohort;
- calculate the declared statistic and uncertainty;
- compare with the declared baseline;
- attach stability, trial-family, evidence-state, and provenance receipts;
- return a typed refusal rather than an unsupported number.

### 4.3 Dependencies and seams

The module SHOULD reuse existing concept-registry, market-data, calendar/session, contract-roll, artifact, and validation implementations.

A new external seam or adapter MUST NOT be introduced unless:

- the current repository has an established seam at that location; or
- two real adapters are needed, normally production and a test stand-in.

Storage format is an implementation detail as long as all normative fields and reconstruction requirements survive. A new database is not required by this specification.

## 5. Concept behavior specification

Before materialization, the implementation MUST resolve a versioned specification equivalent to:

```json
{
  "schema": "concept-behavior-spec/v1",
  "spec_id": "<stable-id>",
  "concept_ref": {
    "concept_id": "<governed-id>",
    "concept_version": "sha256:<definition-hash>"
  },
  "market_scope": {
    "instrument": "<instrument>",
    "venue": "<venue-or-null>",
    "bar_type": "time",
    "timeframe": "<timeframe>",
    "timezone": "<iana-timezone>",
    "session_id": "<versioned-session>",
    "calendar_id": "<versioned-calendar>",
    "contract_rule_id": "<versioned-roll-rule-or-null>"
  },
  "eligibility": {
    "unit": "session",
    "first_or_all": "first_per_session",
    "dedupe_rule": "<deterministic-rule>",
    "tie_rule": "<deterministic-rule>",
    "equality_rule": "touch_inclusive",
    "missing_data_rule": "exclude_with_reason"
  },
  "decision": {
    "timestamp_rule": "<rule>",
    "allowed_context_family": ["<feature-ref>"],
    "bucket_definitions": {"<feature-ref>": ["<frozen-edges>"]}
  },
  "outcome": {
    "outcome_id": "<versioned-outcome>",
    "type": "binary",
    "horizon_rule": "<rule>",
    "unresolved_rule": "censored",
    "outcome_available_rule": "<rule>"
  },
  "validation": {
    "discovery_window": ["<start>", "<end>"],
    "calibration_window": null,
    "holdout_window": ["<start>", "<end>"],
    "forward_start": null,
    "trial_family_id": "<family-id>",
    "minimum_policy": "interval-and-stability-gated"
  }
}
```

All identifiers and rules MUST resolve to immutable content or a content hash. Human prose alone is insufficient authority for executable semantics.

## 6. Event ledger contract

The ledger MUST preserve one row per raw detected event plus the fields necessary to identify the independent unit.

Required fields:

```json
{
  "schema": "concept-event/v1",
  "event_id": "<stable-id>",
  "independent_unit_id": "<normally-session-id>",
  "concept_id": "<governed-id>",
  "concept_version": "sha256:<definition-hash>",
  "instrument": "<instrument>",
  "contract": "<actual-contract-or-null>",
  "session_id": "<versioned-session>",
  "session_date": "YYYY-MM-DD",
  "observed_at": "<rfc3339>",
  "decision_at": "<rfc3339>",
  "features": {
    "<feature-id>": {
      "value": "<typed-value>",
      "known_at": "<rfc3339>",
      "definition_version": "sha256:<hash>"
    }
  },
  "outcome": {
    "outcome_id": "<versioned-outcome>",
    "value": "<typed-value-or-null>",
    "state": "success|failure|unresolved|censored|excluded",
    "available_at": "<rfc3339-or-null>",
    "exclusion_reason": null
  },
  "provenance": {
    "source_ids": ["<source-id>"],
    "source_hashes": ["sha256:<hash>"],
    "calendar_version": "<version>",
    "session_version": "<version>",
    "contract_rule_version": "<version-or-null>",
    "code_commit": "<commit>"
  }
}
```

### 6.1 Identifier requirements

`event_id` MUST be stable across deterministic rebuilds. It SHOULD derive from immutable concept version, instrument/contract identity, independent unit, observed timestamp, and occurrence ordinal.

`independent_unit_id` MUST represent the unit used for uncertainty. Multiple raw events may share one independent unit, but the report MUST disclose both raw and independent counts.

### 6.2 Exclusions

Data-quality exclusions MUST retain a row or separate exclusion receipt containing the candidate unit and reason. Dropping a unit silently is prohibited.

Permitted reason codes SHOULD include:

- `missing_bars`
- `incomplete_session`
- `ambiguous_contract`
- `calendar_conflict`
- `duplicate_source`
- `definition_unresolvable`
- `outcome_unavailable`

## 7. Query contract

```json
{
  "schema": "concept-behavior-query/v1",
  "query_id": "<stable-id>",
  "spec_ref": "<spec-id-and-hash>",
  "ledger_ref": "sha256:<ledger-hash>",
  "decision_at": "<rfc3339-or-null-for-retrospective>",
  "context": [
    {"feature_ref": "<registered-feature>", "operator": "eq", "value": "<typed-value>"}
  ],
  "outcome_ref": "<versioned-outcome>",
  "denominator_policy": "all_eligible_resolved",
  "evidence_partition": "discovery|calibration|holdout|forward|all_descriptive",
  "baseline_query_ref": "<query-id-or-inline-base-cohort>",
  "requested_statistics": ["rate", "wilson_95", "absolute_lift", "relative_lift"]
}
```

The context operators and dimensions MUST be preregistered in the behavior specification. Ad hoc expressions are prohibited in a query claiming holdout or calibrated evidence.

## 8. Point-in-time rules

For every selected event and context feature:

```text
feature.known_at <= query.decision_at
```

If this cannot be proven, `evaluate` MUST return `future_known_feature` and no forecast-capable rate.

A report MAY intentionally condition on a post-hoc subtype for retrospective path research. Such a query MUST:

- set `decision_time_safe` to `false`;
- set evidence state to `descriptive_posthoc`;
- identify the future-known predicate;
- prohibit forecast wording.

For “what happens from this moment?” the eligible cohort MUST be a risk set of historical observations that had reached the same observable unresolved state by the same elapsed-time rule. It MUST include later successes, later failures, and censored observations under the declared policy.

## 9. Denominator rules

The default binary denominator is:

```text
eligible_resolved_n = success_n + failure_n
observed_rate = success_n / eligible_resolved_n
```

Unresolved/censored and excluded counts MUST be displayed separately. A query MUST NOT drop them without declaring its censoring policy.

If a report conditions on eventual completion, the denominator label MUST state that explicitly, for example:

```text
eventual_single_break_sessions_n
```

It MUST NOT be shortened to a generic `sample_size` when used in human output.

For categorical outcomes, all mutually exclusive class counts and the total MUST be returned. A derived class such as “at least one break” MUST include its exact class expression, such as `single_break + double_break`.

## 10. Outcome families

### 10.1 Binary

Examples: filled/not filled, green/red close, target before horizon.

Return `success_n`, `failure_n`, unresolved/censored counts, rate, and uncertainty.

### 10.2 Categorical

Examples: high-only, low-only, both-side, no-break.

Return every class count and rate. Categories MUST be mutually exclusive and exhaustive under the declared unresolved policy.

### 10.3 Magnitude

Examples: extension, retracement, MAE, MFE, realized range divided by ADR.

Return units, `n`, median, declared quantiles, dispersion, and censoring. A magnitude percentage MUST NOT be labeled a probability.

### 10.4 Timing

Examples: time to first break or fill.

Return time origin, horizon, event count, censor count, and distribution/survival summary. Conditioning on an eventual subtype MUST be marked post-hoc unless that subtype was known at decision time.

### 10.5 Path-dependent

Examples: low formed first then high broke first; first break followed by opposite-side break.

Return the exact state sequence, state timestamps, and tie policy. No path state may be treated as known before its timestamp.

## 11. Statistics

### 11.1 Binary proportion

For the pilot, use the two-sided 95% Wilson interval with:

```text
z = 1.959963984540054
p = k / n
denom = 1 + z^2 / n
center = (p + z^2 / (2n)) / denom
half = z * sqrt(p(1-p)/n + z^2/(4n^2)) / denom
lower = max(0, center - half)
upper = min(1, center + half)
```

When `n = 0`, rate and interval MUST be `null` and evidence state MUST be `insufficient_evidence`.

The interval is descriptive uncertainty, not protection against selection bias, dependence, regime drift, or data leakage.

### 11.2 Baseline and lift

Every conditional query MUST identify a simpler baseline cohort and return:

```text
absolute_lift = conditional_rate - baseline_rate
relative_lift = conditional_rate / baseline_rate - 1
sample_retention = conditional_n / baseline_n
```

Division by zero MUST return `null` with a reason.

### 11.3 Dependence

The report MUST expose:

- `raw_event_n`;
- `independent_n`;
- independent-unit rule;
- dependence adjustment, if any.

The pilot SHOULD use one observation per session where that matches the concept. If overlapping horizons or repeated intraday events remain, the specification MUST declare a session-cluster, block-bootstrap, or other approved method before promotion.

### 11.4 Multiple testing

Every discovery query MUST be logged under a `trial_family_id`. The ledger MUST include rejected and unfavorable queries.

The report MUST expose:

- total trials considered;
- selection rule;
- correction or data-snooping method;
- whether the current query was selected after viewing its outcomes.

An exploratory maximum MUST NOT inherit an unadjusted confidence claim.

## 12. Report contract

```json
{
  "schema": "concept-behavior-report/v1",
  "report_id": "<stable-id>",
  "query": {
    "query_id": "<query-id>",
    "spec_ref": "<spec-id-and-hash>",
    "ledger_ref": "sha256:<ledger-hash>",
    "decision_at": "<rfc3339-or-null>",
    "context": [],
    "outcome_ref": "<versioned-outcome>",
    "denominator_policy": "all_eligible_resolved",
    "evidence_partition": "holdout"
  },
  "cohort": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD",
    "eligible_n": 0,
    "success_n": 0,
    "failure_n": 0,
    "unresolved_n": 0,
    "excluded_n": 0,
    "raw_event_n": 0,
    "independent_n": 0,
    "independent_unit": "session",
    "event_set_hash": "sha256:<hash>"
  },
  "estimate": {
    "rate": null,
    "interval_method": "wilson-95",
    "lower": null,
    "upper": null,
    "baseline_rate": null,
    "absolute_lift": null,
    "relative_lift": null,
    "sample_retention": null
  },
  "validation": {
    "decision_time_safe": false,
    "leakage_status": "pending",
    "evidence_state": "descriptive",
    "trial_family_id": "<family-id>",
    "trials_considered": 0,
    "selection_timing": "predeclared|post_selected",
    "multiple_test_method": null,
    "stability_status": "unknown",
    "calibration_status": "not_applicable"
  },
  "economics": {
    "entry_rule": null,
    "exit_rule": null,
    "cost_model": null,
    "expectancy": null
  },
  "provenance": {
    "concept_hash": "sha256:<hash>",
    "data_hashes": [],
    "session_hash": "sha256:<hash>",
    "calendar_hash": "sha256:<hash>",
    "contract_rule_hash": null,
    "code_commit": "<commit>",
    "generated_at": "<rfc3339>"
  }
}
```

Reports MAY add outcome-family-specific fields but MUST NOT remove or reinterpret the common fields.

## 13. Evidence states

Allowed primary states:

| State | Meaning |
|---|---|
| `descriptive` | Reproducible historical description; no forecast claim |
| `descriptive_posthoc` | Valid retrospective subtype analysis using future-known information |
| `exploratory` | Point-in-time-safe discovery result not yet proven on frozen holdout |
| `oos_verified` | Frozen query evaluated successfully on untouched chronological holdout |
| `calibrated` | Pre-outcome issued probabilities pass declared forward calibration and drift gates |
| `insufficient_evidence` | Count, interval, stability, or provenance gate is inadequate |
| `leaked` | Future-known information entered a decision-time cohort |
| `drifted` | Predeclared stability threshold failed |
| `data_invalid` | Data/session/contract/provenance validation failed |
| `definition_conflict` | Required authority is missing or contradictory |

Promotion MUST be explicit and receipt-backed. A report MAY be demoted automatically when a fail-closed condition occurs but MUST NOT be promoted automatically.

## 14. Calibration and drift

To claim a forecast probability, the system MUST store each issued probability before the outcome is known, including query and ledger hashes.

Forward evaluation MUST include:

- reliability bins with forecast count and realized rate;
- Brier score;
- declared minimum observations or uncertainty rule per bin;
- rolling count, rate, interval, baseline lift, and score;
- a predeclared drift/demotion rule.

A calibrator, if used, MUST be fit on a calibration partition disjoint from the evaluation holdout or forward period.

## 15. Human-readable output

A rendered card MUST state:

```text
Concept and version
Market, session, timeframe, and date window
Decision timestamp rule
Exact context
Exact outcome and horizon
k / n and denominator label
Observed rate and interval
Baseline, lift, and sample retention
Discovery/holdout/forward role
Evidence state and leakage verdict
Event-set and provenance receipt
Economics status
```

The preferred phrase is **observed conditional hit rate**, not **actual probability**, until calibrated status is earned.

Examples of prohibited wording:

- “This trade has a 95% chance of winning” when only event frequency was measured.
- “Four confirmations equal a 77% probability” when four marginal rates were shown.
- “Price breaks by 10:30 95% of the time” when the denominator is eventual single-break days.
- “100% setup” for a selected 19/19 subgroup.

## 16. Cross-concept composition

For conditions `X1...Xm`, a joint report MUST use:

```text
cohort = eligible_event_ids(X1) intersect ... intersect eligible_event_ids(Xm)
```

All predicates MUST share compatible instrument, session, independent unit, decision timestamp, and outcome horizon. Incompatible joins MUST return a typed error.

The report MUST include nested comparisons:

- baseline;
- each simpler preregistered condition;
- final intersection;
- sample retention at every step.

## 17. Typed errors

At minimum:

- `unknown_concept`
- `concept_version_mismatch`
- `unknown_feature`
- `future_known_feature`
- `disallowed_context_dimension`
- `incompatible_event_units`
- `incompatible_sessions`
- `incompatible_horizons`
- `ledger_version_mismatch`
- `event_set_unreconstructable`
- `data_provenance_missing`
- `zero_eligible_observations`
- `insufficient_independent_observations`
- `holdout_already_burned`
- `definition_conflict`

Errors MUST include the failed invariant and remediation needed. They MUST NOT silently fall back to a broader cohort.

## 18. Minimum runnable checks

The pilot implementation MUST leave one compact acceptance suite at the module interface covering:

1. deterministic materialization and stable event IDs;
2. literal success/failure/unresolved counts;
3. Wilson interval parity for normal, small, zero-success, and all-success cells;
4. rejection of a future-known feature;
5. post-hoc subtype downgrade;
6. session deduplication and raw-versus-independent counts;
7. exact joint intersection rather than marginal combination;
8. baseline/lift/sample-retention parity;
9. zero/thin cohort typed refusal;
10. event-set hash reconstruction;
11. holdout-family lock and burned-holdout prevention;
12. unknown values preserved as `null`.

Tests MUST cross the same module interface used by callers. They SHOULD NOT assert internal implementation structure.

## 19. Pilot acceptance criteria

The pilot is accepted only when:

- current target-repository authority and reused paths are documented;
- one governed concept and outcome are frozen and hash-addressed;
- a hand-labeled fixture passes;
- every feature and outcome has an availability timestamp;
- the event ledger is deterministic and auditable;
- the report reconstructs numerator and denominator from event IDs;
- uncertainty, baseline, lift, and sample retention are present;
- discovery and untouched chronological holdout are separate;
- all attempted pilot queries are logged;
- leakage and evidence states fail closed;
- rolling stability is reported;
- economics remain null unless a complete costed strategy rule was separately evaluated;
- the operator can inspect the exact artifact and verification receipt.

## 20. Decisions deliberately deferred to target-repository audit

Claude Code MUST identify current authoritative implementations before replacing these placeholders:

- exact concept registry and version-resolution path;
- exact event detector entry point;
- exact normalized market-data adapter;
- exact session/calendar and futures contract-roll authority;
- exact artifact storage and schema-validation mechanism;
- exact trial-family and validation-registry integration;
- exact pilot concept identifier;
- exact discovery/holdout dates;
- interval-width, stability, calibration, and demotion thresholds.

The implementation task MUST stop rather than guess any of these.

## 21. Claude Code review contract

Claude should review the research report, screenshots, plan, and this specification as one packet. It should:

- verify every normative rule against the stated user goal;
- identify look-ahead, denominator, dependence, selection, calibration, or economic-interpretation gaps;
- flag any shallow module, speculative seam, or duplicate authority;
- distinguish a blocker from a recommendation;
- name the exact section for every finding;
- return one of `APPROVE`, `REVISE`, or `BLOCK`;
- avoid implementation until a separate Futures-scoped task is opened.

## 22. References

- [Research report and complete evidence ledger](edgeful-conditional-market-statistics-2026-08-02.md)
- [Implementation plan](edgeful-concept-behavior-atlas-plan-2026-08-02.md)
- [Edgeful report guide](https://www.edgeful.com/blog/posts/edgeful-reports-the-complete-guide)
- [Edgeful subreport definitions](https://help.edgeful.com/en/articles/14198526-subreports)
- [Edgeful YM conditional case study](https://www.edgeful.com/blog/posts/ym-initial-balance-strategy)
- [NIST Wilson interval guidance](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
- [Newey-West dependence adjustment](https://doi.org/10.2307/1913610)
- [White's Reality Check](https://doi.org/10.1111/1468-0262.00152)
- [Probability of Backtest Overfitting](https://ssrn.com/abstract=2326253)
- [Brier score](https://journals.ametsoc.org/view/journals/mwre/78/1/1520-0493_1950_078_0001_vofeit_2_0_co_2.xml)
- [Probability calibration framing](https://icml.cc/Conferences/2005/proceedings/papers/079_GoodProbabilities_NiculescuMizilCaruana.pdf)
