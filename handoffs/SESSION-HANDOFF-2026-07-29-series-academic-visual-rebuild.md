# Into the Laboratory Episodes 02–04 — academic and visual rebuild

Date: 2026-07-29

Repository: `C:\Users\MSI\Documents\tradercockpit`

Branch: `fix/news-shot-capture-and-visual-qa-master`

Starting commit: `438556875ca46be0ef05df1888f12a902e430c9b`

## Operator boundary

- Episode 01 was not read, edited, rendered, or otherwise touched.
- No YouTube object, upload, schedule, approval, or public surface was mutated.
- Futures was read-only evidence. No file in Futures or Register was changed.
- Existing unrelated dirty files were preserved.
- Higgsfield may later provide laboratory atmosphere under the operator's plan. It is not an authority for equations, charts, empirical results, or evidence.

## Current release state

The existing Episode 02–04 masters are **blocked from publication**. They contain unreceipted or misleading mathematical language and do not meet the requested visual-explanation standard. They remain on disk and were not deleted:

| Episode | Existing master | SHA-256 | Private YouTube ID |
|---|---|---|---|
| 02 | `OpenMontage/projects/series-02-out-of-sample/hyperframes/renders/ep02-v43-final.mp4` | `961714d17aff7bccc843eddae0d97ba2b70f0abcea37db38825a717447e81ad7` | `brfNtg_rkNE` |
| 03 | `OpenMontage/projects/series-03-slippage/hyperframes/renders/ep03-v9-final.mp4` | `88a6dd92d7f9943cd56ecfea93a0a1be1aa133dfbd2a164fd1b6b28899c71db1` | `RqHwD3ePtPA` |
| 04 | `OpenMontage/projects/series-04-mc-param/hyperframes/renders/ep04-v8-final.mp4` | `1d36afdfc9ddd287943a7607e27a81448ab0cbf77a0fde1908154d21fcdf6c4a` | `h75geeRyJXs` |

## Candidate narration and ontology receipts

These are candidate scripts, not approved TTS or assembled masters:

| Episode | Script | Script SHA-256 | Private ontology | Gate result |
|---|---|---|---|---|
| 02 | `OpenMontage/projects/series-02-out-of-sample/artifacts/vo.academic-rebuild.txt` | `a3ab44084edd7d84361a57316426dc7c4416935f89bf3e4367bae5c9d439b93a` | `OpenMontage/projects/series-02-out-of-sample/artifacts/claims.academic-rebuild.json` | PASS: 20 spoken paragraphs; 14 sources used |
| 03 | `OpenMontage/projects/series-03-slippage/artifacts/vo.academic-rebuild.txt` | `5e163db2751d2ca6d3f78bc7987575a37f5271b974b1bcea378c9a38ac34bf72` | `OpenMontage/projects/series-03-slippage/artifacts/claims.academic-rebuild.json` | PASS: 21 spoken paragraphs; 12 sources used |
| 04 | `OpenMontage/projects/series-04-mc-param/artifacts/vo.academic-rebuild.txt` | `052dc9eb9908cd18e26d66294c979878aaee35ef2ca5b1b4434c986a2211326b` | `OpenMontage/projects/series-04-mc-param/artifacts/claims.academic-rebuild.json` | PASS: 22 spoken paragraphs; 10 sources used |

`tools/teaching_claim_gate.py` fails closed unless every spoken paragraph has exactly one claim receipt, every receipt is used exactly once, the script hash matches, and each mathematical or empirical claim has locators, limitations, and support.

The Episode 04 claim that more than 200 Monte Carlo simulations is bad has been removed. The replacement says:

- there is no universal maximum at 200;
- ordinary independent Monte Carlo standard error decreases in proportion to `1 / sqrt(N)`;
- four times as many runs approximately halves simulation error;
- 200 runs provide coarse lower-tail resolution;
- more runs improve numerical precision conditional on the model, but cannot make an unrealistic model true.

The research ruling and primary literature map are in `productions/_series/monte-carlo-simulation-count-ontology.md`.

## Exact run evidence used

Read-only source: `C:\Users\MSI\repos\futures\runtime\validation\robustness\rb-20260725T133803-b44bd92c\phases`

- Held-out phase: 184 candidates entered, 154 had positive net profit under that ledger, 30 did not; window 2018-02-25 through 2019-09-21.
- Cost phase: 53 entered and 46 survived; 2 failed at 2x and 7 failed at 3x. This was fixed-ledger re-dollarization, not a fresh market replay.
- Parameter phase: 46 entered and 18 survived; 28 failed; 200 simulations per candidate; the first 100 paths were stored for display.
- Parameter implementation: each numeric exit parameter had a 30% selection chance; selected parameters were multiplied by `1 + Uniform(-30%, +30%)`; entry logic remained fixed.
- The parameter artifact says `validated: false` and `wiring_proof: true`. The narration preserves that distinction.

## Deterministic visual rebuild

`tools/build_series_math_visuals.py` created and installed 20 1920×1080 SVGs. Every visual carries a source SHA-256 receipt and labels whether it is run-derived, method-derived, an implementation receipt, or illustrative.

- Episode 02: ordered holdout, held-out field distribution, concentration stress, selected-maximum bias, walk-forward windows, and sample uncertainty.
- Episode 03: cost anatomy, candidate transitions, stress-response curves, fixed-ledger formula, order-type trade-off, and cost drivers.
- Episode 04: run-count error, candidate scatter, fan chart, response geometry, perturbation mechanism, fifth-percentile rank, tail resolution, and determinism receipt.

Preview and receipt: `productions/_series/visual-rebuild-previews/`

Assembly map: `productions/_series/academic-visual-coverage.json`

The supplied screenshots were treated as references for the general idea of visible geometry, not copied as a complete visual plan.

## Vault receipt

The active Obsidian vault was queried first. Graph retrieval refused normal execution because the graph was stale. A closeout re-check found vault `HEAD` and `origin/main` at `ebeeb8403a55b9f40f85384c8f4e150b4407874e`, while `graphify-out/graph.json` records source commit `ecec4b71d8dd0dc025487eadd38c6d7db8760128`. Stale retrieval was used only to route, then the cited Markdown was re-read from disk, including:

- `GTM/Videos/Into the Laboratory — Series Production Plan.md`
- `GTM/Videos/Into the Laboratory — Series Map.md`
- `GTM/Videos/Into the Laboratory — Ep02 v30 Remediation 2026-07-28.md`
- `GTM/Social-Media-Library/Into the Laboratory — Production Standard.md`
- `Decisions/2026-07-28 Teaching Series Releases as a Batch of Four.md`
- `Decisions/2026-07-28 Phase 3 Is Slippage, Not Timing.md`

Manager owns `vault_sync.py`; this repository task did not mutate the vault or falsely claim that the graph was refreshed.

## Verification

```text
python tools/teaching_claim_gate.py --demo
PASS: teaching claim gate demo

python tools/teaching_claim_gate.py --script <episode-script> --ontology <episode-ontology>
PASS: Episode 02 — 20 spoken paragraphs; 14 sources used
PASS: Episode 03 — 21 spoken paragraphs; 12 sources used
PASS: Episode 04 — 22 spoken paragraphs; 10 sources used

python tools/build_series_math_visuals.py --demo
PASS: visual builder demo

python tools/build_series_math_visuals.py --install
PASS: 20 visuals and receipt installed

Installed-asset hash verification
PASS: 20 installed SVG hashes match the generated receipt
```

## Next action

1. Operator/editor reviews the three candidate narrations for voice while receipts remain authoritative.
2. Record the approved narration or select a separately authorized narration path, then measure actual slot durations. The current `emit_vo.py` files call ElevenLabs and were not invoked under the repository's zero-paid-provider rule; the older local Chatterbox delivery was previously rejected.
3. Wire the visual coverage map to those new timings. Do not retrofit the new visuals under the old inaccurate narration.
4. Render new private candidate masters and run visual, claims, term, silence, and full-frame review gates.
5. Return exact master hashes for operator approval. Publication remains a separate exact-hash action.
