# Helios v27 public-web parity plan — 2026-07-19

Status: operator-authorized plan and implementation. This lane is isolated at
`C:\tmp\tradercockpit-helios-web-parity` on `codex/helios-v27-web-parity`, based on
`a37bf1e2e5a4bc9dfce034b53719594854e13114`. The canonical checkout is read-only.

## Current handoff — 2026-07-19 13:34 ICT

The isolated implementation is verified and review-ready on
`codex/helios-v27-web-parity`. Implementation commit
`81ba261df78a074fdd2ec30a0e83308dbe009a5b` is pushed and draft PR
[#6](https://github.com/javin23863/tradercockpit/pull/6) is open against `main`. The PR is clean and
has no configured status checks. Nothing was merged, deployed, or published, and the canonical dirty
checkout was not mutated.

### Delivered in the isolated worktree

- `docs/index.html`: additive semantic Helios shell with exactly five destinations, claims-safe
  statuses, hash navigation, repeated keyboard navigation, single-view mobile behavior, and preserved
  manifest/waitlist/analytics/gauntlet contracts. Switching a paused or reduced-motion mobile view now
  renders the newly visible canvas immediately.
- `docs/helios-motion.mjs`: one dependency-free fixed-step scheduler for 12 graphic-only canvases,
  deterministic time seeking, bounded desktop/mobile presentation cadence, visibility lifecycle,
  reduced-motion freeze, numeric probes, and five distinct voice morphologies.
- `tools/check_product_manifest.mjs`: existing gates plus semantic geometry, claims, keyboard focus,
  deterministic rendering, temporal/numeric motion contracts, isolated desktop/mobile cadence,
  reduced motion, painted mobile destination, image metrics, and compact Playwright evidence.
- `tests/fixtures/helios-v27-public-web-reference.png`: exact test-only oracle, SHA-256
  `bc872bfb3b819e4e4e10dea3ede784cf5909a58f0d8b4989ea145439c9dcf6d2`. No public file references it.
- `.gitignore`: generated Playwright evidence stays under ignored `output/`.

### Final exercised evidence

| Check | Receipt | State |
|---|---|---|
| Lightweight product/prelaunch gate | `node tools/check_product_manifest.mjs` — product 4/4; prelaunch 3/3 | PASS |
| Browser gate | `node tools/check_product_manifest.mjs --browser` — visual MAE 19.125; desktop 25.91 FPS; mobile 18.04 FPS | PASS |
| Browser evidence gate | `node tools/check_product_manifest.mjs --browser --helios-evidence=output/playwright/helios-web` | PASS |
| Evidence visual metrics | MAE 19.125 ≤ 23; >24-channel 24.868% ≤ 26%; >64-channel 14.931% ≤ 15% | PASS |
| Evidence motion metrics | desktop 22.52 FPS against 22–26.5 bound; mobile 18.05 FPS against 17–20.5 bound | PASS |
| Determinism/lifecycle | repeated t=2 hashes equal; t=2→t=8 changes; five unique voice states; live/pause/resume and hidden/resume | PASS |
| Accessibility/responsive | five keyboard destinations, visible focus, AA faint text, no clipping, 44 px mobile targets, painted mobile Test canvas | PASS |
| Reduced motion/privacy | 12 stable canvas hashes; scheduler stopped; zero pending analytics scripts/cookies | PASS |
| JavaScript syntax | `node --check docs/helios-motion.mjs`; `node --check tools/check_product_manifest.mjs` | PASS |
| Repository suite | `py -m pytest -q` — 61 passed, 17 subtests passed | PASS |
| Diff hygiene | scoped review; `git diff --check`; fixture-reference scan | PASS |

Complete regenerable evidence is in ignored `output/playwright/helios-web`; `metrics.json` SHA-256 is
`8e9ae443a4ecf99df6e60a4237f4993fa52edaffd5ba770ca0befa892345c8e6`. The first repository-suite
run failed only because the isolated worktree lacked the ignored generated
`productions/video-04-iran-regime-v2/build/sections.json`. Hydrating the canonical same-repository
artifact closed the prerequisite; source and destination both hash to
`d869facc1818cf18cc0af0c32d3b75e60097233b2a40a263e8985ad06e27741a`. No test or production code
was changed for that gate.

### Closed implementation gates and honest residual

The original deterministic t=2 failure was fixed without weakening the assertion. A later mobile
capture exposed a blank newly visible Test canvas while the scheduler was paused; the shared view
transition now paints at the held deterministic time, and the browser gate asserts 31,414 painted
pixels in that state. The eruption assertion was also changed from a fixed delay to a bounded
animation-frame poll to remove callback-quantization flakiness without relaxing the state contract.

This is semantic and measured visual parity, not pixel-perfect identity. Residual differences are
primarily claims-safe text and generated solar/detail topology. Operator visual acceptance is still
required; PR #6 must remain draft and must not be merged, deployed, or published before that approval.

### Next safe action

Review PR #6 and the desktop/mobile evidence. If the visual result is accepted, record the exact
operator approval before making the PR ready or initiating any merge/deploy workflow. Otherwise,
continue only with named visual deltas on this isolated branch.

## Ground truth and measured baseline

| Input | SHA-256 | Use |
|---|---|---|
| `Generated image 1 (1).png` | `bc872bfb3b819e4e4e10dea3ede784cf5909a58f0d8b4989ea145439c9dcf6d2` | Authoritative 1536×1024 visual oracle; test fixture only, never a UI backplate |
| `HANDOFF(3).md` | `739a714b89534359c6f714775bc6a1fe3112718bfccfe6408725aae03e58a12f` | v27 runtime/API contract |
| `QA-RESULTS(1).md` | `71ba608aee16807f18b85f4460dd73372a574c87f0553fbf487d9a786685055b` | Supplied QA baseline |
| `helios-animation-test.html` | `3b406f7ecec1f0fb22f6d238b5af36a22526b25f0240c1b8ae5097051f893b54` | Tuned deterministic physics source; never shipped wholesale |
| `helioshandoff-v27-animation-test.zip` | `5019e4b8b5b2efe598b6370a2c995790c3654222618d7018ae08f38529023118` | Read-only source package |

The supplied default parity runtime uses the old reference image as a fixed backplate. That mechanism
is prohibited for this lane. Only its explicit physics, palette, and timing parameters may be ported.
Visible UI must remain semantic HTML; canvases are restricted to graphic fields and contain no text.

Read-only headroom receipt: `154.15 GB` free on C:. Full/default and C:\tmp janitor audits both exceeded
120 seconds; a no-confirm worktree-only janitor preview completed with zero reclaimable items at the
future task path.

Committed public-site baseline at 1536×1024:

- one semantic landing-page chamber, two canvases, no five-destination app shell;
- product manifest verified as `waitlist`, Apollo `concept`, zero verified capabilities;
- prelaunch providers both `pending_operator_account`, so mailto fallback and no analytics are active;
- reference comparison: RGB MAE `26.239/255`, RMSE `53.836/255`, `31.420%` of pixels differ by more
  than 24 in at least one channel, and `17.421%` differ by more than 64;
- existing browser gate closes before launch because the declared Puppeteer package is not installed;
- supplied v27 live observation reached `23.61–26.00 fps` against a 24 fps target at quality `0.78`;
  live/pause/resume and deterministic time 2 → 8 → 2 hashes all behaved correctly.

Reference crops were generated and inspected at 200% for all five desktop destinations, both mobile
views, Apollo copy, motion studies A–E, header, and footer. Additional 400% crops cover status chips,
panel chrome, evidence chips, navigation, Settings controls, motion legends, and footer. Regenerable
captures live under ignored `output/playwright/reference/`.

## Implementation decision

Keep the existing static GitHub Pages stack and public contracts. Build the missing app shell in
`docs/index.html`, place the shared deterministic graphic engine in one dependency-free module,
and extend the existing browser gate rather than introducing a framework or test runner.

Planned scoped files:

- `docs/index.html` — semantic five-destination shell, responsive states, existing waitlist/claim copy,
  manifest integration, keyboard/focus behavior, and below-fold explanatory content;
- `docs/helios-motion.mjs` — seeded fixed-step particle/solar/orbit/wave/quantile/voice graphics only;
- `tools/check_product_manifest.mjs` — preserve current manifest/waitlist checks and add app geometry,
  semantics, reduced-motion, deterministic-motion, temporal, and performance assertions;
- `tests/fixtures/helios-v27-public-web-reference.png` — exact oracle for local evidence only;
- this handoff and the authoritative vault note — dated plan, receipts, residuals, and final state.

No framework, paid service, product capability, telemetry feed, broker connection, microphone access,
or new runtime dependency will be added. The already-declared Puppeteer lock may be installed locally
to exercise the repository's own browser gate; `node_modules` remains unversioned.

## Visual and interaction parity matrix

Reference coordinates are in the 1536×1024 oracle. Bounds tolerate anti-aliasing but not structural
drift. “Claims-safe copy” means reference wording is replaced where it would assert an unavailable
capability; the geometry, hierarchy, and color role remain the target.

| Region / interaction | Reference and current implementation | Measured gap | Owner | Verification | Acceptance threshold |
|---|---|---|---|---|---|
| Global header | Oracle y=0–64: left Trader Cockpit/Apollo, centered Helios title/subtitle, two right chips. Current page has a centered marketing hero. | Structure absent. Reference chip claims are unsupported. | `docs/index.html` | 1536 screenshot + DOM/rect audit | Three header zones present; center error ≤4 px; chips keyboard-readable; claims-safe copy |
| Header status chips | Green evidence and violet Apollo pills, compact icon/title/subtitle. Current has one orange simulation tag. | Form and hierarchy absent. | `docs/index.html` | 400% crop + computed styles | Two 1 px outlined chips; radius, gap, and two-line hierarchy within 6 px; no unsupported “active/verified” claim |
| Home / Apollo | x=8–362, y=64–473: hero core, four orbit nodes, message, four evidence chips, five-item nav. Current Apollo is one wide canvas/copy row. | Layout absent; current solar renderer is an orange ball with arbitrary orbit glow. | `docs/index.html`, `docs/helios-motion.mjs` | region crop, DOM snapshot, pointer/keyboard checks | Panel rect within 4 px; all labels DOM text; solar graphic fills 52–62% panel width; eruption and voice preview remain functional |
| Test / Particle Genesis | x=371–656, y=64–473: five phases, converging particle field, registry, evidence cards, nav. Current strategy chips feed a simulated 12-phase gauntlet below the hero. | Destination and staged field absent. | same | crop, phase clicks, deterministic t=2/8 captures | Panel rect within 4 px; phase selection works; active state visible; ≥4 visually distinct aggregation stages; no canvas text |
| Strategies / Knowledge Atlas | x=663–949, y=64–473: provenance graph, central core, five strategy cards, nav. Current has strategy chips only. | Graph/destination absent. | same | crop, semantic graph labels, keyboard nav | Seven graph nodes in DOM; core-to-node couriers remain inside graph ROI; selected card/focus visible; copy remains concept-qualified |
| Live / Execution Eligibility | x=957–1211, y=64–473: concentric eligibility rails, eight nodes, kill switch, status, nav. Current has no destination. | Entire region absent; oracle live/certified copy conflicts with waitlist manifest. | same | crop, manifest fallback test, DOM assertions | Geometry within 4 px; rails/courier animate; all availability reads unavailable/not connected unless manifest verifies it; no arming control |
| Settings / System Constellation | x=1217–1520, y=64–473: nine-node constellation, controls, nav. Current has no destination. | Entire region absent; several oracle statuses are unsupported. | same | crop, control focus/order, reduced-motion toggle | Geometry within 4 px; controls are real buttons or disclosures; no credential/config mutation; claims-safe statuses |
| Mobile Home | Oracle phone x=687–922, y=488–751. Current 390×844 stacks a marketing hero and chamber. | App state absent; mobile is vertically oversized. | `docs/index.html` | 390×844 screenshot, overflow audit, touch nav | One active destination; no horizontal overflow; header/core/message/status/nav visible in first 844 px; targets ≥44 px |
| Mobile Test | Oracle phone x=949–1196, y=488–751. Current has no separate Test screen. | State absent. | same | click Test at 390×844, screenshot, phase keyboard/touch | Test title, phases, particle field, registry, cards, nav visible; no clipped focus ring; targets ≥44 px |
| Apollo explainer | Oracle x=1217–1522, y=488–751. Current claim-safe Apollo copy exists in the hero. | Visual hierarchy differs; oracle monitoring/execution claims are unsupported. | same | DOM text/contrast audit | Five benefit rows preserve icon/color hierarchy but use concept/guardrail language; WCAG AA text contrast |
| Global navigation | Five labeled destinations repeat in desktop panels and mobile footer. Current page has no product navigation. | Absent. | same | Playwright snapshot, click/keyboard traversal | Exactly five destinations; selected state uses `aria-current`; URL hash deep-links; all views reachable without pointer |
| Footer | Oracle y=955–1024: five compact trust principles. Current footer is a claims warning and boundary link. | Visual form differs; current legal language must remain. | same | 400% crop + link audit | Five visual principles plus preserved no-advice/no-performance and boundary link; all text semantic; no overflow |
| Borders, type, spacing | Oracle: #010101 background, warm 1 px hairlines, 8–12 px radii, wide uppercase tracking, compact labels. Current red/pink palette and large mono headline. | Global design system mismatch. | same | CSS token audit + screenshots | Declared tokens; panel gaps/rects within 4 px at 1536; no font/network dependency; readable ≥11 px public copy |
| Iconography | Oracle uses thin outline icons. Current uses text/symbols and canvas marks. | Inconsistent and sometimes decorative text. | same | DOM/accessibility snapshot | Inline SVG or CSS-native icons, `aria-hidden` when decorative; no icon font/dependency; focus labels remain text |
| Color, glow, noise | Oracle uses ember/orange/gold, sparse magenta/blue, green verification, near-black surfaces, structural glow/noise. Current uses magenta/red with broad gradients. | Palette and energy topology mismatch. | same + motion module | pixel metrics, ROI histograms, 200% crops | Full-frame RGB MAE ≤23.0; >24-channel diff ≤26%; >64-channel diff ≤15%; additive motion remains inside graphic ROIs |
| Waitlist and manifest | Current same-origin manifest validation, mailto fallback, Buttondown activation, UTM capture, support link. | Must survive shell redesign unchanged. | `docs/index.html`, existing modules | existing browser gate in valid/missing/malformed/unsupported and active waitlist modes | Existing assertions all pass; fallback remains non-transactional; zero inferred capability/pricing/platform fields |
| Consent and analytics | Current Plausible is injected only from an active allowlisted config; pending state loads nothing. | No visual gap; regression risk. | existing module + gate | network/DOM audit | Pending config makes no analytics request/cookie; active test uses only allowlisted HTTPS Plausible snippet |
| Strategy simulation | Current seeded illustration, explicit confirmation, cancellation, receipt, no verdict. | Must be reachable from Test without becoming a capability claim. | `docs/index.html` | existing selection/confirm/cancel/run assertions | Explicit confirmation retains focus handoff; output remains “simulation only”; no market-data/performance claim |
| Keyboard/focus/accessibility | Current core, chips, confirmation, voice preview are keyboard accessible; canvas is labelled. | Five-view focus/order and hidden-view semantics are new. | same | Tab/Enter/Space checks + snapshot | One h1; landmarks present; inactive views `hidden`; focus never enters hidden content; visible 2 px focus indicator |
| Reduced motion | Current page follows OS and freezes Apollo; supplied test overrides OS unless query-forced. | New multiple canvases need one public fail-closed policy. | motion module + gate | emulate reduce, hash twice 350 ms apart | No animation loop; identical hashes; deterministic living frame at t=12; all navigation/interactions still work |

## Motion parity matrix and explicit parameters

All renderers use a seeded clock and a fixed `1/60 s` simulation step. Presentation is frame-gated,
not simulation-gated, so fixed-time captures remain identical across desktop and mobile.

| System | Supplied measured behavior / current gap | Ported explicit contract | Verification / threshold |
|---|---|---|---|
| Solar filament flow | Current public sun is an opaque radial ball. v27 uses 7–13 seeded spiral filaments/core, current knots, asymmetric prominences, sparse ejecta, magenta/blue S-channel, low pointer parallax. | 13 hero filaments; 7–10 secondary; angular drift 0.014–0.031 rad/s; internal wave 8–15 cycles; prominence drift 0.006–0.014 rad/s; pulse 0.72–0.97 rad/s; pointer offset ≤1.4 px x / 1.1 px y. | Same-time canvas hash exact; t2/t8 differ; core radius changes ≤12%; no energy pixels outside each declared graphic ROI |
| Particle Genesis | v27 native physics: 320 desktop stage particles, 150 phone; triangular births; vx/vy ±0.01; age rate `0.44/lifetimeScale`, lifetimeScale 0.55–1.30; curl forces 0.010; drag `exp(-1.7dt)`; stages at age .28/.62/.88; guidance .026/.14/.17/.24; three fading trail points. Current public page has no genesis field. | Preserve those values; render 320 desktop / 150 mobile; fixed seed; explicit respawn fade; capture/accretion at core radius ×0.72; no teleport. | Birth x within first 20% and triangular y; lifetime 1.25–2.95 s from normalized age; spread at final quartile ≤45% of birth spread; ≥95% finite particles; t2→t8 changed-pixel ratio 0.5–35% inside ROI |
| Chronosphere | v27 overlay has seven shells, radii `54+i×16.8`, y radii `24+i×4.5`, alternating couriers, phase speeds 0.32–0.47 rad/s, dash drift 7–10.6 px/s. Current page absent. | Preserve seven shells, warm→green/cyan→blue/violet order, alternating direction, precession amplitude ≤0.006 rad at 0.08 rad/s. | Seven DOM legend bands and seven couriers; shell ordering invariant at t0/t2/t8/t12; each courier advances and stays within 2 px of its ellipse |
| Correlation gravity field | v27 has six fronts/side, left 0.075 cycles/s and right 0.070 with phase offset .08, radius 18→163, green/blue convergence, five truth sparks. Current absent. | Preserve counts, directions, phase offset, 0.07–0.30 alpha envelope, dash drift 7 px/s, labels as DOM. | Six fronts per side; median radial displacement over 1 s >8 px toward center; center sparks remain within ±5 px; labels never animate |
| Probability corona | v27 has seven ordered quantiles, colors orange→hot→green→blue→violet, span 33 px right / 18 px left, exponent 1.28, wave frequency 8.8, temporal 0.42–0.528 rad/s, packet speed 0.055–0.070 cycles/s. Current absent. | Preserve ordering and mirrored bands; median index 3, line width 1.0 vs 0.68; pulsation amplitude `1.4+4u`; one packet/band. | For 43 sampled u values, quantile ordering has zero crossings; seven separable colors; packet progress changes at t2/t8; median luminance ≥1.25× adjacent-band mean |
| Voice states | Current public page exposes listening/thinking/previewing/confirming/running/speaking but one generic sun. v27 supplies five distinct morphologies. | Listening cool receptive sweep/inbound motes; reasoning two counter-rotating ellipses/three couriers; retrieving locator orbit/packet/reaching filament; speaking three outward pulse rings/bilateral jets; interrupted broken red hold ring/shutter. | Five buttons expose state in DOM; per-state fixed-time hashes all unique; reduced-motion state changes repaint once; state names announced via `aria-live` |
| Execution and constellation orbits | Current absent. v27 has two counter-rotating live rails, one packet, eight checkpoints, and core-to-node couriers. | Preserve two rails, 0.38 rad/s outer packet, eight independent pulses, and seeded 0.055–0.067 cycles/s couriers. | Packet advances ≥15°/s and remains on rail; eight checkpoints; couriers stay inside graph ROI; no false availability state |
| Scheduler / performance | Supplied v27 target 24 fps at 0.78 scale; observed 23.61–26.00 fps desktop. | One shared rAF scheduler, fixed simulation step, cached glow sprites, manual two-pass glow, internal render scale 0.70 desktop / 0.65 mobile; 24 fps desktop, 18 fps mobile. | Desktop measured fps ≥22 and p95 frame interval ≤66.7 ms; mobile ≥17 and p95 ≤75 ms; render p95 ≤20 ms; long-frame (>100 ms) ratio ≤2%; hidden tab pauses |

## Evidence and completion contract

Version only the oracle, scripts, compact JSON metrics, selected final screenshots/diffs, and the
residual ledger. Keep exploratory crops, traces, full temporal sequences, and node modules ignored in
`output/playwright/`.

Required final fixtures:

1. 1536×1024 desktop full render and region crops for Home/Test/Strategies/Live/Settings.
2. 390×844 mobile Home and Test renders.
3. fixed-time t=0/2/8/12 graphic frames; repeat t=2 hash; live/pause/resume sequence.
4. overlay and heatmap against the exact oracle, plus machine-readable global/region metrics.
5. manifest fallback/active waitlist, pending analytics, keyboard, focus, reduced-motion, and hidden-tab checks.
6. desktop/mobile rAF cadence metrics.

No “100%”, “pixel perfect”, or “done” claim is permitted unless every threshold above closes. A
semantic responsive implementation may retain honest anti-aliasing and claims-safe text residuals;
those must be listed by region with measured values. The delivery boundary is commit, push, and draft
PR only—no merge, deploy, publish, schedule, upload, or public-surface mutation.
