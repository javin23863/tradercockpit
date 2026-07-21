# TraderCockpit Growth Experiment System

- **Status:** Active foundation; organic baseline only
- **Owner:** TraderCockpit for acquisition and social; future consumer repository for in-product behavior
- **Updated:** 2026-07-16
- **External media spend:** `$0`; paid activation is not authorized
- **Reference concept:** [AI Meta Ads Playbook](https://www.facebook.com/reel/878979078602533/)

## Purpose

Turn research, ideas, creative, landing pages, and measured results into one reusable learning loop.
Audience, angle, hook, format, and offer stay separate so one controlled change can be measured and
reused without rebuilding the entire campaign idea.

The canonical library and experiment records live in
`social-ops/growth-experiments.v1.json`. This document explains the workflow; it does not duplicate
that ledger.

## TraderCockpit translation

| Reference block | TraderCockpit implementation |
|---|---|
| Hopper | New ideas enter through research/content backlog; measured components re-enter through the Sunday review. |
| Libraries | Stable audience, angle, hook, format, and offer IDs in the growth manifest. “Avatar” means a user segment, never a synthetic presenter. |
| Crafting bench | One experiment joins one ID from each library and changes one component. |
| Landing pages | `docs/index.html`, populated only by verified `product-manifest/v1` fields. |
| Dispenser | Existing `social-batch/v1` and exact-hash operator approval, built last. |
| Experiment database | The growth manifest joined to `social-ops/metrics.csv` by batch and item ID. |
| Numbers gate | A read-only advisory verdict; the operator records the actual decision. |

## Operator workflow

1. Add or reuse library IDs in the manifest.
2. Add a `proposed` experiment with one hypothesis, surface, primary metric, and guardrails.
3. After an approved item exists, add its repo-relative batch path and item ID, then mark the
   experiment `running`.
4. Add the reviewed 24-hour platform row to `social-ops/metrics.csv`; blanks remain unknown.
5. Lock thresholds only after the 14-day baseline and its receipt are reviewed.
6. Read the dashboard suggestion, then record a dated operator `kill`, `iterate`, or `reuse`
   decision. A new iteration receives a new experiment ID.

```powershell
py tools/growth_experiments.py validate
py tools/growth_experiments.py report --json
py tools/dashboard.py --no-open
```

Validation failures are blocking for the experiment record, not permission to change or bypass the
social publishing gate.

## Measurement contract

One experiment covers one surface. The module never aggregates unlike platforms. Direct retention
and CTR fields come from the existing scorecard; shares, saves, CTA clicks, and confirmed signups
are normalized only when their denominator exists and is greater than zero. Missing values remain
unknown rather than becoming zero.

Every joined observation must retain a passing claims gate and zero material corrections. A failed
guardrail forces a `kill` suggestion and prevents the recorded decision from reusing that exact
component.

Thresholds start in `pending_baseline`. Once locked, the module takes the median primary metric:

- below `killBelow` → `kill`;
- at or above `reuseAtOrAbove` → `reuse`;
- between them → `iterate`;
- missing values or too few observations → `insufficient_evidence`.

The suggestion never writes to the manifest. Operator decisions remain explicit and auditable.

## Attribution

Reuse the landing page's existing fields. Experiment links use:

- `utm_source=<channel>`
- `utm_medium=organic_social|email`
- `utm_campaign=<experiment-id>`

No new public tracking field or analytics provider is introduced.

## Boundaries

- `paidActivation` must remain `disabled`; there is no ad account, campaign generator, provider
  adapter, budget, or spend path.
- Product-facing experiments remain blocked until verified consumer facts, real media, consent,
  attribution, and exact launch-copy approval exist.
- Consumer activation and retention measurements remain owned by the future consumer repository.
- Generated media remains creative material, never evidence. Claims, provenance, accessibility,
  consent, approval, and correction gates continue to control publication.
