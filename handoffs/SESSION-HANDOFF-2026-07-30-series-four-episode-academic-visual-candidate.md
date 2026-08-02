# Into the Laboratory Episodes 01–04 — meaning-first visual revision

Date: 2026-07-30

Repository: `C:\Users\MSI\Documents\tradercockpit`

Branch: `fix/news-shot-capture-and-visual-qa-master`

HEAD: `438556875ca46be0ef05df1888f12a902e430c9b`

## Outcome

All four episodes now use the same current evidence boundary: the rebuilt Futures code graph,
the rebuilt ops-vault graph, exact robustness-run artifacts, and claim-level primary literature.
Episode 01 was absorbed through parallel candidate files; its existing `artifacts/vo.txt` was
not overwritten.

No full narration batch, generated footage batch, render, upload, schedule, subscription change,
commit, push, or public action occurred. Futures remained read-only.

## Graph and run authority

- Graph rebuild receipt:
  `C:\Users\MSI\Documents\Manager\vault\2026-07-29-code-graph-rebuild-receipt.md`
- Futures stamped commit and current `origin/main`:
  `ecec4b71d8dd0dc025487eadd38c6d7db8760128`
- Futures graph: 17,996 nodes, 34,060 links, 1,323 communities, 35 hyperedges.
- Ops-vault graph: 3,434 nodes, 4,959 links; revision
  `51c45b3bc462e63dd714cdc3f4efafa8954e4b12e4bc395ab40c5805ffefe13f`.
- Series run: `rb-20260725T133803-b44bd92c`.
- Recorded funnel: 1,335 → 184 → 154 → 53 → 46 → 18.
- The 154 → 53 screen remains parked as an episode. Episode 03 states the count transition once
  and teaches only the higher-cost fill test.
- Gate-margin recording is proven on `origin/fix/gate-margins`, not merged on stamped main.
  The first-screen census was re-derived from existing artifacts; no script says the repair is
  deployed.
- Of 1,065 profit-factor failures, 856 were within the declared ten-percent band below 1.05.
  Values cluster around profit factor one in this population; this is not a universal generator
  theorem.

Common private snapshot:

`productions/_series/academic-evidence-snapshot.json`

SHA-256:
`595bd51eb866a111c85af339270b64ec983e44fd8ec4e056858937b9caa35a6b`

## Candidate narration and private ontology

| Episode | Script SHA-256 | Claim gate |
|---|---|---|
| 01 | `0ba4424e989feea239e57a25a9897bc4a6def53801395b39929b91f1ac15e75f` | PASS: 29 spoken paragraphs; 12 sources |
| 02 | `c69e0ffe9970ac74ee1db76392ad31ea290afa0710434d04bf88f78a2227e9a8` | PASS: 20 spoken paragraphs; 15 sources |
| 03 | `09986cebda8c11c1d0fee9a134f9ea1d684ce8344898e8e7e3d2d8035ed0a702` | PASS: 21 spoken paragraphs; 13 sources |
| 04 | `505d6b77c177a4be718c65ad9101bf8c90e491fc8907adf01a594f2c6bc12619` | PASS: 22 spoken paragraphs; 11 sources |

Each episode stores:

- `artifacts/vo.academic-rebuild.txt`
- `artifacts/claims.academic-rebuild.json`
- `artifacts/academic-evidence-snapshot.json`

The spoken scripts define the public terms when introduced and exclude repository vocabulary:
phase, gate, pipeline, candidate, artifact, receipt, wiring proof, `p95`, and the parked
timing/delay words. Private `# receipt:` markers remain comments for the fail-closed checker and
are not spoken or displayed.

Episode 04 rejects a universal 200-simulation maximum. It explains:

- what one random replay contains;
- why ordinary independent-run error falls approximately with `1 / sqrt(N)`;
- why four times as many runs roughly halves that numerical error;
- why 200 runs give coarse lower-tail resolution; and
- why more runs cannot repair a bad uncertainty model.

## Mathematical visual layer

`tools/build_series_math_visuals.py` builds 26 deterministic 1920×1080 SVGs:

- Episode 01: 6.
- Episode 02: 6.
- Episode 03: 6.
- Episode 04: 8.

`productions/_series/academic-visual-coverage.json` maps all 56 scene slots and 92 private
claim links to installed assets. SHA-256:
`d214207f6648c7dfe7776cbd8ba84ae19bf39556d531e9a115c08e21e286bdf6`.

Visible SVG text contains no run IDs, field paths, repository source locators, academic citations,
or ontology-receipt language. The private build receipt binds every output to source hashes:

`productions/_series/visual-rebuild-previews/receipt.json`

SHA-256:
`915c1f40b3c88ec91373462a03dad217827329a19f3d5e9c6ff1d951a15abf78`.

## Higgsfield web allocation

The live public web modal listed 23 unlimited models and explicitly said plan-unlimited models
are unavailable through MCP/CLI and several studio surfaces. The operator signed into
`victorianfalcon1741`; live read-back confirmed Max Plan and 3,600 paid credits.

Allocation:

- original deterministic graphics for every mathematical claim;
- draw-on/chalkboard animation for concepts that unfold;
- cards for definitions, comparisons, and checklists;
- real chart captures and trader-at-desk footage for workflow context;
- Higgsfield only for a surviving human/context motion gap or brief non-explanatory transition;
- identical narrator auditions through Eleven v3, MiniMax Speech 2.8 HD, and Seed Audio 1.0;
- regular credits preserved until a required capability is outside unlimited web coverage.

Full plan:
`productions/_series/higgsfield-web-production-allocation.md`

SHA-256:
`286faf900c0cd335e5b2b2244bc6003d12a48931865fba19991061ebd9bef236`.

Three identical-text John auditions now exist from the authenticated web UI:

- Eleven v3: MP3, 13.440s.
- MiniMax Speech 2.8 HD: MP3, 12.841s.
- Seed Audio 1.0: WAV PCM, 16.200s.

All three used checked Unlimited mode. Paid credits read 3,600 before and after. The files,
hashes, media probes, loudness measurements, asset IDs, and claim boundaries are in:

`OpenMontage/projects/series-04-mc-param/artifacts/voice-auditions/higgsfield-unlimited-audition-receipt.json`

Current receipt SHA-256:
`31a22de0d074d346fa1ed9fc5375a813a06fff769e6df0b1319ffd51bfcb0f7b`.

MiniMax and Seed originals are materially quieter than Eleven. Three separate 48 kHz mono PCM
listening copies are level-matched to within 0.7 LU; the originals remain untouched. No
subjective ranking was inferred from measurements.

The operator subsequently selected the earlier Qwen/John MCP sample as the most realistic of all
four auditions. Its RIFF and data length fields were malformed, but FFmpeg recovered a valid
14.456-second, 24 kHz mono PCM payload. The repaired container decodes to the same PCM SHA-256 as
the source:

`6aefda0e7c942570c28f94270d0a50c59fbbb3e43e9aced00d50e52c1c3a64fd`

The untouched source remains in place. Two 48 kHz, 24-bit, 14.456-second processing candidates now
await operator audition:

- `ep04-qwen-john-clean.wav` — 70 Hz high-pass plus loudness normalization; SHA-256
  `6d4fa9e01a2183a973829c166f6c0119a7030b28bf9275a0a2e59aa5aca1dfe7`.
- `ep04-qwen-john-clean-deeper.wav` — the same cleanup plus a formant-preserving
  `-0.7`-semitone pitch shift at unchanged tempo; SHA-256
  `5fb6687b015f39586a09495bc2f16b435df9737424dec495c0bc17496cf8f921`.

Both decode without error and peak at approximately `-1.5 dBTP`. Denoising was deliberately
omitted because the measured source did not justify destructive noise processing. The operator's
source selection is recorded in:

`OpenMontage/projects/series-04-mc-param/artifacts/decision_log.json`

## Meaning-first visual revision — 2026-07-30

The operator rejected `B01`, `B07`, `B13`, and `B15`. Although the files were technically clean,
the laboratory glass, specimen rack, physical spike/platform, and abstract fan do not represent
the narration. All four are quarantined as rejected AI-slop direction; they are not cut candidates.

The files remain only as provenance:

`OpenMontage/projects/series-01-backtest-is-not-a-strategy/hyperframes/assets/broll/higgsfield-candidates/provenance.json`

The series now routes visuals by explanatory function:

- original deterministic mathematical graphics for claims;
- draw-on/chalkboard animation for relationships that unfold;
- cards for definitions, comparisons, and checklists;
- real TradingView captures and existing trader-at-desk footage for workflow and human context;
- generative atmosphere only for brief non-explanatory transitions.

The operator subsequently rejected the first meaning-first proof because it pasted the supplied
reference pictures into a review collage. Supplied screenshots are now reference-only and may not
appear verbatim in a cut or review still. The rejected collage remains only as revision provenance.

Two replacement Episode 04 visuals were drawn from scratch in the TraderCockpit red-on-black
instrument system:

- `snapshots/original-ep04-neighborhood.png` — an illustrative 9×9 neighborhood test that gives
  the same selected center score to a broad plateau and a narrow spike, then reveals whether nearby
  settings confirm or collapse.
- `snapshots/original-ep04-fan-chart.png` — an original chart built from 100 stored display paths
  from 200 recorded simulations, with pointwise middle-50%, middle-90%, and median treatments.
- `snapshots/original-ep04-review-receipt.json` — source hash, output hashes, dimensions, $0 cost,
  reference-only policy, and illustrative-versus-recorded claim boundaries.

The deterministic SVG system was rebuilt into the brand palette and monospace typography. Episode
04's `ep04-response-geometry.svg` now uses the original neighborhood grid rather than imitating a
reference surface. `ep04-fan-chart.svg` remains bound to recorded paths.

Local frame review found four semantically usable chalkboard inserts—distribution, split,
trade-count, and cost-stack—and confirmed `lab-desk-monitors.mp4` as the existing trader seated at
a desk with trading graphics. Ambiguous chalkboard drawings are not explanatory defaults.

Paid credits read 3,600 before and after the rejected wave; measured incremental external cost
remained `$0`. No replacement generation, subscription change, narration batch, render, upload,
schedule, or public action occurred.

## Robustness-geometry revision — 2026-07-30

The operator approved the original explanatory language in principle and required the fan chart
to use the trading convention: profitable terminal paths in green and losing or flat terminal
paths in red. The recorded Episode 04 sample contains 100 stored display paths; all 100 finish
above zero and none finish at or below zero. The corrected chart therefore shows green recorded
paths and reports zero red failures instead of inventing losses for visual balance. Neutral bands
remain reserved for pointwise quantiles and an explicit amber zero line separates terminal outcome
from uncertainty shading.

- Corrected fan-chart PNG SHA-256:
  `2ca5f873b9677bb982fda5ddefb5c2b65e345e1227718665fcce7622715a198a`.
- Updated original-proof receipt SHA-256:
  `430c4bfcb64a28fe71e67cb4abfe5f09663819dcb4d6ea1a472ec2ef2600488f`.
- Ten-geometry review filmstrip SHA-256:
  `799de7a4cb3d0a6c083df5da2f88da4e86acbb25e8bb18032ec546f1d99926a8`.
- Episode mathematical-asset filmstrips:
  - Episode 01:
    `4cabe96a318fffefc412ae02920643773e9362fd80200b2c7db8c66b22cd764e`;
  - Episode 02:
    `7036a24d411cccf8e42e69a27c31ee5c79d12c22b9cff55c4a04779c8e9c9d4b`;
  - Episode 03:
    `932dc7de7d08ec7f1d851bbaa9b92060743cf2926ed25939c280474f50d229a9`;
  - Episode 04:
    `5676ca262cfea3148aaefd2cfaeb7b4339cfecf78be59dab41b6f78be5a47184`.

`academic-visual-coverage.json` now defines ten test-specific visual families: search
multiplicity, holdout sequencing, population distribution, threshold fragility, concentration
stress, cost sensitivity, parameter neighborhoods, Monte Carlo paths, tail resolution, and
reproducibility. Each family records required encodings and forbidden substitutes so future
assembly cannot silently replace a test with decorative atmosphere.

The operator also replaced minimum-cost selection with quality-first use of the existing
Higgsfield Max plan. Higgsfield remains eligible for a defined non-evidentiary human/context
motion gap; it remains ineligible to invent mathematical evidence. No new provider call or credit
readback occurred in this revision.

The operator then explicitly approved the revision-5 mathematical layer and directed production
to continue. That approval is recorded as decision `d-027`; it does not approve the entire assets
stage or authorize a full render.

A sentence-level mixed-media review now covers all 56 academic scene slots:

- 41 animated mathematical scenes;
- 9 owned chalkboard draw-on scenes;
- 3 definition/limitation cards;
- 1 real TradingView chart scene; and
- 2 non-evidentiary trader-context scenes from the existing premium desk clip.

The four filmstrips are:

- Episode 01:
  `ea6e4cc9a037d0e1d8d298ed667d7fa0a60a42dc9a760f503d97bfea51eb8290`;
- Episode 02:
  `9562d2a7395c9abe9bc53470762746f91e5d6a194aceb1c923ddf01f88bb0459`;
- Episode 03:
  `5e54fc4f80309b2ac52af388c244ccdc9d03b31e691c48e13d557c4d279efd39`;
- Episode 04:
  `311cf3bc8d6fabaef26ad51a8cbe017a95b678685b4cab48ad27a972024f4305`.

The assets checkpoint is revision 6, `in_progress`, and the full render remains blocked:

- checkpoint SHA-256:
  `2cd0dca3b4b4ec77956dd09a35e731f364415d9276735180abd681ec3ee5259f`;
- mixed-media receipt SHA-256:
  `d31cd67b529a5410d65ed02616f1300b54c17241e5864a1b8d5119ebc7e79e72`;
- decision-log SHA-256:
  `c77c9a7dbb85ab1ebb36a311f495dd70113ddc1128805e015836559c3a942298`.

The existing trader-at-desk clip closes the current human/context gap, so no new Higgsfield
generation was justified.

## Canonical idea reset after mixed-media approval

The operator approved the four mixed-media filmstrips and directed production to continue.
OpenMontage's live resume audit then exposed that Episode 01 still carried the rejected
nine-scene laboratory brief, while Episodes 02–04 had packaging files but no canonical idea
checkpoint. The four projects have now been reset to the same meaning-first academic idea gate.

All four schema-valid briefs select:

- hybrid narration-led graphics;
- the approved five-mode visual system;
- HyperFrames as the recommended runtime and Remotion as the explicit alternative;
- Atelier rather than stock templates;
- no music; and
- no generated mathematical evidence or static-slide fallback.

The current registry preflight reported FFmpeg, Remotion, and HyperFrames unavailable. Its
specific HyperFrames warning is `ffmpeg not found on PATH`. The briefs therefore fail closed:
the runtime must be repaired and re-read before scene implementation or compose.

Current idea checkpoints are all `awaiting_human`, `human_approved=false`, with zero critical
review findings:

| Episode | Brief SHA-256 | Idea checkpoint SHA-256 |
|---|---|---|
| 01 | `7a4a0abd0875407667b55eaf1a5ecd4729c099a66c7f540962d8d083eed68743` | `44f5b26999b36d3ee6b30f6cbbbd424e8e4da47c889c5663fa90e91af10ab703` |
| 02 | `8abfdd8942710165ab6dfc46f2037a8e9766101719440972f2c4fcbb42e565ff` | `53d5da2d62b10de59a15ed6f832047ed410a0b0d6c18dc19ac1cd9a6505e6026` |
| 03 | `b00d880887739eba23a1eba25aa9680f45a8304d9a2a73cb5ee357e2cd872b6b` | `5732d290af28eb0f39b9a5c3a4645471c02546ccd60130c20f271f0a0a8ffa69` |
| 04 | `b6887f05dca4f2ab86cc72a88041ac80de22ce13793fd76bdd1343305de32d36` | `2e59b67321dbf8eb5f187850cea66ffa8ddcf0f72a287ba9d4a336ca85a67e60` |

Episode 03 and Episode 04 still carry their previously disclosed thumbnail-package approval
items. Those do not authorize or block the current private script rewrite, but they remain open
before publication.

## Verification

```text
teaching_claim_gate.py --demo
PASS

Episode 01
PASS: 29 spoken paragraphs; 12 sources used

Episode 02
PASS: 20 spoken paragraphs; 15 sources used

Episode 03
PASS: 21 spoken paragraphs; 13 sources used

Episode 04
PASS: 22 spoken paragraphs; 11 sources used

build_series_math_visuals.py --demo
PASS

build_series_math_visuals.py --install
PASS: 26 visuals

SVG XML + output hashes + evidence-snapshot hash
PASS

Scene assets
PASS: 56/56

Scene-to-claim links
PASS: 92

Spoken repository-vocabulary scan
PASS

Visible SVG internal-evidence-text scan
PASS

Higgsfield web audio
PASS: 3/3 files probed; 3/3 hashes and sizes match; paid-credit delta zero

Higgsfield web video pilot
PASS: 4/4 files stored and hashed; operator rejection recorded; no candidates remain; paid-credit delta zero

Meaning-first asset revision
PASS: decision-log schema; checkpoint schema; revision 6/in-progress; full render not started

Episode 04 asset-gate proof
PASS: two original 1920x1080 PNGs; no supplied screenshot pixels; fan chart uses 100 green profitable endings and 0 red losing or flat endings

Robustness visual grammar
PASS: 10 geometry families; 10 grammar frames; 26 mathematical review frames; 4 episode filmstrips; 26 SVG hashes and XML parse

Mixed-media scene review
PASS: 56/56 routes; five visual modes; all sources, scene frames, filmstrips, and hashes verified

Canonical idea reset
PASS: 4/4 brief schemas; 4/4 decision-log schemas; 4/4 checkpoint schemas; all four projects stop at idea/awaiting_human; full render not started

Qwen/John repair
PASS: corrected WAV header; decoded PCM hash matches source

Qwen/John processing
PASS: clean and clean-deeper candidates decode; 48 kHz mono PCM; 14.456s; no clipping

Offline ASR
BLOCKED: faster-whisper PyAV _core DLL load returned Access is denied
```

## Vault update

Updated existing source note:

`GTM/Videos/Into the Laboratory — Series Production Plan.md`

SHA-256:
`32e67de9d12f10fd2788d7ff9054e936e2997fb6826dbd89bfa9ccb34d4420c4`.

Appended vault log:

`log.md`

SHA-256:
`3615ac52c7aa5c76f7ebd1ec934933ab6309f71f4f39ed30cd9155ce7f3380d3`.

Generated graph pages were not edited and `vault_sync.py` was not run. Manager must perform the
next graph/index refresh.

## Next action

1. Operator approves or revises the four canonical idea briefs, including the HyperFrames /
   Remotion runtime choice, Atelier mode, and no-music plan.
2. Mark only the idea gates complete, then build the four canonical `script.json` artifacts and
   stop at the batch script gate.
3. After script approval, build the 56-scene canonical scene plans; after that separate approval,
   align the asset manifests. Do not inherit the rejected nine-scene laboratory plan.
4. Audition `ep04-qwen-john-clean.wav` and `ep04-qwen-john-clean-deeper.wav`; approve one
   processed narrator.
5. Generate full narration only from the approved voice.
6. Repair and re-read the local composition runtime before scene implementation or compose.
7. Measure actual narration durations, wire approved assets to timing, render four private
   candidates, and run full-frame visual, audio, claims, terminology, silence, and encoded-output
   review.
8. Return four exact master hashes for batch approval. Publication remains a separate action.

## Runtime repaired; canonical scripts awaiting batch approval — 2026-07-30

The operator approved the four canonical idea briefs and directed production to continue. The
OpenMontage runtime was repaired at the shared dependency boundary:

- project-local FFmpeg 8.1.2 is discovered by `VideoCompose`;
- project-local HyperFrames 0.7.82 is preferred without a network lookup;
- Node.js 24.15.0 satisfies the HyperFrames runtime;
- HyperFrames doctor exits 0; and
- the live registry now reports `ffmpeg=true`, `hyperframes=true`, `remotion=false`.

Remotion is not the selected runtime. The installation sources, checksums, binary hashes, tests,
and doctor output are recorded in
`productions/_series/openmontage-runtime-repair-receipt.json`, SHA-256
`51262b3b663362505ac15e98ac60616184f447cb4849f30c263c5ed8f3423a21`.
The focused runtime regression suite passed `5 passed, 44 deselected`.

All four idea checkpoints are completed and human-approved. Four exact-text canonical scripts
were then built from the approved academic narration:

| Episode | Sections | Words | Estimated duration | Script SHA-256 | Script checkpoint SHA-256 |
|---|---:|---:|---:|---|---|
| 01 | 13 | 1,092 | 454.862s | `1030483e5772e7c36bc56ca8fbfbf6e4bb0255d3859665c675cb92011115f372` | `06743a1dd5d0e396a423b3e1a53201fe8aa56bc51e561f04a162fb6d2f909582` |
| 02 | 13 | 1,319 | 548.793s | `7e023cef70e5bf8d925edbcb2989457479665b4f7714fb27cd26b732ac349440` | `4ed754b55d1e65e5d3d44cad3de95eb74f759ea307c2e7d1d52ee6073396b65e` |
| 03 | 15 | 1,343 | 558.724s | `0aece4178543aab4d2b7069f0451a67439604cf4d1f506041e5991e83a58648f` | `1138b725ef5dc12fb868c7892762ab03b7d6599999c01ce1417bbb007997deef` |
| 04 | 15 | 1,390 | 578.172s | `fdcfc3bcb959994e7e4490b82bd219c9973b4f799f1932f88b8c8e4f84d2da5c` | `8a1738634f8bac7d4c09ddbbbf1857b0a27f2fbb276aaffa97e7ee9a37ee68fc` |

Schema validation, exact narration/provider-text mirroring, contiguous timing, source references,
and scene enhancement cues pass for all four scripts. The teaching-series claim gate remains
PASS at 29/20/21/22 spoken paragraphs with 12/15/13/11 sources. Review reports zero critical
findings.

The generic daily-market style gate is retained as an advisory investigation receipt. Its flags
require a ticker or digit in individual sections, a numeric invalidation level in the close, or
avoid corrective teaching contrast; those rules do not match this teaching-series lane. The
exact receipted narration was not rewritten to satisfy those unrelated heuristics.

All four script checkpoints now read `script/awaiting_human`, `human_approved=false`. The next
authorized action is one operator batch approval or revision of these four scripts. Only after
that approval may production build the 56-scene canonical scene plans, then stop again at the
separate scene-plan gate. The Qwen/John `clean` versus `clean-deeper` narrator choice and the
Episode 03–04 thumbnail-package choices remain open.

No canonical scene plan, asset manifest, narration batch, render, Higgsfield generation call,
upload, schedule, subscription change, or public action advanced.

## Four canonical scene plans awaiting batch approval — 2026-07-30

The operator approved the exact four-script batch. The unchanged approved script hashes were
written to completed, human-approved script checkpoints, and all four projects advanced only to
the canonical scene-plan stage.

The scene plans bind every approved narration section one-to-one to the 56 previously reviewed
mixed-media routes:

| Episode | Scenes | Mode mix | Duration basis | Scene-plan SHA-256 |
|---|---:|---|---:|---|
| 01 | 13 | 9 animated math, 2 chalkboard, 1 real chart, 1 trader context | 454.862s | `01b5eee206c587d11a14266d770c4e6d91d4c48a432bb502225e6af74a6422f6` |
| 02 | 13 | 10 animated math, 2 chalkboard, 1 card | 548.793s | `ad40eae304d1a7e2b1c3bee6dca514630edcde9b6cbccf8c00bb7364ae9c5240` |
| 03 | 15 | 10 animated math, 3 chalkboard, 1 card, 1 trader context | 558.724s | `52bcce540ac1b542bc7388e0338a994596bb2c0a1f7da3fcd1f9f379d2d7555c` |
| 04 | 15 | 12 animated math, 2 chalkboard, 1 card | 578.172s | `10f3718c78c3fdb133cbb19fcb8e7ace30c636ab1214d05731bc03601a40193a` |

Each plan covers the full timeline from the 0–3 second ident through the estimated final script
boundary. All 56 scenes name a reviewed source and exact source/review-frame hashes, a distinct
primary visual subject, a narrative and information role, purposeful motion, phone-safe framing,
overlay-density limits, and the no-duplicate-caption rule. The 16:9 YouTube master is the only
variant in this gate; any future 9:16 derivative requires separate crop and layout planning.

OpenMontage schema validation passes for all four plans. The variation checker reports `strong`
with zero violations on all four. Slideshow-risk scores are `strong`: 0.00 / 0.33 / 0.00 / 0.33.
The only reviewer suggestion is to replace estimated section boundaries with measured Qwen/John
audio after the narrator-processing choice and narration batch are separately approved.

All four checkpoints read `scene_plan/awaiting_human`, `human_approved=false`, with zero critical
findings and external provider spend/reservation of $0. No current scene has an unfilled visual
job, so no new Higgsfield call is justified at this gate; the Max plan remains reserved for a
specific non-evidentiary gap if one appears during the separately gated assets alignment.

The next action is operator approval or revision of the four scene plans. After approval,
production may align the canonical asset manifests to these exact 56 scenes, populate the
scene-by-scene filmstrip, and stop again at the assets gate before any draft or full render.
Qwen/John `clean` versus `clean-deeper` and the Episode 03–04 thumbnail packages remain open.

No asset manifest, narration batch, Higgsfield generation, edit decision, render, upload,
schedule, subscription change, or public action advanced.

## Scene plans approved; visual assets verified; narration disclosure approval required — 2026-07-30

The operator approved the exact four scene-plan hashes and selected `Qwen / John clean`;
`clean-deeper` is rejected. All four scene-plan checkpoints are now completed and
human-approved, and all four projects are stopped at `assets / in_progress`.

Canonical visual asset manifests now inventory the 56 approved source routes without promoting
the review stills to final frames:

| Episode | Visual assets | Asset-manifest SHA-256 |
|---|---:|---|
| 01 | 13 | `3c3d1ae5b3ac62c4e179593de32c26f7ccbb3d72e646401334935a18ba19611f` |
| 02 | 13 | `dc9c6a20ab9928dae0e50646e165385b7ecbeeee1b7b8f87f9af5e009ea6caf4` |
| 03 | 15 | `0aeb612a3f6c6aefe0a75fee7273adf20af939e5ef544e80c18d28b4b1ec20ab` |
| 04 | 15 | `ac582bfd42265fed80f36a3601bc4e890f2f2dd56b7054df94ca8a94bffbd1a1` |

OpenMontage schema validation, source paths, source hashes, filmstrip hashes, the zero visual-gap
claim, and the full-render lock all pass. No Higgsfield visual generation is needed.

The current authenticated Higgsfield catalog was read back and exposes `Qwen Audio 3.0 TTS
Flash` with the same John preset ID `6b528d43-c056-4a2f-9d82-1591a7ba13b0`. One exact runtime
verification take completed:

- job `e3f0215f-cac1-4b1e-9496-b0c7c3116dd6`;
- local file
  `OpenMontage/projects/series-04-mc-param/artifacts/voice-auditions/ep04-qwen-audio-3-john-runtime-check.wav`;
- SHA-256 `0c9ac077934b9dea0649f90742eb116f41a5bdf6a48d0f23bef39a591392ee1c`;
- 11.6 seconds, 24 kHz mono PCM; and
- Max-plan balance moved from 3,600 to 3,599.91 credits.

The current official Qwen take is not byte- or duration-identical to the previously approved
14.456-second Qwen sample whose exact model version was unknown. The selected `clean` mastering
contract remains 70 Hz high-pass plus two-pass EBU R128 normalization to -16 LUFS / -1.5 dBTP,
48 kHz mono 24-bit PCM, with no denoising.

The 56-section batch is prepared and dry-run verified, with an estimated 5.04 credits. It has not
started because it would disclose all four unpublished scripts to Higgsfield. The next action
requires explicit operator approval of that payload disclosure and credit use. After approval,
run `python -B tools/generate_series_higgsfield_narration.py --workers 4`, verify all 56 files and
manifest hashes, write `assets / awaiting_human`, and stop before edit or render.

No full narration batch, edit decision, render, upload, schedule, subscription change, or public
action advanced.

## Qwen/John narration completed; four asset gates awaiting approval — 2026-07-30

The operator explicitly approved disclosure of all four unpublished scripts to Higgsfield and
authorized 56 Qwen Audio 3.0 / John generation jobs followed by local `clean` mastering.
Higgsfield completed 56 usable jobs. One additional duplicate attempt failed and was excluded;
no failed output appears in the manifests.

The local mastering contract is unchanged: 70 Hz high-pass, two-pass EBU R128 normalization to
-16 LUFS / -1.5 dBTP, 48 kHz mono 24-bit PCM, and no denoising. Exact script text, raw and clean
file hashes, media headers, manifests, filmstrips, source assets, and review-frame hashes all
pass independent validation:

| Episode | Narration files | Clean audio | Asset-manifest SHA-256 | Asset-checkpoint SHA-256 |
|---|---:|---:|---|---|
| 01 | 13 | 465.280s | `d462f5ac5c6d61cb03bfdcda64b80b4a54b1e0a319d72b3f03036ec02ea3980e` | `afb0650a81766dda5ab4cee9ef84894499d3ccf58a3cf24c41181623b38d4400` |
| 02 | 13 | 543.360s | `f4d35d272618adba390a8d011d214c67b6b1359667983067fa069c338b02b893` | `053890afa9e3d6a990810af92f2f089e139efa6b3139847b99238412016e88e3` |
| 03 | 15 | 550.640s | `89172a83aaf92b5b31ed1666909437cd81c01694c2998009999b50d228dc0aa6` | `e18b65fc8d1e6010b725be3c9f77f2cd0edeb0e4295db6899f1c841917746c65` |
| 04 | 15 | 590.480s | `f419cbeb57dd3bf474ece3cb19dc4f95fd98f9613945b389f00e2241f3dd5729` | `e1fa9eaac7351662003c4c121bcf9a80eced6558b787b756e8414366018bd398` |

The batch produced 2,149.760 seconds of clean narration. The authenticated Max-plan balance moved
from 3,599.91 to 3,586.49 credits: 13.42 credits actually used, 8.38 above the 5.04 estimate.
There was no top-up or incremental dollar purchase. The resumable receipt is
`productions/_series/higgsfield-qwen-john-narration-receipt.json`, SHA-256
`6ee95c4b3962d94752ff06dd6d5bc05cc51a1de2fcdc44b0a36d8de86905129d`.

All four OpenMontage checkpoints now read `assets / awaiting_human`,
`human_approved=false`. Asset review reports zero critical findings and zero visual gaps across
41 animated-math scenes, 9 original chalkboard draw-ons, 3 cards, 1 real chart, and 2 existing
trader-context scenes. The accepted current Qwen runtime-version disclosure and actual credit
variance are recorded in every checkpoint.

The next action is operator approval or revision of the four asset packages. No edit decision,
draft render, full render, upload, schedule, subscription change, or public action has started.
The ops-vault source note and `log.md` were refreshed from these live receipts; Manager-owned
generated index/graph/hot-cache sync was not run from the TraderCockpit repository.
