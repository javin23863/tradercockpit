# Concept Behavior Atlas implementation plan

**Date:** 2026-08-02
**Status:** Review-ready design; no implementation authorized by this document
**Origin:** TraderCockpit research task
**Implementation target:** A separately scoped Futures task after current authority, branch, worktree, data, and concept-registry state are reverified
**Primary reviewer:** Claude Code, followed by the operator
**Amended:** 2026-08-02 — R3/R4/R5 from the Claude review (REVISE): rehomed to a dedicated branch off `ops/main`, futures-vault backlink added to Phase 0, board card `validation.concept-behavior-atlas` named as the card-first gate

## Review packet

Review these artifacts together:

1. [Research report](edgeful-conditional-market-statistics-2026-08-02.md) — public evidence, statistical interpretation, limitations, and source ledger.
2. [Normative specification](edgeful-concept-behavior-atlas-spec-2026-08-02.md) — interfaces, invariants, schemas, calculations, states, and acceptance criteria.
3. [Screenshot evidence](evidence/edgeful-conditional-market-statistics/) — nine source frames referenced from the research report, each tied to a public video timestamp and SHA-256 digest.

This packet records requirements and evidence. It does not make TraderCockpit the owner of Futures implementation doctrine, and it does not authorize editing Futures or Register from this checkout.

## Outcome

Add a conditional market-statistics layer to the governed concept library so a caller can ask:

> Given concept X, market scope M, information known at decision time T, context C, and outcome definition Y, how did all eligible historical observations behave?

The returned artifact must answer with reconstructable counts, uncertainty, baseline lift, point-in-time safety, evidence status, and provenance. It must refuse to emit forecast language when the cohort is leaked, thin, selected, drifting, or otherwise unsupported.

## Product boundary

The proposed layer is an evidence module, not a trading signal or strategy optimizer.

```text
governed concept definition
        -> point-in-time detector
        -> dated event ledger
        -> conditional behavior report
        -> hypothesis/backtest/economic validation
        -> optional human or AI query surface
```

The concept library says what an event is. The Concept Behavior Atlas says how occurrences behaved. A backtester determines whether a complete entry/exit/cost rule was economically useful. These responsibilities must remain distinct.

## Goals

- Reuse existing governed concept definitions and current market-data authority.
- Preserve one dated row per independent eligible event or session.
- Support binary, categorical, magnitude, timing, and path-dependent outcomes.
- Answer both retrospective questions and decision-time-safe as-of questions.
- Expose exact numerator, denominator, event identifiers, exclusions, and hashes.
- Show sample uncertainty, baseline rate, lift, stability, and evidence partition.
- Keep exploratory discovery separate from holdout and forward proof.
- Fail closed when a result cannot support the requested interpretation.

## Non-goals

- Rebuilding the concept library.
- Creating a new charting product, dashboard, chatbot, vector database, or service mesh.
- Choosing or installing a new market-data vendor.
- Claiming that an event frequency is a profitable strategy.
- Producing live trading recommendations.
- Generalizing across every concept before one vertical slice passes.
- Mutating Futures, Register, or their vaults from this TraderCockpit task.

## Governing decisions

### One deep module

Create one deep `ConceptBehaviorAtlas` module. Its interface has two operations:

1. `materialize(spec_ref, data_ref) -> ledger_receipt`
2. `evaluate(query) -> behavior_report`

The implementation hides event detection orchestration, availability checks, cohort construction, deduplication, statistics, uncertainty, validation-state rules, and provenance assembly. Callers and tests use the same interface.

Do not introduce a network port, database abstraction, or provider factory unless the target repository already has the relevant seam or two real adapters are required. Use existing adapters and storage first.

### One pilot before library expansion

The first delivery covers:

- one already-governed concept;
- one instrument;
- one timeframe and session;
- one frozen decision timestamp rule;
- one primary outcome and one horizon;
- one base cohort plus a small preregistered context family;
- one chronological holdout;
- one report artifact.

The pilot concept is selected only after the current Futures concept registry and data authority are inspected. Initial balance, inside bar, Donchian breakout, and volatility squeeze are examples, not approved identifiers.

### No AI in the evidence authority

Natural-language querying may be added later. It can only compile a request into the validated query contract and summarize the returned artifact. It cannot invent definitions, calculate statistics independently, select unlogged favorable filters, or promote evidence status.

## Work plan

### Phase 0 — authority and reuse audit

Perform this in a new Futures-scoped task and worktree.

Tasks:

- Reconfirm repository, branch, base, commit, worktree cleanliness, and governing instructions.
- Locate the current concept registry, DSL-ready definitions, hypothesis composition layer, market-data adapters, session calendars, continuous-contract rules, artifact schemas, validation registry, and test conventions.
- Trace one candidate concept from registry definition through every detector caller and existing backtest consumer.
- Identify existing storage capable of retaining dated event rows and hashes.
- Record which requested fields already exist and which are missing.
- Produce a delta-only file plan. Do not redesign working machinery.
- Vault-link this packet from the Futures engineering vault (`repos\futures\docs\vault\`) so the futures plan chain can see it; until that link exists this packet is invisible to the plan of record.

Acceptance:

- Exact source paths and current commits are cited.
- Board card `validation.concept-behavior-atlas` is Active and referenced; no feature code before that (card-first standing rule).
- The candidate concept has unambiguous point-in-time semantics.
- Data/session/roll authority is named, not guessed.
- No dependency or new module is proposed where an existing implementation suffices.

Stop conditions:

- Concept authority conflicts or is incomplete.
- The detector cannot establish when its inputs become known.
- The market-data/session/roll authority is ambiguous.
- The candidate requires a new paid source or credential.

### Phase 1 — freeze the pilot question

Write a versioned pilot specification before counting outcomes.

Declare:

- concept identifier and definition hash;
- instrument and contract/roll identity;
- bar type, timeframe, session, calendar, and time zone;
- eligibility and exclusion rules;
- event equality, tie, duplicate, and first/all occurrence rules;
- each context feature and `known_at` rule;
- primary outcome, horizon, censoring, and `outcome_available_at` rule;
- independent observation unit;
- allowed context dimensions and bucket edges;
- discovery, calibration, holdout, and forward periods — all inside the target repository's data ceiling (holdout ceiling 2025-12-31; `packages/esq/governance/data_ceiling.py` is the authority);
- baseline cohort;
- maximum trial family;
- evidence-state promotion rules.

Acceptance:

- A reviewer can label a raw session without reading implementation code.
- Every field used at decision time is demonstrably available then.
- No condition depends on the eventual outcome class unless marked `descriptive_posthoc`.
- Changing any definition creates a new version.

### Phase 2 — create the smallest golden fixture

Hand-label a compact fixture containing:

- a normal success;
- a normal failure;
- an unresolved/censored event;
- an equality/touch edge case;
- a duplicate or multiple-event session;
- a missing/incomplete-data exclusion;
- a session boundary or daylight-saving case where applicable;
- one deliberately leaked feature that must be rejected.

Acceptance:

- Expected event rows and report counts are literal fixtures.
- The fixture fails if a future timestamp enters the decision-time feature set.
- The fixture reconstructs the exact numerator and denominator.

### Phase 3 — materialize the event ledger

Reuse the existing concept detector and data adapter. Add only the missing dated ledger emission.

Required behavior:

- one stable event identifier per independent eligible observation;
- `observed_at`, every feature's availability, and `outcome_available_at`;
- success, failure, unresolved/censored, and data-quality exclusion kept distinct;
- source, concept, code, calendar, session, and roll provenance;
- deterministic output and receipt hashes;
- append or rebuild semantics consistent with existing artifact authority.

Acceptance:

- Re-running the same specification over identical inputs produces identical rows and hashes.
- Every row is traceable to source bars and the frozen concept version.
- No aggregation removes the dates needed for joins, deduplication, or audit.

### Phase 4 — implement the conditional reducer

Implement `evaluate(query)` behind the module interface.

Required outputs:

- exact cohort selectors;
- eligible, success, failure, unresolved, excluded, raw-event, and independent counts;
- binary/categorical rates or continuous/time-to-event distribution summaries;
- Wilson 95% interval for pilot binary proportions;
- unconditional baseline, absolute lift, relative lift, and sample loss;
- event identifiers or a deterministic event-set receipt;
- discovery/holdout/forward role and evidence state;
- point-in-time and leakage verdicts;
- source and implementation provenance.

Acceptance:

- The reducer matches the golden fixture exactly.
- `n = 0`, thin, leaked, drifting, or unvalidated cells return typed refusal/evidence states.
- Four marginal conditions are never represented as a joint probability unless their event rows are intersected.
- Derived statistics identify their source class counts.

### Phase 5 — time-ordered validation

Tasks:

- Run discovery only on the declared discovery period.
- Freeze the selected query family before opening holdout results.
- Evaluate a chronological holdout with an explicit gap if overlapping outcomes require it.
- Log every tested concept/filter/threshold query in the family.
- Compare the conditional result with the unconditional baseline and simpler nested cohorts.
- Report rolling-window rates, intervals, counts, and lift.
- Where repeated events overlap, use the session as the independent unit or apply the declared clustered/block method.

Acceptance:

- The holdout remains untouched during discovery and selection.
- Results are reported even when unfavorable.
- Multiple-testing treatment and total trials are present.
- No same-sample result receives `oos_verified` or `calibrated` status.

### Phase 6 — as-of shadow lookup

Tasks:

- Evaluate the current context using only information available at the query timestamp.
- Match only preregistered dimensions and frozen bucket edges.
- Store every probability before its outcome is available.
- Compare issued probabilities with realized frequencies using reliability tables and Brier score.
- Monitor rolling drift and demote evidence state when thresholds fail.

Acceptance:

- A query cannot select an eventual day subtype during the live session.
- Issued probabilities and later outcomes are date-keyed and immutable.
- Unsupported cells return `insufficient_evidence` or `descriptive_only`.
- Forecast language is allowed only after the specification's calibration gate passes.

### Phase 7 — library expansion

Do not start this phase until the operator approves the pilot artifact and the current repository authority accepts the interface.

Expand by adding concept specifications and outcome definitions, not new one-off reducers or dashboards. Every added concept must pass the same fixture, point-in-time, provenance, holdout, and status gates.

## Verification matrix

| Risk | Minimum verification |
|---|---|
| Concept mismatch | Frozen definition hash plus hand-labeled occurrence parity |
| Look-ahead | Availability-timestamp test and deliberately leaked fixture |
| Wrong denominator | Literal event-ID reconstruction of eligible/success/failure sets |
| Duplicate dependence | Declared independent unit and deduplication fixture |
| Session/roll drift | Versioned session, calendar, and contract-rule receipts |
| Thin cohort | Count plus uncertainty interval and typed evidence state |
| Filter mining | Query-family ledger and frozen holdout |
| Regime drift | Predeclared rolling windows and demotion rule |
| False tradability | Economics fields remain null until entry/exit/cost rules exist |
| AI overreach | AI output cannot alter reducer results or promotion state |

## Required acceptance surface

The implementation task is not complete because a command prints success. Claude and the operator must be able to inspect:

- the frozen pilot specification;
- the literal golden fixture;
- the emitted dated event rows;
- the report JSON;
- event-set and source hashes;
- the discovery/holdout/forward partition receipt;
- the tested-query family ledger;
- the point-in-time leakage verdict;
- the exact verification command and output;
- the current branch, commit, diff, and intentionally excluded files.

## Evidence-state ladder

```text
descriptive
    -> exploratory
    -> oos_verified
    -> calibrated
```

Fail-closed states can apply at any stage:

```text
insufficient_evidence | leaked | drifted | data_invalid | definition_conflict
```

No automatic promotion is allowed. A definition or cohort change invalidates downstream evidence for that version.

## Delivery and commit boundaries

For the future implementation task:

- Create a dedicated Futures worktree under `C:\tmp\`.
- Preserve the canonical and dirty checkouts.
- Stage only reviewed files.
- Keep implementation, fixtures, and the smallest runnable checks together.
- Do not mix TraderCockpit, Register, unrelated cleanup, or remote deployment.
- Return the exact branch, commit, tests, artifacts, blockers, and next action to Manager.

For this research task, the intended commit contains only this plan, the normative specification, the research report, the nine screenshot evidence files, and the evidence manifest README.

## Claude Code review checklist

Claude should answer these in order:

1. Does any requested condition use information unavailable at the declared decision timestamp?
2. Can every displayed numerator and denominator be reconstructed from independent dated event IDs?
3. Are retrospective eventual-class reports prevented from being presented as live forecasts?
4. Does the interface reuse likely existing Futures authorities rather than duplicate them?
5. Is any proposed seam hypothetical or any module shallow?
6. Are baseline, lift, uncertainty, sample loss, and evidence state mandatory?
7. Can exploratory filtering or AI interaction inspect and overfit the holdout?
8. Are session, time-zone, continuous-contract, roll, missing-data, and correction rules versioned?
9. Are overlapping horizons or multiple intraday events incorrectly treated as independent?
10. Can a high event frequency be mistaken for a profitable strategy?
11. Are all fail-closed states machine-readable and tested?
12. What exact current Futures files and existing helpers should replace any speculative names in this packet?

Claude should return `APPROVE`, `REVISE`, or `BLOCK`, followed by file-and-section-specific findings. It should not implement until the operator opens a separately scoped Futures task.

## Source index

The full evidence ledger is in the [research report](edgeful-conditional-market-statistics-2026-08-02.md). Key sources:

- [Edgeful reports guide](https://www.edgeful.com/blog/posts/edgeful-reports-the-complete-guide)
- [Edgeful platform overview](https://www.edgeful.com/blog/posts/what-is-edgeful)
- [Edgeful subreport definitions](https://help.edgeful.com/en/articles/14198526-subreports)
- [Initial balance breakout report](https://www.edgeful.com/blog/posts/initial-balance-breakout-report)
- [YM date-joined case study](https://www.edgeful.com/blog/posts/ym-initial-balance-strategy)
- [Edgeful AI walkthrough](https://www.edgeful.com/blog/posts/fulll-edgeful-ai-platform-walkthrough)
- [NIST binomial proportion intervals](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
- [White's Reality Check](https://doi.org/10.1111/1468-0262.00152)
- [Probability of Backtest Overfitting](https://ssrn.com/abstract=2326253)
- [Brier score](https://journals.ametsoc.org/view/journals/mwre/78/1/1520-0493_1950_078_0001_vofeit_2_0_co_2.xml)
