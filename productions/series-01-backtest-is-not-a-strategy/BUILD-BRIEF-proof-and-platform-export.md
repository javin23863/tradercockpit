# Build Brief — Proof Surface + Platform Export

**Project:** TraderCockpit / "You Are The Market" series
**Purpose:** Give the public something *real* to look at. Answer the comment "how do you know? where's your data from?" with actual math on screen, and let customers run trusted strategies where they already are (MetaTrader, TradingView).
**Status:** planning locked, not yet built. Brainstorm output — no shared repo or kanban touched to produce this.
**Date locked:** 2026-07-24

---

## The one-line finding that changes the plan

The math is **not missing**. esq already computes it, serializes it to disk, Ed25519-signs it, and even ships it into the customer snapshot. The gap is **legible charts**, not backend math. And **MetaTrader export already exists** as a deterministic, golden-tested transpiler (`esq.adapters.mt5`). We are mostly *rendering* and *reusing*, not building from scratch.

---

## Two surfaces

### Surface 1 — Proof display (show the math)

Today the customer "Apollo" dashboard binds real numbers to a decorative space-physics scene — no axes, no values. A full readable chart suite already exists but is wired only into the operator app. Job = mount real charts into the customer view, inside the governance allowlist.

**6 panels, with status:**

| # | Panel | Status | Work |
|---|-------|--------|------|
| 6 | **Pipeline journey** (Scene-07 8-stage path, live per-run state) | FREE | Pure composition over existing snapshot (phase board + 8 live-eligibility nodes). Build FIRST — it's the spine. |
| 1 | **Walk-forward equity** (in-sample vs out-of-sample) | FREE | Equity arrays already in the customer snapshot. Drop in a real axed chart. |
| 3 | **IS-vs-OOS scatter** (overfit detector) | FREE | `wfc.rank_pairs` already served. One 45°-line scatter. Note: points are exit-surface cells, not time folds. |
| 4 | **Sensitivity heatmap** (robust plateau vs lone spike) | EMIT | Grid on disk + operator chart exist; add a customer-safe projection (strip param labels), then mount. |
| 2 | **Monte Carlo** (distribution, not one line) | EMIT | Envelope band FREE now; add ~10-line emit for terminal-value / %-profitable / drawdown histograms. Path-cloud stays operator-only. |
| 5 | **Execution fidelity** (backtest vs live markers) | BUILD | No artifact pairs signal↔fill timestamps. Needs a reconciler + signed telemetry. Heaviest; last. |

**Governance = the trust story, not a blocker.** Customer allowlist forbids raw candidate IDs, dollar P&L, exit params, individual MC paths. So panels show ranks / shapes / envelopes / aggregates. That's the honest "can't show you the secret params, can show you the out-of-sample and the distribution — signed" — same spine as Scene-08.

**Build order:** 6 → 1 → 3 (all FREE, zero new backend) → 4 → 2 → 5.

**Monte Carlo reality:** exists decisively — 5 engines (trade-dropout, bootstrap max-DD, param-perturbation, options GBM, permutation null). Real distributions, serialized. Not the single-line kind.

### Surface 2 — Platform export (meet the customer where they are)

**A strategy in esq is data, not code:** a closed ~67-op JSON AST + typed exit-bracket dict `{sl,pt,be,trail,eab}` + typed sizing doc. The engine interprets it; no strategy-supplied Python ever runs. That is exactly the precondition for **deterministic codegen** — write ~67 op-emitters once per platform, every strategy after compiles byte-for-byte.

**Deterministic transpiler, NOT an LLM per strategy.** Deterministic = ~0 tokens per strategy, reproducible (same spec hash → identical output), and *testable*. LLM-per-strategy = tokens every time, non-reproducible, unverifiable — which breaks the trust thesis. LLM is the wrong tool.

**The trust boundary is already mechanized.** `refuse_reasons()` fail-closed refuses anything it can't faithfully emit (ML/GA/RL/policy engines, time ops, context/htf ops, true-volume, level-kind exits). **The strategies that pass clean ARE the trustable set.** "Display only what we can trust" is a computable set, not a judgment call.

| Target | Status | Work |
|--------|--------|------|
| **MetaTrader / MQL5** | DONE — reuse as-is (`esq.adapters.mt5`, golden-tested, ships in customer exe) | Only *coverage*: extend `SUPPORTED_OPS` + land timezone & volume calibration cards. No rebuild. |
| **TradingView / Pine v6** | BUILD once (`adapters/pine.py`) | ~60–70% copied from `mt5.py` (parse/refuse/warmup/DSL-semantics front-half is platform-agnostic). Swap only back-half emitters → `strategy.entry/exit`. |

**Critical discipline (inherited from mt5.py):** hand-roll indicators — do NOT use raw Pine `ta.sma/ta.rsi/ta.atr`; they differ from esq's pandas semantics (same reason mt5.py avoids `iATR/iRSI`). Two known landmines: htf time-shift, and swing/value-area conventions.

**Coverage:** ~70–85% of the single-symbol bar library transpiles; ~0% of options (instrument not traded on these platforms). Escape hatch is per-**op** not per-strategy: `ctx` (cross-asset), `xs_rank` (universe panel), `event_*` (econ calendar) need data one chart can't supply → refuse those strategies cleanly.

---

## Fidelity test — the credibility spine (Scene-06 "match the screens")

Golden-**signal** diff, only possible because output is deterministic:

1. **Cheap / CI (every build):** source-golden snapshot — the generated code is exactly what the machine should produce. Catches emitter regressions. Runs automatically.
2. **Full / authoritative (the "trusted" badge):** run esq replay on fixed bars → capture per-bar intent + order events; run the transpiled EA/strategy in the platform's own tester on byte-identical bars → assert trade-for-trade equality of entry timing, direction, stop/target distances. Any divergence → fail-closed, not shown as "trusted." Needs the rented box (no-local-compute doctrine).

One pass proves a strategy forever (deterministic); regenerate only when the spec changes.

---

## Locked decisions (2026-07-24)

1. **Pine v6.**
2. **Ship now** with the refuse-clean DSL subset. Add timezone + volume blocks later as "we just added X" updates.
3. **Cheap source-check on every build; the "trusted" badge customers see requires the full behavior (trade-log) check on the box.**
4. **Build authorization:** at build time — claim the `adapter.tradingview-pine` kanban card, take ownership, mirror the work into this project. This is the one authorized kanban write; everything else stays read-only.
5. **Legacy d1–d5 parity strategies included** via 5 hand-written per-template emitters.
6. **Options display-only** — never published to MT5/Pine.

---

## Isolation fence (both target zones are cold — keep them that way)

- **Build in a fresh isolated worktree only** (`C:/tmp/futures-<name>`), open-wave at build time. Never the shared clone `C:/Users/MSI/repos/futures`.
- **No kanban / manager.db writes** except the one authorized card claim (decision 4). Any other coordination need → surface to operator, don't write the board.
- **Zone 2 (Pine):** new sibling file `packages/esq/adapters/pine.py` + `tests/fast/test_pine_transpiler.py`. Import `dsl.py` + mt5's `SUPPORTED_OPS`/`SUPPORTED_COLUMNS` as single source of truth — do NOT fork them.
- **OFF-LIMITS until it merges:** `packages/esq/consumer_contracts.py` + `engine/strategies/entry_factory.py` — a live P0 lane (`consumer.repo-boundary-gate`) has uncommitted edits there in `C:/tmp/futures-repo-boundary`. The customer-exe codegen imports through that boundary → branch off its merged head or coordinate.
- **Zone 1 (proof charts):** add new files under `apps/cockpit/frontend/src/components/charts/`; keep edits to shared wiring (`CustomerViews.tsx`, `EvidenceSurface.tsx`, `CustomerApp.tsx`) minimal and rebase on main immediately before PR — ~20 dormant-but-open codex cockpit PRs own those exact files.
- **Do not touch:** the genesis sweep fleet (`configs/genesis_sweep.yaml`, `library/index.yaml` across ~32 genesis worktrees — a live run) or the active validation lanes (fidelity-merge-train, pipeline-certification, data.ingestion-runtime). Different subsystems.
- **Stdlib-only contract for `pine.py`** exactly like `mt5.py` (no numpy/pandas/yaml — enforced by `test_customer_packaging_boundary.py`).

---

## Suggested build sequence (when green-lit)

1. **Proof panels 6 → 1 → 3** — three real charts, zero new backend. Flips "pretty but empty" → "point a skeptic at it." Biggest narrative payoff for least work.
2. **`adapters/pine.py` (v6)** — reuse mt5 front-half, new back-half emitters, source-golden test. Claim the card here.
3. **Proof panels 4 → 2** — small emits.
4. **Full behavior fidelity harness on the box** — the "trusted" badge gate.
5. **Coverage widen** — timezone + volume calibration cards (unlocks more strategies for both platforms).
6. **Panel 5 (execution fidelity)** — heaviest; needs the paired-marker reconciler + signed telemetry.

---

## Open items / notes

- MT5 coverage-widen (timezone/volume cards) is a coverage task, not machinery — the transpiler scaffold is done.
- Transport for the customer proof feed (live `/api/customer/pipeline` vs signed-record desktop bundle) affects freshness gating — confirm which ships before wiring panels to a feed.
- Per-run vs per-strategy: today all customer quant evidence hangs off the newest run. A true per-strategy proof panel in the Strategies tab needs a small backend add. Single-newest-run is fine for the series-01 demo.
