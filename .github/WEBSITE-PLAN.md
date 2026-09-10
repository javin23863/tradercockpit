# TraderCockpit Public Website Plan

Status: **Phase A complete / Phase B visual depth in progress**
Repository: `javin23863/tradercockpit`
Publishing boundary: GitHub Pages from `docs/`
Last adversarial review: 2026-09-10

## 1. Goal

Build a public TraderCockpit website that feels like an explorable quantitative-research environment rather than a conventional SaaS brochure. The site must combine marketing, education, documentation, how-to/video learning, research-method explanations, examples, and contextual in-app help without overstating product capability.

The visual identity should use meaningful depth and motion to explain uncertainty, selection, distributions, regimes, correlations, drawdowns, robustness, and validation. Decorative 3D is not enough: every significant visual encoding must have a defined analytical meaning or be clearly marked as atmosphere.

## 2. Repository and truth boundaries

These are non-negotiable:

1. Keep public website assets under `docs/` and governance material under `.github/` so the public-surface allowlist remains satisfied.
2. `docs/product-manifest.v1.json` remains the sole authority for product availability, verified capabilities, platform support, pricing/checkout state, and commercial CTA state.
3. Current manifest state is treated as a waitlist/prelaunch boundary. New educational pages must not imply that a research concept is already a verified TraderCockpit feature.
4. No performance promises, guaranteed edge, investment advice, or misleading backtest claims.
5. Public research demonstrations use clearly labeled synthetic/illustrative data unless a specific publishable dataset has been approved.
6. Never publish secrets, proprietary backend architecture, private research datasets, unreleased UI contracts, private roadmaps, credentials, or internal operational details in this public repository.
7. First implementation is additive. Do not replace the current landing page or waitlist path until the new experience passes acceptance review.
8. GitHub Pages is the current delivery target. Core pages must function as a static site with progressive enhancement.

## 3. Site concept: an explorable Quant Universe

The website is an explorable visual map of quantitative research.

- **Home** creates curiosity and explains the public product state.
- **Research Lab** makes quantitative ideas interactive.
- **Learn** structures education.
- **Docs** answers exact product/reference questions when verified.
- **Methods** explains the mathematics and research logic independently of product UI.
- **Examples** shows end-to-end research stories with synthetic or explicitly publishable data.
- **Updates** communicates public changes without exposing a private roadmap.
- **Contextual help** lets the application deep-link to exact public explanations through stable help IDs.

## 4. Information architecture

### Primary navigation target

- Home / Product
- Research Lab
- Learn
- Docs
- Methods
- Examples
- Updates

Persistent utilities when implemented:

- Search
- Support
- Manifest-authorized CTA

Pricing, Download, Buy, Trial, checkout, or platform claims are shown only when authorized by `product-manifest.v1.json`.

### Research Lab

Purpose: memorable, public-safe demonstrations of quantitative research concepts using synthetic data.

Planned modules:

- Strategy Universe
- Monte Carlo probability paths
- Out-of-sample boundary
- Walk-forward windows
- Parameter robustness surface
- Drawdown landscape
- Correlation network
- Distribution explorer
- Regime map
- Selection funnel

Each module must contain:

- What the visitor is seeing
- What each visual dimension encodes
- Why the concept matters
- What can mislead the researcher
- Related Methods material
- Related How-To/Docs only when those product instructions are verified
- Synthetic/illustrative-data disclosure

### Learn

Subsections:

- Start Here
- Concepts
- Academy
- How-Tos
- Videos
- Visual Atlas / glossary

### Docs

Purpose: exact product reference, not general education.

Public-safe target taxonomy:

- Getting Started
- Navigation and workspace conventions
- Visual analysis reference
- Validation/reference concepts that are verified for public documentation
- Settings
- Troubleshooting
- Errors/recovery
- Reference

The detailed product-specific documentation tree is maintained with the private product implementation until individual areas are approved for public disclosure.

**Publication gate:** a product-specific page may be drafted privately elsewhere, but this public repository only publishes behavior that is already safe and verified for public disclosure. Until then, public Docs may explain the documentation system and link to public-safe concepts without presenting unreleased controls as shipped behavior.

### Methods

Purpose: explain quantitative research principles independently from UI instructions.

Initial topics:

- In-sample vs out-of-sample
- Walk-forward analysis
- Monte Carlo methods
- Parameter robustness
- Time-series cross-validation
- Selection bias and multiple testing
- Probability of Backtest Overfitting (PBO)
- Deflated Sharpe Ratio (DSR)
- Costs and slippage
- Drawdown and tail risk
- Correlation and diversification
- Calibration and model evaluation

### Examples

Purpose: end-to-end public research stories built only from synthetic or explicitly publishable evidence.

Standard structure:

1. Research question
2. Setup
3. Evidence
4. Validation
5. Interpretation
6. Limitations
7. Next research question

### Updates

- Release notes for public releases
- Public availability/status changes
- Publicly announced milestones only

Private planning remains outside this public site.

## 5. Signature visual system

### Strategy Universe

The signature scene is a spatial research universe rendered from deterministic synthetic points.

Analytical encoding must be stated adjacent to the scene. Candidate mappings include:

- x/y/z position = explicitly named synthetic analytical dimensions
- distance = similarity only when the demo actually computes similarity
- size = explicitly named magnitude
- transparency = uncertainty or evidence strength only when calculated in the demo
- connections = defined relationships
- motion = state change across an illustrative test
- filtering = rejection under an explicitly stated synthetic rule

The implementation must not use vague visual semantics such as “higher = better” without defining the variable.

### Homepage scroll narrative

Target sequence after the additive Research Lab milestone is accepted:

1. Research universe
2. Candidate selection
3. Validation pressure
4. Uncertainty/distribution view
5. Interpretation
6. Repeatable workflow
7. Current product state and manifest-authorized CTA

No homepage replacement occurs during the first additive milestone.

## 6. Contextual help contract

A public versioned registry will live at `docs/help-registry.v1.json`.

Example public-safe IDs:

- `research.strategy-universe`
- `research.monte-carlo`
- `research.walk-forward`
- `research.out-of-sample`
- `research.parameter-robustness`
- `research.drawdown`
- `research.correlation`

Each entry contains:

- `id`
- `path`
- `title`
- `kind` (`concept`, `method`, `how-to`, `reference`, `troubleshooting`)
- `status`
- `aliases`

Rules:

1. Help IDs are stable public contracts once released.
2. The public registry contains public-safe knowledge topics only. Unreleased UI control names, private routes, internal identifiers, and backend implementation details remain outside this repository.
3. Paths resolve to real public pages or anchors.
4. The desktop application may later maintain a private mapping from controls to these public knowledge IDs.
5. Public IDs may explain concepts before a product capability exists, but the content must never claim that the capability is shipped unless manifest-authorized.

## 7. Technical architecture

Phase 1 is dependency-light and static:

- semantic HTML
- shared CSS under `docs/assets/`
- progressive-enhancement JavaScript under `docs/assets/`
- Canvas/SVG/CSS transforms for quantitative visuals
- JSON registries for product truth and help routing
- GitHub Pages hosting

No mandatory WebGL or large 3D framework is required for the first paint.

### Progressive-enhancement tiers

**Tier 0 — no JavaScript / assistive technology**

- all navigation works
- all educational content is readable
- every visual has a textual equivalent

**Tier 1 — standard JavaScript**

- deterministic Canvas/SVG diagrams
- keyboard-accessible controls
- no dependency on GPU-specific features

**Tier 2 — optional advanced depth later**

- richer WebGL/3D only if measured performance and accessibility remain acceptable
- automatic fallback to Tier 1/0

## 8. Content model

### Concept / Method page

1. What is it?
2. What research question does it answer?
3. What does the visualization encode?
4. What assumptions matter?
5. What can mislead you?
6. What should you inspect next?
7. Related methods
8. Related verified product help, when available

### How-To page

1. Goal
2. Prerequisites
3. Steps
4. Expected state/result
5. Common mistakes
6. Troubleshooting
7. Related concepts
8. Video when available

### Reference page

1. Control/field name
2. Exact meaning
3. Allowed values/defaults when verified
4. Effects
5. Validation/errors
6. Related help IDs

## 9. Search, video, analytics, and privacy

### Search

Start with a static, local search index. Do not send documentation queries to a third party merely to provide site search.

### Video

Video lessons use a click-to-load pattern. Do not eagerly load third-party video embeds on every page. A written learning path must remain available without video.

### Analytics

Use the existing prelaunch analytics configuration as authority. Do not silently introduce a new tracker.

Allowed future event classes may include page/module/help opens and CTA interaction. Do **not** log user-entered strategy parameters, research values, queries containing private research content, or other sensitive research payloads as analytics dimensions.

## 10. Accessibility and performance requirements

Required behavior:

- keyboard-operable controls
- visible focus states
- semantic headings and landmarks
- adjacent text alternative for Canvas/SVG information
- `prefers-reduced-motion` support
- important meaning not encoded only by color or motion
- touch-friendly controls
- responsive layouts at narrow widths and zoom
- useful no-JavaScript fallback

Initial performance rules:

- useful text paints before advanced visuals initialize
- no mandatory heavy 3D dependency
- below-fold scenes lazy-initialize
- animation pauses while the page is hidden
- avoid unbounded full-screen rendering loops
- reserve layout space to reduce content shift
- images use dimensions/aspect ratios
- videos do not autoplay-download large payloads

## 11. Implementation phases

### Phase 0 — plan and adversarial review

- create this in-repo plan
- review it against the live repository boundary and manifest
- correct high/medium findings before website code

### Phase A — additive foundation

- shared visual tokens/styles for new pages
- shared navigation/footer pattern
- public-safe help registry
- Research Lab landing page
- Strategy Universe interactive scene
- optional second lightweight research visualization
- Docs landing page
- Learn landing page
- How-To/Academy landing page
- Methods landing page
- Examples landing page
- Updates landing page
- reduced-motion/responsive foundations

### Phase B — Research Lab depth

- Monte Carlo explorer
- robustness surface
- correlation network
- distribution explorer
- accessible legends/fallbacks
- per-module deep links

### Phase B progress checklist

- [x] Existing Monte Carlo path field remains interactive and synthetic.
- [x] Parameter-robustness surface compares broad plateau, narrow spike, and ridge geometry.
- [x] Correlation network exposes labeled families, relationship strength, node selection, and focus mode.
- [x] Distribution explorer compares symmetric, skewed, and heavy-tail synthetic families with a keyboard-operable threshold.
- [x] New Phase B modules have adjacent legends and written interpretation/fallback text.
- [x] Direct hash links initialize lazy visuals and land below the sticky navigation.
- [x] Expanded Research Lab passes 320px reflow and 200% text-size stress.
- [ ] Build the walk-forward landscape.
- [ ] Build the explicit in-sample/out-of-sample boundary visualization.
- [ ] Build drawdown-valley path visualization.
- [ ] Build the selection/multiple-testing funnel.
### Phase C — documentation system

- durable docs taxonomy
- concept template
- method template
- how-to template
- reference template
- client-side search index
- initial high-value public-safe concept pages
- help-ID resolver validation

### Phase D — homepage integration

Only after Phase A/B acceptance:

- replace legacy/decorative hero behavior with the accepted Strategy Universe narrative
- connect homepage to Research Lab, Learn, Docs, Methods, Examples
- preserve manifest-driven CTA behavior
- preserve waitlist/prelaunch behavior until manifest state changes
- update metadata, sitemap, and internal navigation

### Phase E — Academy and examples

- structured Academy learning paths
- click-to-load video lesson template
- first end-to-end synthetic research example
- cross-links between video, concepts, methods, and help IDs

### Phase F — hardening

- browser/device review
- accessibility review
- keyboard-only review
- reduced-motion review
- performance profiling
- SEO/canonical/sitemap review
- broken-link/deep-link validation
- public-disclosure audit
- product-claim audit against manifest

## 12. Adversarial review — 2026-09-10

The first draft was reviewed as though an external reviewer were trying to find ways the plan could create commercial, technical, accessibility, or disclosure problems.

| Severity | Finding | Correction in this revision |
|---|---|---|
| High | Planned Product/Docs pages could accidentally advertise unverified capabilities. | Added manifest publication gates, removed unreleased product-specific taxonomy from the public plan/site, and separated public concepts from verified product reference. |
| High | A public help registry could leak unreleased controls/routes/internal names. | Registry is restricted to public-safe knowledge IDs; private control-to-help mapping stays outside this repo. |
| High | “3D-first” could harm mobile performance, accessibility, reduced-motion users, and no-GPU environments. | Added progressive-enhancement tiers; first milestone uses Canvas/SVG/CSS and must have Tier 0 fallback. |
| High | Replacing the existing homepage during initial work could disrupt the current waitlist/CTA flow. | First milestone is additive; homepage replacement moved behind Phase A/B acceptance. |
| High | Visual “survivors” could be read as profitable or endorsed strategies. | Visual semantics now require explicit synthetic variables/rules and neutral interpretation. |
| Medium | Third-party site search could leak documentation/research queries. | Initial search is local/static only. |
| Medium | Eager video embeds could create tracking/performance problems. | Added click-to-load video requirement and non-video fallback. |
| Medium | Analytics could capture research parameter values or private user intent. | Explicitly prohibited research payloads/parameters as analytics dimensions. |
| Medium | Public roadmap language risked disclosing internal plans. | Updates now contain public releases/status/announcements only. |
| Medium | Help URLs could become brittle on static GitHub Pages. | Registry uses versioned IDs and real static pages/anchors; IDs remain stable while paths can be migrated deliberately. |
| Medium | Visual encodings such as distance/density/transparency were underspecified. | Added requirement that every analytical visual dimension name the variable or rule it encodes. |
| Medium | Site could become animation-heavy while still saying little. | Every module now requires explanatory text, assumptions, failure modes, and next concepts. |

**Adversarial review result:** no unresolved high-severity plan findings. Remaining medium-risk items are implementation acceptance checks rather than plan blockers.


## 12A. Adversarial implementation review — 2026-09-10

The additive implementation slice was reviewed against this plan before any homepage integration.

| Severity | Finding | Resolution |
|---|---|---|
| High | The first public Docs scaffold named unreleased product-specific areas even though the canonical manifest currently exposes no verified capabilities. | Removed product-specific taxonomy from the public Docs page and public plan. Detailed product documentation remains private until approved for disclosure. |
| Medium | The first Strategy Universe draft represented a synthetic drawdown coordinate on a −1 to +1 scale, which could imply negative drawdown severity. | Public readout and legend now use normalized 0–1 synthetic scores; centering to −1..+1 happens only internally for projection. |
| Medium | The first animation loop still scheduled drawing while the document was hidden. | Visibility handling now cancels the animation frame while hidden and restarts it on return. |
| Medium | A future manifest-backed Updates page could become an injection surface if manifest strings were inserted as HTML. | Manifest values are rendered with DOM `textContent`, never `innerHTML`. |
| Medium | A broad integrity check across all legacy pages would create unrelated failures and discourage enforcement. | The new integrity checker is intentionally scoped to the additive architecture plus its links into required existing files. |
| Medium | Initial narrow-screen browser capture exposed a mobile min-content/navigation risk. | Added `min-width: 0` to hero grid children, allowed the long eyebrow to wrap, and changed mobile navigation from hidden horizontal overflow to visible wrapping; a true 390px Puppeteer viewport then reported `scrollWidth == innerWidth`. |
| Medium | Browser console review exposed a default `/favicon.ico` 404 on every new page. | Added a zero-payload data-URI favicon declaration so the additive pages remain console-clean without introducing another public asset request. |

**Implementation review result:** no unresolved high-severity findings in the additive slice. Windows Edge/Puppeteer acceptance now passes for all seven new pages at 1440px and 390px, including no horizontal overflow or console errors. Keyboard candidate traversal, Monte Carlo regeneration, reduced-motion behavior, and no-JavaScript Docs navigation were exercised. The existing homepage remains untouched because Phase D is intentionally later than the additive foundation.

## 12B. Foundation completion review — 2026-09-10

The three deferred Phase A acceptance items were implemented and adversarially exercised before being marked complete.

| Severity | Finding | Resolution |
|---|---|---|
| High | Documentation search could leak research/help queries to a third-party search service or analytics endpoint. | Added a versioned same-origin static search index and client-only ranking. Browser interception confirmed search makes no third-party requests; result text is created with DOM `textContent`. |
| High | Video embeds could contact YouTube on page load even when the user only wanted written instructions. | The Academy ships no iframe in initial HTML. A privacy-enhanced `youtube-nocookie.com` player is created only after the explicit Load video action, while the written Method link remains primary. |
| Medium | The first responsive video frame used a minimum height together with `aspect-ratio`, creating an intrinsic width wider than a 320px viewport. | Removed the minimum-height width pressure and constrained grid children with `min-width: 0`; 320px reflow now passes on all seven additive pages. |
| Medium | A scripted HTML edit briefly inserted literal backtick-newline characters beside new script tags. | Detected during source inspection before commit, normalized to real line breaks, and revalidated through HTML/browser checks. |
| Medium | Narrow-screen acceptance alone did not prove resilience under enlarged text. | Added a seven-page 200% text-size stress pass at a 640px viewport; no horizontal overflow or console errors remain. |

**Foundation completion result:** all Phase A acceptance items are now evidence-backed. Local search covers 18 public-safe destinations, the first Academy video is optional and click-to-load, and browser acceptance passes for 320px reflow and 200% text enlargement across every additive page. The legacy homepage remains outside this change set.
## 12C. Phase B visual-depth review — 2026-09-10

The first Research Lab depth slice was reviewed for misleading quantitative semantics, inaccessible state, deep-link failures, and responsive defects.

| Severity | Finding | Resolution |
|---|---|---|
| High | A visually rich surface/network/distribution could be mistaken for live product output or market evidence. | Every new module is deterministic synthetic education, explicitly names its visual encodings, links to method limitations, and avoids product-availability claims. |
| Medium | Long synthetic-status badges forced correlation/distribution panels wider than 320px and failed the 200% text stress case. | Mobile visual headers now stack and badges wrap; the expanded Research Lab passes both reflow tests. |
| Medium | Sticky navigation could cover the heading reached by an in-app/deep help link. | Added scroll margins for visual section targets; direct 390px hash-navigation tests land all three sections below the sticky nav. |
| Medium | The correlation focus toggle changed its visible label while also using `aria-pressed`, making the toggle state harder to interpret. | Kept the control label stable as “Focus selected”; `aria-pressed` alone carries the toggle state. |
| Medium | A standardized heavy-tail sample could have a less-negative 5th percentile than the symmetric sample, making the chosen tail summary visually counterintuitive. | Changed the summary to the 1st percentile and added an acceptance assertion that the current deterministic heavy-tail sample exposes the farther lower tail. |
| Medium | Lazy initialization could leave a deep-linked module blank if the observer missed a hash jump. | Direct links to robustness, correlation, and distribution were exercised independently; each initializes its metric and canvas without console errors. |

**Phase B review result:** no unresolved high-severity findings in this slice. Surface-mode switching, network selection/focus, keyboard threshold adjustment, direct hash navigation, 320px reflow, and 200% text stress pass in Windows Edge/Puppeteer.
## 13. Acceptance checklist

### Governance / truth

- [x] All new public files stay inside the repository allowlist.
- [x] No secrets, proprietary backend internals, private roadmap material, unreleased UI contracts, or private datasets are published.
- [x] Product claims are checked against `product-manifest.v1.json`.
- [x] Pricing/download/checkout UI is absent unless manifest-authorized.
- [x] Concept demos are visibly labeled illustrative/synthetic.
- [x] No performance promises or implied guaranteed edge.
- [x] Existing waitlist/prelaunch path remains intact through the additive milestone.

### Information architecture

- [x] New-page navigation exposes Research Lab, Learn, Docs, Methods, Examples, and Updates.
- [x] Docs, Learn, Methods, and How-Tos are visibly distinct information types.
- [x] Every new landing page has a clear next path rather than a dead end.
- [x] Mobile navigation is usable without horizontal overflow.
- [x] No navigation item points at an unpublished/broken target.

### Research Lab / visuals

- [x] Strategy Universe has an explicit encoding legend.
- [x] At least one interactive research scene uses deterministic synthetic data.
- [x] Every scene remains understandable without animation.
- [x] Every scene has adjacent textual explanation/fallback.
- [x] Visual depth supports analytical meaning rather than only decoration.
- [x] Pointer-only interactions are nonessential or have keyboard/touch equivalents.
- [x] Continuous animation respects reduced motion and page visibility.

### Docs / contextual help

- [x] `help-registry.v1.json` exists and parses as JSON.
- [x] Help IDs are unique and public-safe.
- [x] Each released help entry resolves to a real public page/anchor.
- [x] Registry exposes no private UI routes/control IDs.
- [x] Docs landing page clearly distinguishes reference from concept education.
- [x] Deep links are stable enough for future application use.

### Academy / video

- [x] Academy/How-To area uses structured learning paths rather than a thumbnail dump.
- [x] Video slots are click-to-load/lazy by design.
- [x] Written context remains available without video.

### Accessibility

- [x] Keyboard navigation works for every essential interactive control.
- [x] Focus indicators are visible.
- [x] Heading order and landmarks are semantic.
- [x] Reduced-motion mode removes nonessential continuous motion.
- [x] Important meaning is not color-only.
- [x] Text remains readable at narrow widths and zoom.
- [x] Canvas/SVG scenes have adjacent textual equivalents.

### Performance / resilience

- [x] Useful content paints before advanced visuals initialize.
- [x] No mandatory heavy 3D dependency blocks first load.
- [x] Rendering pauses when the document is hidden.
- [x] Site remains navigable with JavaScript disabled.
- [x] Research visuals fail gracefully if Canvas is unavailable.
- [x] No eager third-party video payload on landing pages.

### Privacy

- [x] No new tracker is introduced outside existing analytics configuration.
- [x] Search remains local/static in the first implementation.
- [x] Analytics design excludes strategy parameters/research payloads.

### SEO / discoverability

- [x] Each new public page has a unique title and description.
- [x] Canonical URLs are correct before pages are linked from the homepage/sitemap.
- [x] Research visuals have indexable explanatory text.
- [x] Concepts use durable human-readable anchors/URLs.
- [x] Internal links connect related learning material.

### Validation before homepage integration

- [x] Public-surface allowlist check passes.
- [x] Product-claim audit passes.
- [x] JSON registries parse successfully.
- [x] Internal links and registered anchors resolve.
- [x] JavaScript syntax check passes.
- [x] No obvious HTML parsing errors in new pages.
- [x] Desktop layout review passes.
- [x] Mobile layout review passes.
- [x] Keyboard-only review passes.
- [x] Reduced-motion review passes.
- [x] Adversarial implementation review has no unresolved high-severity findings.

## 14. First milestone definition of done

The additive first milestone is complete when:

1. this reviewed plan is committed in-repo;
2. a shared visual foundation exists for new pages;
3. Research Lab is a real navigable page;
4. Strategy Universe works with deterministic synthetic data, explicit visual semantics, reduced-motion behavior, and text fallback;
5. at least one additional lightweight quantitative visual is present or the Research Lab clearly scaffolds the next module;
6. Docs, Learn, How-To, Methods, Examples, and Updates landing pages exist without unverified product claims;
7. a versioned help registry resolves stable public-safe help IDs to real pages/anchors;
8. focused validation of JSON, links, JavaScript, static-page parsing, reduced motion, and public-surface boundaries passes;
9. the existing homepage/waitlist remains unchanged until this additive milestone is reviewed.

## 15. Implementation log

- 2026-09-10: Initial plan drafted against live repository README, allowlist, product manifest, prelaunch config, and current landing-page structure.
- 2026-09-10: Adversarial plan review completed; 5 high and 7 medium findings corrected before website implementation.
- 2026-09-10: Phase A implementation started in an additive staging tree; homepage intentionally untouched.
- 2026-09-10: Adversarial implementation review removed unreleased product-specific documentation taxonomy from the public surface and normalized synthetic axis semantics to 0–1 scores.
- 2026-09-10: Windows Edge/Puppeteer browser review covered all seven additive pages at 1440px and a true 390px viewport; mobile min-content/nav handling was hardened and the default favicon 404 was removed.
- 2026-09-10: Browser interaction checks passed for keyboard candidate selection, Monte Carlo regeneration, reduced-motion suppression of continuous motion, and no-JavaScript Docs navigation.
- 2026-09-10: Tracked-tree public-surface allowlist check passed with 31 tracked files; homepage, product manifest, and prelaunch config remained unchanged; publishable-content sensitive-pattern and unreleased-product-term scans passed.
- 2026-09-10: Added same-origin local documentation search with 18 public-safe entries and an accessible Search dialog available from every additive page.
- 2026-09-10: Added the first click-to-load Academy video using the public TraderCockpit Monte Carlo lesson; no third-party iframe exists before explicit user action.
- 2026-09-10: Browser acceptance passed across all seven additive pages at 320px and under 200% text-size stress; fixed the video aspect-ratio/min-height overflow found by that review.
- 2026-09-10: Built the first Phase B visual-depth slice: a three-mode parameter surface, an 18-node synthetic correlation network, and a three-family distribution/tail explorer.
- 2026-09-10: Phase B adversarial review fixed synthetic-badge reflow, deep-link sticky-nav occlusion, correlation toggle labeling, and the heavy-tail summary statistic.
- 2026-09-10: Direct hash-link acceptance passed for all three new lazy modules at 390px; each initialized its canvas/metric below the sticky navigation with no horizontal overflow.
