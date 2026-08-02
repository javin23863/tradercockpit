# Strategy evidence audit for the teaching series

Date: 2026-07-30  
Futures repository inspected read-only: `C:\Users\MSI\repos\futures`  
Repository state inspected: branch `main`, commit `33651e5819c780663bbe93f19146f6dd9e440304`

## Decision-grade conclusions

1. The standard registered order is **parameter Monte Carlo → trade-dropout/order Monte Carlo → walk-forward → WFC**. Walk-forward is not the immediate next phase after parameter Monte Carlo.
2. Futures, forex, and equities use that same standard phase registry. Their strategy definitions and transaction-cost dollarization differ, but the four robustness algorithms do not branch by those asset classes.
3. Options use a separate registry: lifecycle-parameter Monte Carlo → occurrence-dropout/order-bootstrap Monte Carlo → frozen-structure walk-forward. **There is no options WFC phase.**
4. The strongest local late-pipeline receipt is a real DOW H1 run. It went **46 → 18 → 1 → 0** through parameter MC, trade MC, and walk-forward. Its only trade-MC survivor produced positive aggregate walk-forward net, but failed the consistency/drawdown gates. No candidate reached WFC, so this receipt cannot support “WFC killed the strategy.”
5. The local forex and stock receipts do not support late-pipeline teaching claims: the cited EURUSD run lost every candidate at intake, and the cited SPY Connors RSI2 run lost its one candidate at first OOS.
6. The real options receipt is not fit to demonstrate walk-forward: it emitted zero rolling runs, null walk-forward metrics, and nevertheless recorded pass because the options Phase 8 gate block was empty. Its MC was also reduced to 12 dropout/lifecycle simulations and 25 bootstraps.
7. A definitive episode can explain the algorithms from code and use the DOW run as the worked example. It must not imply that the same empirical result was observed in forex, stocks, or options.

## 1. Registered phase order

The standard registry is the authority consumed by the orchestrator:

| Order | Key | Meaning |
|---:|---|---|
| 1 | `phase01_intake` | Intake + IS baseline |
| 2 | `phase02_oos` | OOS retest |
| 3 | `phase03_timing` | Timing/session stress |
| 4 | `phase04_cost` | Cost stress |
| 5 | `phase06_mc_param` | Exit-parameter Monte Carlo |
| 6 | `phase07_mc_trade` | Trade-dropout and order-bootstrap Monte Carlo |
| 7 | `phase08_walkforward` | Frozen-parameter walk-forward retest |
| 8 | `phase08b_wfc` | Walk-forward correlation gate |
| 9 | `phase09_final_oos` | Final OOS |
| 10 | `phase10_governance` | Governance battery |

Primary source: `C:\Users\MSI\repos\futures\packages\esq\robustness_pipeline\registry.py:37-81`. The same file explicitly documents this order and the removal of Phase 5 at `:109-128`.

The orchestrator uses this registry by default and accepts the options registry only when the options runner supplies it: `C:\Users\MSI\repos\futures\packages\esq\robustness_pipeline\orchestrator.py:769-776`.

### What each adjacent phase actually tests

- **Parameter MC:** 200 simulations; each exit parameter has a 30% chance of being moved by up to ±30%. ATR periods stay fixed, and entry logic is not perturbed. Sources: `C:\Users\MSI\repos\futures\packages\esq\robustness_pipeline\phases\phase06_mc_param.py:1-15,36-60`; `C:\Users\MSI\repos\futures\packages\esq\robustness_pipeline\param_space.py:37-80`.
- **Trade MC:** delete 10% of trades over 200 simulations, then bootstrap/permutate trade order 1,000 times. This is post-processing of one frozen OOS ledger, not another parameter search. Source: `C:\Users\MSI\repos\futures\packages\esq\robustness_pipeline\phases\phase07_mc_trade.py:1-12,30-36,74-128`.
- **Walk-forward:** keep parameters frozen; slice one deterministic replay into full 12-month windows stepped every 6 months. Grade total net, profitable-window fraction, concentration of profits, minimum trades per window, and worst-window drawdown relative to a fixed capital base. Source: `C:\Users\MSI\repos\futures\packages\esq\robustness_pipeline\phases\phase08_walkforward.py:1-42,64-71,83-140`.
- **WFC:** create a 5×5 stop-loss/profit-target surface, measure the same 25 cells in IS and OOS, then gate Spearman rank correlation. It asks whether good regions in the IS landscape stay relatively good OOS; it is not the ordinary frozen-parameter walk-forward retest. Source: `C:\Users\MSI\repos\futures\packages\esq\robustness_pipeline\phases\phase08b_wfc.py:1-31,50-67,70-96,128-168`.

The registered thresholds make the distinction concrete: parameter MC retains at least 50% of baseline conservative-tail Ret/DD; trade MC adds a ≤1.5× bootstrap drawdown ceiling; walk-forward requires positive net, >70% profitable runs, <50% profit concentration, ≥20 trades in the worst-count run, and ≤25% capital-base drawdown; WFC requires Spearman >0.3. Source: `C:\Users\MSI\repos\futures\configs\robustness_fast_lib2.yaml:156-171`.

## 2. Representative strategy passports

These are implementation passports, not recommendations or claims of profitability.

### Futures — DOW H1 Donchian breakout

Evidence class: **sealed roster / exact construction; not the identified late-pipeline survivor**.

- Enter long when close exceeds the prior bar’s 20-bar rolling high.
- Exit package: break-even at 1.0 ATR(120), exit-after-bars 48, profit target 5.0 ATR(25), stop 1.5 ATR(20), trailing stop 1.8 ATR(50), trailing activation 1.2 ATR(60).
- Tunable construction parameters visible here: Donchian lookback 20; six exit distance/period/time values.

Primary source: `C:\Users\MSI\repos\futures\runtime\validation\library_cycle\dow-h1-lib1-limit5\frozen_roster.yaml:2-40`.

The DOW run’s actual walk-forward survivor was `formula-2309285457-3357`, a three-clause generated formula using `<`, `>`, `and`, `ema`, `rolling_min`, and `sma`. The run manifest preserves its factor inventory, seed/index, signal hash, and specification hash but not its full entry AST. Therefore the repository snapshot does **not** support narrating that survivor’s exact indicator periods or Boolean expression. Its ledger row is `C:\Users\MSI\repos\futures\runtime\validation\robustness\ledger\dow-h1-lib1.jsonl:1650`.

### Forex — EURUSD M1 Donchian breakout

Evidence class: **sealed roster plus real run, but no late-phase survivor**.

- Enter when close exceeds the prior bar’s 20-bar rolling high.
- Exit package: break-even 0.8 ATR(60), exit-after-bars 350, target 2.0 ATR(70), stop 1.0 ATR(70), trail 1.5 ATR(90), trail activation 1.0 ATR(120).

Primary source: `C:\Users\MSI\repos\futures\runtime\validation\library_cycle\eurusd-m1-cat1-limit250\frozen_roster.yaml:2-61`.

The real EURUSD receipt entered 2,051 candidates at intake and retained zero. Every later artifact, including MC and walk-forward, is an empty-funnel artifact. Sources: `C:\Users\MSI\repos\futures\runtime\validation\robustness\rb-20260715T154557-12660559\phases\phase01_intake.json:961791-963863`; `C:\Users\MSI\repos\futures\runtime\validation\robustness\rb-20260715T154557-12660559\phases\phase06_mc_param.json:13-33`.

### Stocks — SPY D1 Connors RSI2

Evidence class: **sealed roster plus real intake/OOS run, but no MC or walk-forward evidence**.

- Enter long when close is above SMA(200) and RSI(2) is below 5.
- Exit when close is above SMA(5), with same-close entry enabled.
- Tunable strategy parameters recorded by the generator: trend length `n=200`, oversold threshold `q=5.0`, RSI length `rn=2`; exit SMA length is 5.

Primary source: `C:\Users\MSI\repos\futures\runtime\validation\library_cycle\spy-d1-connors-lib1-specc1840f9631ff\frozen_roster.yaml:2-38,79-93`.

The real run retained the one candidate at intake and dropped it at first OOS, leaving all later phases empty. Sources: `C:\Users\MSI\repos\futures\runtime\validation\robustness\rb-20260715T045247-67fe0873\phases\phase01_intake.json:3452-3474`; `C:\Users\MSI\repos\futures\runtime\validation\robustness\rb-20260715T045247-67fe0873\phases\phase02_oos.json:768-793`.

### Options — SPY 45-DTE 16-delta short strangle

Evidence class: **exact config plus real short-history run; late robustness evidence is diagnostic only**.

- Sell one 16-delta put and one 16-delta call at a target 45 DTE.
- Permit ±7 days of DTE tolerance and one day between occurrences.
- Close at 50% of entry credit or at 21 DTE.
- Two sibling candidates add IV-rank minimums of 30 and 50.
- Natural tunable parameters: put/call delta, target DTE, DTE tolerance, occurrence spacing, profit target, exit DTE, and IVR threshold.

Primary source: `C:\Users\MSI\repos\futures\configs\robustness_options_real.yaml:7-65`.

## 3. Cross-asset differences

| Asset lane | Parameter MC | Trade/occurrence MC | Walk-forward | WFC |
|---|---|---|---|---|
| Futures | Exit distances/time exit | Trade dropout + trade-order bootstrap | Frozen parameters, 12mo/6mo | 5×5 SL/PT IS-to-OOS rank correlation |
| Forex | Same standard implementation | Same standard implementation | Same standard implementation | Same standard implementation |
| Stocks | Same standard implementation | Same standard implementation | Same standard implementation | Same standard implementation |
| Options | Lifecycle jitter: profit target, stop-loss multiple, exit DTE | Whole-occurrence dropout + occurrence-order bootstrap | Frozen option structure; month/day rolling windows | **Not registered** |

Futures/forex/equities share the standard registry. Asset-specific economics enter through calibrated dollarization; the equity path uses generic $0.01/share mechanics and symbol-specific cost lookup. Source: `C:\Users\MSI\repos\futures\packages\esq\robustness_pipeline\phases\__init__.py:40-70`.

Options instead register lifecycle MC, occurrence MC, and frozen-structure walk-forward, with no WFC sibling: `C:\Users\MSI\repos\futures\packages\esq\options_pipeline\registry.py:26-66`. Lifecycle jitter is limited to profit target, stop-loss multiple, and exit DTE: `C:\Users\MSI\repos\futures\packages\esq\options_pipeline\phases\opt_phase06_mc_lifecycle.py:1-18,45-74`. Occurrence MC drops or resamples whole option occurrences, never individual legs: `C:\Users\MSI\repos\futures\packages\esq\options_pipeline\phases\opt_phase07_mc_occurrence.py:1-25,42-77`.

## 4. What the existing receipts can support

### Strong enough for a worked lesson

The real DOW H1 run `rb-20260725T133803-b44bd92c` supports this factual story:

- Parameter MC: 46 entered, 18 survived.
- Trade dropout/order bootstrap: 18 entered, 1 survived.
- Walk-forward: the sole survivor, `formula-2309285457-3357`, produced `wf_net=45,216.8`, was profitable in 62.5% of eight runs, had at least 215 trades per run, concentrated 36.6195% of positive-run profit in its largest run, and had worst-run drawdown equal to 80.0016% of the $50,000 grading base.
- It failed because >70% profitable runs and ≤25% drawdown were required.
- WFC received zero candidates.

Primary receipts:

- `C:\Users\MSI\repos\futures\runtime\validation\robustness\rb-20260725T133803-b44bd92c\phases\phase06_mc_param.json:561057-561160`
- `C:\Users\MSI\repos\futures\runtime\validation\robustness\rb-20260725T133803-b44bd92c\phases\phase07_mc_trade.json:436938-436983`
- `C:\Users\MSI\repos\futures\runtime\validation\robustness\rb-20260725T133803-b44bd92c\phases\phase08_walkforward.json:2243-2274,2288-2317`
- `C:\Users\MSI\repos\futures\runtime\validation\robustness\rb-20260725T133803-b44bd92c\phases\phase08b_wfc.json:13-35`

The strongest teaching point is: **positive total walk-forward profit is insufficient when the result is temporally inconsistent or the worst window consumes too much of the grading capital.** That conclusion follows directly from the registered gates and the receipt.

### Unsupported or too weak to publish as demonstrated fact

- “WFC killed the last DOW strategy.” It did not reach WFC.
- Any numeric WFC result for forex, stocks, or options.
- “The same funnel happened across all four asset classes.”
- Exact indicator periods/logic of the DOW walk-forward survivor; its full signal payload is absent from the local receipt and ledger.
- A valid options walk-forward result. The real options artifact reports zero runs and null metrics (`C:\Users\MSI\repos\futures\runtime\validation\robustness\rb-20260714T211850-932b1d6b\phases\opt_phase08_walkforward.json:3-32`) while `configs\robustness_options_real.yaml:101-103` supplies empty Phase 6–8 gate blocks.
- General options-MC conclusions from the same receipt. It used only 12 MC simulations and 25 bootstraps, with as few as one to seven occurrences, rather than the standard 200/1,000 demonstration scale.
- Strategy-quality certification from an artifact’s `validated` field. Phase artifacts deliberately self-report `validated: false`; they are execution receipts, not self-certificates. Source: `C:\Users\MSI\repos\futures\packages\esq\robustness_pipeline\artifacts.py:49-56`.

## 5. Episode implication

If the already-produced parameter-MC video remains immediately before the new episode, the next process-faithful lesson is **trade dropout and order permutation**, not walk-forward. The DOW receipt gives that episode a clean, real result: parameter perturbation left 18; changing which trades occurred and their sequence left one.

Walk-forward should follow it. That episode already has a strong receipted reveal—positive aggregate profit still failed—but WFC needs either:

1. a different existing real receipt in which a candidate actually reaches WFC, or
2. an operator-authorized governed run that produces a non-empty WFC artifact.

Until then, WFC can be taught from the registered algorithm as a clearly labeled method demonstration, but it cannot be presented as the observed cause of elimination in the cited run.
