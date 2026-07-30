---
name: series-script
description: Write the full spoken script for a teaching-series episode (operator on camera, "you are the market" playlist) — actual words, beat map, visual column, receipts, gates. Use for "script the episode", "series script", "teaching video script", or any on-camera playlist scripting. NOT for the daily news video (that is daily-news-video).
---

# Series script writer — the teaching playlist

Operator on camera, teaching retail traders what they're doing wrong. This skill DRAFTS THE
ACTUAL SPOKEN WORDS; the operator approves, edits freely, and delivers. Separate lane from the
daily (`daily-news-video`) and from the parked Show.

## Read before drafting

Read `templates/episode-contracts.md` in this skill directory before creating episode files. It
contains the literal JSON skeletons, working-to-runtime handoff, and source/final gate inventory;
do not improvise those contracts from an older episode.

Vault (`Desktop\Obsidian Vault From VPS\tradercockpit\tradercockpit`):
- `GTM/README.md` → "Writing a script" list (voice guide, claims ontology, offer constraints)
- `Series/Operator Doctrine — You Are the Market.md` — the thesis; binding claims position
- `Series/Set 03 — Dumb Money Hunter Delivery.md` §1–3 — register mechanics (§4–5 never adopt)
- `Series/Reviewer Notes — Series Sets 01-03 — 2026-07-24.md` — the never-say corrections
- Skill `youtube-scriptwriting-isaacverse` — hook layering, but/therefore, complexity ramp

## The voice — how the operator articulates

**Persona: 25 years in the market, blunt, receipts in hand. Controversial by telling the
industry's uncomfortable truth — never by attacking a person or channel.** The controversy IS the
doctrine; no manufactured outrage needed:

Phrase bank — the operator's own verbatim words (doctrine note + every capture session and
recorded episode; append as they accumulate). Seed the register from these:
- *"You're their market. You're not educated. No one showed you."*
- *"If anybody had money, a strategy, or edge, they would not sell it to you."*
- *"I just killed my longest living strategy... You can't fall in love with it. It decays."*
  (kill story: script ONLY from a receipted fact pack, never the bare dictation)

Register rules (Set 03 mechanics, our personality on top):
- Second person, present tense, talking TO one trader, not lecturing a room.
- The claim of the episode lands inside the first 15 seconds. No throat-clearing, no
  "in this video we will".
- Short declaratives. One idea per sentence. Rhetorical question → immediate answer.
- Tag-question paragraphing sparingly (`right?`, `okay?`) — pacing device, not a tic.
- **Unedited resolution:** when something is demonstrated on camera, the outcome lands on camera
  — hesitation and surprise kept, no cut. That authenticity is the moat DeltaTrend doesn't have.
- Anti-boring rule: never explain a concept for more than ~40 seconds without either an on-screen
  payoff (artifact, animation, number changing) or a stakes reset ("here's what that costs you").

Never: name/mock the studied channels, reaction formats, win-rate promises, "easiest", urgency
frames, alpha promises, machinery words on screen ("claims gate", "receipt", "verified" — show
the artifact, speak the implication), discovery-window dollar figures.

## Repeatable episode process

Work in `productions/series-<nn>-<slug>/`. Stages, in order:

**1. Thesis.** One controversial-but-true sentence, doctrine-derived. If it can't be said in one
sentence a retail trader would repeat to a friend, it's not the thesis yet.

**2. Receipt pull + strategy passport — the trusted-source spine.** Every factual claim binds to a real repo
artifact BEFORE drafting: cert outputs, robustness runs, battery verdicts, equity curves, the
killed-strategy fact pack (`repos\futures` docs/vault + run artifacts; lake catalog for data
claims). **Check `productions/_series/receipt-library.md` FIRST** — the accumulating index of
camera-ready artifacts (artifact path → what it shows → episodes that used it). Pull from it;
add every new artifact discovered back to it. Per-episode archaeology is the throughput killer —
the library turns it into a one-time cost. Write `fact-pack.md`: claim → artifact path → what
appears on screen. Also write `artifacts/strategy-passport.json` from receipts: asset class, instrument,
venue, timeframe/session/timezone, entry and exit rules, sizing, costs/slippage/fees, data and
test windows, split method, tunable parameters with ranges/steps, validation settings/seeds,
pass thresholds, results, limitations, and an exact source locator for each value. Use `unknown`
when a field is not evidenced. Never infer a missing formula or parameter. No artifact → cut the
claim, or explicitly voice it as opinion ("my read, after 25 years"). Keep the working claim
map in the fact pack; do not mint `artifacts/claims.json` until the final spoken script exists.

**3. Package first — the first-impression contract (operator ruling 2026-07-24).**
Thumbnail and title are attention-grabbing or the video does not exist. Then the chain is
binding: **thumbnail promise → title promise → known intro → first 5 seconds pay the promise —
or they leave.**
- Write the **promise** as one line before anything else. Thumbnail, title, and the first
  post-intro sentence all express THIS line. If any of the three would make a viewer feel
  baited by the others, rewrite until they match.
- **Demand screen the topic** before committing: search-intent check (what retail actually
  types — "is my strategy overfit", prop-firm math, Monte Carlo backtest) via the Hot Dog
  automation (YouTube Desk §2). Thesis-strong but demand-dead topics get the doctrine threaded
  into a searched topic instead of their own video.
  Run episode-specific phrases and keep the receipt with the episode:
  `python -B tools/social_analytics.py hotdog --query "<phrase>" --query "<phrase>" --output "<episode-dir>/artifacts/demand-screen.json"`.
  An expired read-only credential or incomplete query set blocks package lock; it never falls back
  to a writer's intuition.
- Title: confrontation or curiosity gap, search-aware, never a topic label.
- Thumbnail: mechanics per the house reference ([[Thumbnails & First Impressions — House
  Reference]], [[First Impression System Team Brief]]); geometry gated by `tools/visual_qa.py`.
- **Known intro:** the series' fixed ident — same every episode, this is what we're known for.
  Keep it ≤5s; every second of ident is paid for by the payoff that follows.

**4. Beat map** (`beats.md`) — fixed skeleton, ~8–12 min:
- **Known intro (0:00–0:05):** the fixed series ident. Never varies.
- **Promise payoff (0:05–0:10):** the first five seconds after the intro deliver exactly what
  the thumbnail and title promised — the thesis, stated cold, with its visual on screen. No
  throat-clearing, no "welcome back". This beat is checked against the promise line at the gate.
- **Stakes (0:10–1:00):** why it costs the viewer money — tie to "you are the market".
- **Teach loop ×2–4:** concept in plain words → artifact/animation on screen → implication
  ("so when your guru shows you X, now you know what's missing"). Complexity ramps across loops.
- **The demonstration — pre-registered on-camera experiment.** Our translation of Set 03's
  unedited-resolution engine (we never call live trades): declare the test before running it —
  "here's the strategy everyone teaches; I don't know if it survives honest validation" — run
  it, let the outcome land on camera, no cut. **The outcome must be genuinely unknown at record
  time** — that's where the real hesitation comes from, and it's the controversy engine:
  "I tested it" beats "trust me", with no callout needed. Compute for these runs follows
  standing rules: operator green-light, rented box, never local.
- **The turn:** what the honest version looks like (this is where our process quietly
  differentiates; product stays unnamed until the Apollo arc episode).
- **Close (≤30s):** one takeaway the viewer can apply tonight + open loop to next episode.
  Never a purchase CTA — nothing is for sale.

**5. Capture — the operator's words first.** Before any drafting: the operator talks the thesis
out loud for ~5 minutes — voice memo, rambling fine, no structure needed. Transcribe it. The
draft is built FROM this transcript: his sentence rhythm, his metaphors, his emphasis — the
skill supplies structure, never voice. Every captured session (and every recorded episode)
feeds the phrase bank, so the voice spec compounds instead of drifting AI-generic.

**6. Draft and refine the words** (`script.md`, two columns: SPOKEN | SCREEN). Full sentences as delivered,
contractions and all — teleprompter-ready. Every SCREEN cell names its artifact or animation.
But/therefore chaining between beats; no "and then".
Word budget: on-camera natural pace ≈ 145–160 wpm → 8–12 min ≈ **1,200–1,900 words**.
Give every SPOKEN paragraph one stable claim ID. After approval, export the SPOKEN cells in
delivery order to `OpenMontage/projects/<episode>/artifacts/vo.txt`, putting
`# receipt: <claim-id>` immediately before each paragraph. `vo.txt` is the canonical narration
that the claim gate, TTS, captions, and final receipt bind; it may not be edited independently.
<!-- ponytail: 145-160 wpm is a prior, not a measurement — time the operator's first recording
     and calibrate the band; the daily lane's MEASURED clone rate is 145 wpm (the old 197 figure
     was wrong and produced a 14.3 min master), and it is a CLONE rate — do not reuse it -->

After the factual draft, read `.claude/skills/no-ai-slop/SKILL.md` and its `eval.md` completely
and run its minimum-edit pass against the operator capture. Preserve information, not sentence
shape: do not add, remove, soften, strengthen, or generalize any claim; preserve every number,
range, unit, parameter, negation, uncertainty marker, limitation, quote, source relationship,
and disclosure. If a cleaner sentence would require a new fact or interpretation, leave it
alone and flag it. Compare the revision to the fact pack and strategy passport, fix every failed
eval check, and record the protected-item comparison plus the short change summary in the
hash-bound `artifacts/human-facing-review.json`.

Aim for the operator's recognizable voice and a natural read, never a classifier score or hidden
authorship. Preserve internal drafting provenance and every required disclosure for synthetic
narration, visuals, or other generated media.

**7. Visual column spec.** Attention graphics, rendered at production (OpenMontage/matplotlib/
plotly — no new engine). When E1 hits rendering, build ONE reusable `tools/mc_visuals.py` (fan /
histogram / underwater / 3D surface from a trades CSV or param-grid CSV) — justified because
every episode reuses it; do not build per-episode animation code.

House patterns — reference exemplars in `productions/_series/visual-refs/` (operator-supplied
2026-07-24 screenshots; ours must out-pop them):
- **Path fan (the wave):** resampled equity curves racing in one-by-one, then the percentile
  envelope; **actual backtest overlaid in white** — the kill-shot: where the sold dream sits
  inside the honest cloud.
- **Distribution build:** terminal-P&L histogram filling bar-by-bar as sims run; breakeven and
  5th/95th percentile markers drop in last, observed result lands final.
- **3D parameter terrain:** the optimization surface (peaks = the dream). Never static — slow
  rotation, camera push toward the chosen peak, circle-and-arrow tracking "the peak you picked".
- **The terrain morph (the reveal):** in-sample surface animates INTO the out-of-sample surface
  — peaks collapsing on screen. One cut, the whole overfitting lesson. Side-by-side is the
  fallback; the morph is the signature.
- **Pass-rate geometry:** 3D win-rate × R:R surface with the EV=0 breakeven curve carved in
  black (prop-firm episodes).
- **Green/red scatter cloud:** 3D outcome scatter (size × count × ROI), rotating, breakeven
  plane slicing through it.
- **Underwater plot:** drawdown filled area — visceral, red.
- **IS/OOS boundary strip:** one equity curve, color shifts at the split line — degradation
  visible in a glance.
- **Retail-native extras:** monthly-returns heatmap calendar; regime shading bands on price
  charts (trending vs chop, for regime episodes).
- **TradingView layer — meet them on their own screen:** whenever the concept touches price,
  entries, or rules, it appears FIRST on a TradingView chart (bar replay, entry/exit markers —
  their home turf; capture per the TradingView TA Runbook / daily-lane flow), THEN cut to our
  validation graphics for the honest math. TV chart = their world; our graphics = what their
  world isn't showing them.

Rules: dark theme; one highlight color per 2D chart; red→green stays semantic (loss→profit) on
3D surfaces; numbers animate to final value; every axis labeled; every price chart shows
symbol/timeframe/price axis (standing format ruling). Real data from receipt artifacts only —
never illustrative fake curves presented as real.

**Platform doctrine — concept awareness (operator 2026-07-24), not script text:** we meet
traders where they trade — TradingView, MetaTrader, and (watching) Robinhood's LLM-connected
trading. The repo already carries the backend for both (MT5 adapter; Pine-expressible rule
paths). Implication for scripting: taught rules should be *expressible* on the viewer's own
platform — that reproducibility is exactly what the studied channels withhold, and it is our
differentiation. Frame any handed-over rule as a lesson artifact under honest validation, never
a signal or a promise. Machinery stays unnamed on camera (backstage ruling).

**8. Independent critic + operator read-aloud.** Give a separate critic the complete factual
package — promise, capture transcript, final draft, fact pack, strategy passport, working claim
map, and source locators — without the writer's conclusions. The critic checks unsupported or
distorted claims, omitted strategy mechanics, promise/payoff alignment, operator-voice drift,
teaching clarity, and disclosure. Save the findings and their receipt-backed disposition in
`critic-review.md`; receipts outrank both writer and critic.

The operator then reads the entire SPOKEN column aloud in delivery cadence. Fix anything that
does not fit his mouth. An operator edit wins, but it sends the script back through the
information-preservation check and independent critic. Approve the exact final script only after
that loop passes. Record the critic disposition and dated read-aloud approval in
`artifacts/human-facing-review.json`. Do not generate TTS or start a render yet.

**9. Final claims freeze + gates.** Build the episode project's final ontology at
`artifacts/claims.json` from the exact approved spoken text and bind it to that script's SHA-256.
Every rewrite invalidates that hash and requires a rebuilt ontology plus a fresh source-gate
receipt.

The executable JSON contracts are:

- `packaging.json.release`: `privacy`, `category`, boolean `containsSyntheticMedia`,
  `captionLanguage`, and `captionName`. The title remains at top level; description and tags
  remain `_yt_desc.txt` and `_yt_tags.json`.
- `strategy-passport.json`: `schema: strategy-passport/v1`; non-empty `strategy` fields
  `asset_class`, `instrument`, `venue`, `timeframe`, `session_timezone`, `entry`, `exits`,
  `sizing`, `costs`, `parameters`; non-empty `validation` fields `phase`, `test_window`, `settings`,
  `thresholds`, `result`; non-empty `limitations`; and at least one `sources` row with
  `citation`, `locator`, `supports`, and `limitations`.
- `human-facing-review.json`: `schema: human-facing-review/v1`; exact SHA-256 values for
  `script_sha256`, `operator_capture_sha256`, and `strategy_passport_sha256`; PASS
  `protected_items_status` and `disclosure_status`; a named PASS `independent_critic` with
  empty `unresolved_findings`; and a dated APPROVED `operator_read_aloud`.
- `claims.json`: `schema: teaching-claims/v1`; exact `script_sha256`; a `sources` object whose
  entries contain `citation`, `locator`, `supports`, `limitations`, and an artifacts-relative
  evidence `path` plus exact `sha256`; and one `claims` entry for every `# receipt:` ID.
  Factual claims use `academic` or `run_receipt` plus source IDs. Pure delivery lines use
  `delivery`, no source IDs, and a non-empty `why_non_claim`.
- `operator-script-approval.json`: `schema: tradercockpit-series-script-approval/v1`; approved
  `vo.txt` and exact `scriptSha256`; timezone-bearing `reviewedAt`; operator `reviewedBy`;
  `approvalKind: operator`; `operatorReviewed: true`; and true `readAloud`,
  `phrasingATraderWouldSay`, and `factSeparatedFromJudgment` attestations. A writer or worker
  may prepare a candidate but may not issue this receipt.

Manual scrubs (automated style coverage is partial — a clean run is not compliance):
- **Promise check:** read thumbnail + title, then the first 5s of script post-intro. If a viewer
  who clicked would feel baited, the open is rewritten before anything else is polished.
- Never-say table: reviewer corrections ("7 of 7", "only order-dependence", "passes every
  check", "reproducible without product" → "from the spoken track", options critique unscoped).
- Banned-claims grep: win-rate %, "easiest", "guaranteed", urgency. Regex source
  `Series/verify_claims.py` §F. Any hit = blocker.
- Verify every strategy-passport value used in speech against its source locator.

Run the unified source gate from the repository root:

```text
python -B tools/episode_gate.py source <absolute-episode-dir>
```

Only a PASS from that command may unlock TTS, screen capture, composition, or rendering. Delivery split:
teleprompter for teach loops is fine; the demonstration and resolution beats run from beat cards,
not prompter — read delivery kills the register exactly where authenticity is the payload. After
rendering, the operator reviews the exact master and issues
`artifacts/operator-master-approval.json` using
`schema: tradercockpit-series-master-approval/v1`, the project-relative `master`, exact `sha256`,
timezone-bearing reviewer fields, `approvalKind: operator`, `operatorReviewed: true`, and
`publicationAuthorized: false`. The master approval never authorizes upload. Then run the full
gate against that exact master:

```text
python -B tools/episode_gate.py run <absolute-episode-dir> --master <master.mp4>
```

A source receipt never certifies a render.
Publication must go through `tools/upload_youtube.py`, which requires the series lane, checks the
exact certified public values before authentication, inserts the video private, uploads and
downloads the certified caption track for an exact-content check, verifies the custom thumbnail,
and only then promotes to the certified privacy. Copying a master outside its episode does not
carry its certification with it.

**10. After publish — measure, don't guess.** Pull the episode's numbers via
`tools/social_analytics.py`: retention curve (drop at the ident? at 30s? at the first teach
loop?), search impressions, shorts→long click-through. The retention curve decides pacing and
intro changes for the next episode — not taste.

## Series packaging spec (one-time, before E1)

The playlist must read as ONE object. Built once, reused every episode:
- **Title grammar** — one fixed pattern family so episodes are recognizably siblings.
- **Thumbnail template** — one composition system (face/artifact/3-word-max text), consistent
  colors; per-episode content changes, the system never does.
- **The known intro** — the ≤5s ident (visual + audio signature). Design it once, gate it with
  `visual_qa.py`, never tweak it per episode.
Store as `productions/_series/packaging-spec.md` + template assets. Episodes that deviate fail
the promise check by definition.

## Output contract

`productions/series-<nn>-<slug>/`: `fact-pack.md`, `beats.md`, `capture-transcript.txt`,
`script.md` (two-column), `critic-review.md`, `scene-plan.json` (beat → visual binding,
daily-lane format), and `thumbnail-brief.md`. Export the approved `scene-plan.json` to the
episode runtime's canonical `artifacts/scenes.json`; that runtime file may not be edited
independently. Copy the approved operator capture to
`OpenMontage/projects/<episode>/artifacts/operator-capture.txt`; the final
`strategy-passport.json`, `human-facing-review.json`, `claims.json`,
`operator-script-approval.json`, and `operator-master-approval.json` live beside it and are
exact-hash bound by `episode_gate.py`.
Shared, cross-episode: `productions/_series/`
(`packaging-spec.md`, `receipt-library.md`, phrase-bank additions).
Derivatives after approval via `post-approval-derivatives` — each teach loop is a natural short.
