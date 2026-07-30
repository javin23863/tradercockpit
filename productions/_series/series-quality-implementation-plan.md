# Teaching-series quality system and repair plan

Date: 2026-07-30
Status: RATIFIED FOR IMPLEMENTATION by the operator's instruction to continue. This authorizes
the quality-system work and episode repairs below. It does not authorize upload, scheduling, or
publication.

## Outcome

Release the first TraderCockpit teaching playlist as one pipeline-faithful, evidence-backed
series in one coordinated wave. Every episode must teach a real validation phase, expose the
strategy and test parameters the evidence supports, sound like one operator, and remain bound to
the exact public copy and media that passed review.

The release is all-or-nothing: no episode is published until every episode in the initial slate
has a current exact-hash certification.

## Public slate

| Episode | Validation phase | Source material |
|---:|---|---|
| 1 | Strategy construction and intake | Current Episode 1 |
| 2 | Out-of-sample testing | Current Episode 2 |
| 3 | Timing and session stress | Restore `series-XX-timing-PARKED` |
| 4 | Cost and slippage stress | Renumber current Episode 3 |
| 5 | Exit-parameter Monte Carlo | Renumber current Episode 4 |
| 6 | Trade dropout and trade-order bootstrap | Next net-new episode |
| 7 | Frozen-parameter walk-forward | After Episode 6 |
| 8 | Walk-forward correlation | Only after a real candidate reaches WFC |

The standard robustness order is parameter Monte Carlo, trade Monte Carlo, walk-forward, then
walk-forward correlation. Options use their separate lifecycle/occurrence variants and have no
registered WFC phase. An episode must not imply that an observed result occurred in an asset lane
whose receipt is empty.

## Episode evidence contract

Before drafting, create a strategy passport containing:

- instrument, asset class, timeframe, and tested date range;
- complete entry, exit, position-sizing, and transaction-cost construction;
- every tunable parameter and the exact value used in the worked example;
- phase algorithm, simulation/window counts, perturbation ranges, and registered thresholds;
- run identifiers, source locators, limitations, and unsupported details;
- the distinction between a fully specified teaching example and any anonymous population result.

Missing construction evidence is written as unavailable. It is never reconstructed from memory.
Titles, thumbnails, narration, charts, and descriptions may not merge results from different
strategies or asset lanes without saying so.

## Human-facing writing contract

The target is consistent operator voice and viewer comprehension, not an AI-detector score.
Internal provenance and required synthetic-content disclosures remain intact.

Use this order:

1. Lock the fact pack and strategy passport.
2. Capture the operator explaining the thesis in his own words.
3. Draft from that capture.
4. Apply the existing no-AI-slop/Humanizer-derived edit: preserve information, add no facts, and
   keep the operator's vocabulary, cadence, uncertainty, bluntness, and useful rough edges.
5. Compare the candidate against protected numbers, names, parameters, negation, qualifiers,
   quotes, citations, disclaimers, and disclosures.
6. Run an independent critic against the evidence contract.
7. Complete the operator read-aloud pass.
8. Hash the final narration and rebuild its claim ontology.
9. Run source gates before TTS or visual assembly.

The refinement pass is upstream editing. Certification gates audit and block; they never rewrite.

Writing references: [`blader/humanizer`](https://github.com/blader/humanizer) is used as a
minimum-edit pattern library, not installed as another runtime. The
[`StoryScope` paper](https://arxiv.org/pdf/2604.03136) informs narrative-level review, not an
authorship classifier or a score to game. The local `no-ai-slop` workflow remains the canonical,
versioned application of both.

## Enforced public surfaces

Certification covers the exact:

- narration;
- title and thumbnail copy;
- description, chapters, tags, and captions;
- financial disclaimer, privacy state, and synthetic-content setting;
- scene plan, composition source, and rendered master.

Changing a certified surface invalidates certification. Upload must compare the requested public
values with the certified values rather than accepting arbitrary command-line replacements.
The initial episode package contains no separate public-document surface. Adding one requires
extending the release contract and human-facing gate first; an undeclared document cannot be
smuggled into a release.

## Shared implementation delta

Keep the change behind the existing episode acceptance surface:

1. Add the teaching claim gate to the executable episode chain.
2. Add one thin human-facing audit that reuses the existing writing detector and applies explicit
   profiles for narration, short titles, descriptions, and public documentation.
3. Extend the episode receipt to hash every declared public surface and release setting.
4. Make receipt verification re-hash those sources as well as the master.
5. Make YouTube upload reject public arguments that differ from certification, require the
   exact series or social-batch approval artifact, upload privately first, attach and read back
   the certified captions and thumbnail, then promote to the certified privacy only after the
   complete private object passes.
6. Add a source-only gate command so writing and claims fail before costly audio/render work.
7. Update the canonical `series-script` skill and add a discovery bridge to the existing
   `no-ai-slop` skill. Do not install another Humanizer or StoryScope runtime.

The source contract requires `artifacts/strategy-passport.json`,
`artifacts/operator-capture.txt`, `artifacts/human-facing-review.json`, a separately issued
exact-hash `artifacts/operator-script-approval.json`, and local hash-bound evidence files for
every factual claim. The review receipt is bound to the exact narration, capture, and passport
hashes and carries the resolved independent critic, protected-item, disclosure, and dated
operator read-aloud decisions. Final certification also requires the operator's separate
exact-hash `artifacts/operator-master-approval.json`; it explicitly does not authorize
publication.

Do not add a Git hook. Episode project files live outside the parent repository's tracked surface,
and local hooks would not protect the Linux worker or upload boundary.

## Repair scope

### Episode 1

- Resolve the Golden Cross construction gap: the entry is SMA 10/50, while the exact bracket exit
  and sizing choice still require an evidence-backed decision.
- Add the complete strategy passport.
- Align the title promise with the actual first spoken paragraph.
- Rewrite academic prose into operator speech and rebuild claims, narration, timing, and render.
- Reuse verified intake, arithmetic, and checklist visuals where their labels remain accurate.

### Episode 2

- Use the fully specified SPY Connors RSI2 example for construction and real OOS failure.
- Keep the separate DOW population result explicitly separate from that protagonist.
- Preserve point-in-time, universe-selection, and sample-size limitations.
- Rebuild the hook, claims, narration, timing, and render; reuse sound OOS/timeline visuals.

### Episode 3

- Restore the parked timing/session-stress lesson as source material, not a finished episode.
- Remove causal overclaims and define what each timing perturbation can establish.
- Add the strategy passport or label its missing construction honestly.
- Rebuild claims, narration, visuals, packaging, and render.

### Episode 4

- Renumber the current cost/slippage episode.
- Identify the instrument, timeframe, dates, baseline commission, tick/slippage units, sizing
  convention, and one traceable strategy example.
- Remove the current admission that an unseen phase performed the prior population reduction.
- Rebuild claims, narration, packaging, scene identifiers, transitions, and render.

### Episode 5

- Renumber and narrow the current Monte Carlo episode to exit-parameter Monte Carlo.
- Show the actual exit parameter names and values and one complete perturbation.
- Separate that fully specified teaching example from the real anonymous 46-to-18 field result.
- Define one simulation, explain the 200-run configuration without calling it an optimum, and
  distinguish parameter perturbation from trade bootstrap/permutation and MCMC.
- Rebuild claims, narration, packaging, scene identifiers, transitions, and render.

## Linux repair and render lane

The Linux desktop is a worker, not the source of truth.

Before transfer:

1. Verify host identity, OS updates, firewall, remote-access policy, user privileges, storage,
   RAM, CPU/GPU, and exact Node/Python/FFmpeg/browser versions.
2. Verify the TraderCockpit and OpenMontage revisions and refuse an unclean or mismatched base.
3. Keep credentials, browser profiles, API keys, `.env` files, model caches, and unrelated data
   off the transfer.
4. Use one isolated directory per episode and one exclusive owner per directory.

Transfer only a SHA-256-manifested source bundle: briefs, passports, narration, claims, package,
scene plans, composition source, small chart data, and required episode tools. Exclude old renders,
audio takes, snapshots, virtual environments, `node_modules`, caches, and backups.

Start with at most two concurrent renders and benchmark before assigning CPU workers. Each repair
returns:

- source patch and file inventory;
- strategy-passport and fact-preservation receipts;
- critic and operator-review findings;
- source-gate and final episode-gate receipts;
- final master, contact sheets, Whisper read-back, logs, and SHA-256 manifest.

No intermediate is accepted as a master. No result is accepted solely because a worker reports
success.

## Parallel ownership

Shared gates, skills, schemas, and uploader logic land and freeze first. Episode agents then own
only their assigned episode directories; they do not edit shared tools or another episode.
Renumbering is coordinated centrally so links, titles, descriptions, captions, thumbnails, and
transitions cannot diverge.

The initial episode wave runs in bounded batches to fit available agent and render capacity.
Episode 6 research/scripting may begin only from the frozen foundation and must not reuse the
public Episode 5 number.

## Acceptance

The foundation is ready when:

- adversarial tests prove claim, number, disclosure, and public-copy drift block;
- a clean voice-only rewrite can proceed without an authorship score;
- source-only gating blocks before TTS;
- changing any certified title, description, caption, thumbnail, setting, source, or master makes
  verification fail;
- skill validation and an independent forward test pass;
- the complete diff preserves every unratified stopped-task change outside this branch.

An episode is ready when its exact source and master pass the unified chain with no copied waiver,
its strategy passport and claim ontology are complete, and the operator approves the exact script
and master hashes.

The playlist is ready when Episodes 1-5 all pass a blind cross-episode review for numbering,
terminology, factual continuity, voice, title-promise delivery, accessibility, and public-surface
hashes. Publication remains a separate operator approval.
