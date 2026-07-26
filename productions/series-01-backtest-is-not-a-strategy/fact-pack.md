# E1 Fact Pack — A Backtest Is Not a Trading Strategy

Status: working draft; not filming-ready  
Format: operator on camera  
External media cost: $0  
Public performance claims: none

## Package

- Promise: A green backtest shows what rules did on old prices; it does not prove the idea is ready for real money.
- Title: **You Don’t Have a Trading Strategy — You Have a Backtest**
- Thumbnail: **DON’T TRADE THIS**
- Selected hook: **“An indicator and a green backtest do not make a trading strategy. They make a candidate.”**

## Audience

- Primary: a retail trader who builds indicator rules in TradingView, sees a profitable backtest, and treats the result as ready to trade.
- Secondary: a system trader who knows testing vocabulary but lacks a single controlled lifecycle from idea through retirement.
- Surface problem: how to build a trading strategy.
- Deeper problem: the need for permission to believe a result.
- Transformation: “the green line means I am ready” → “the green line answers only the old-prices question.”

## Claim spine

### E1-C1 — Candidate generation and validation are separate

The project’s strategy-genesis contract treats every generated idea as candidate-grade until the unchanged evaluation funnel says otherwise. Generation may begin from a formula, paper, thesis, or other idea source; generation itself grants no trading authority.

Source:

- `C:/Users/MSI/repos/futures/docs/vault/esq-genesis-pipeline-spec.md`, Thesis and F1.

### E1-C2 — The lifecycle extends past the backtest

The declared lifecycle is:

`idea → candidate → robustness verdict → engine parity → paper → limited live → monitored → demoted or retired → research`

Source:

- `C:/Users/MSI/repos/futures/docs/vault/trader-cockpit-consumer-product-plan-2026-07-15.md`, “Strategy lifecycle.”

### E1-C3 — Paper precedes real exposure

The architecture requires paper before real exposure and keeps monitoring, demotion, and retirement inside the strategy lifecycle.

Source:

- `C:/Users/MSI/repos/futures/docs/CONTINUOUS_ALPHA_ARCHITECTURE.md`, “The loop” and “Invariants.”

### E1-C4 — The series never promises an edge

The operator’s binding position is that the series teaches process rather than selling a strategy, signal, win rate, or alpha promise.

Source:

- Ops vault `Series/Operator Doctrine — You Are the Market.md`.

## Live demand screen

**BLOCKED / UNMEASURED.** On 2026-07-24, the official command failed closed:

`OpenMontage\.venv\Scripts\python.exe tools\social_analytics.py hotdog`

Error: `RuntimeError: YouTube credential is not currently valid`

These public videos are packaging references only; they are not a substitute for the authenticated Hot Dog demand screen:

- [How I Develop Trading Strategies](https://www.youtube.com/watch?v=NLBXgSmRBgU)
- [Trading System Design — A Practical Guide](https://www.youtube.com/watch?v=LlYwvEhZKkQ)
- [Build Your Own Trading Strategy](https://www.youtube.com/watch?v=fIEwVmJJ06s)

The title and thumbnail remain working choices until the official screen succeeds.

## Demonstration status

**BLOCKED FOR FILMING.** The current on-camera card is a construction exercise, not a pre-registered unknown-result experiment. Filming requires either:

- operator authorization for one exact governed test through the remote-compute path; or
- an explicit E1 waiver that keeps this manifesto episode non-computational.

No parameters, result, authorization, or waiver are inferred here.

## Claims excluded

- The operator’s killed-strategy story remains unreceipted and is not used.
- No claim that every retail strategy fails.
- No claim that a backtest is useless.
- No claim that the pipeline produces profitable strategies.
- No Monte Carlo claim; that is a later validation lesson.
