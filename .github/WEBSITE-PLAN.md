# TraderCockpit Public Website Plan

Status: **Phases A–F complete / appraisal-adversarial visual and customer-language passes complete**
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
- [x] Build the walk-forward landscape.
- [x] Build the explicit in-sample/out-of-sample boundary visualization.
- [x] Build drawdown-valley path visualization.
- [x] Build the selection/multiple-testing funnel.
### Phase C — documentation system

- durable docs taxonomy
- concept template
- method template
- how-to template
- reference template
- client-side search index
- initial high-value public-safe concept pages
- help-ID resolver validation

### Phase C progress checklist

- [x] Durable public content taxonomy is versioned in `content-registry.v1.json`.
- [x] Concept, Method, How-To, and Reference authoring templates exist under `.github/site-templates/`.
- [x] Eight high-value Concept pages are generated from `concepts.v1.json` and checked for source drift.
- [x] A full Monte Carlo Method page demonstrates the deeper mathematical/assumption layer.
- [x] A full product-neutral Monte Carlo How-To demonstrates task-oriented interpretation.
- [x] Client-side search indexes the new Concept, Method, How-To, and help-resolver destinations locally.
- [x] `help.html?id=...` resolves versioned public help IDs without exposing private application routes.
- [x] Concept → visual → Method → How-To continuations are visible and browser-tested.
- [x] Phase C detail/resolver pages pass 320px reflow, 200% text enlargement, and console-error review.

### Phase D — homepage integration

Completed after Phase A/B/C acceptance:

- [x] Replace the legacy/decorative hero with the accepted synthetic Strategy Universe narrative.
- [x] Connect the homepage to Research Lab, Learn, Docs, Methods, Examples, and Updates.
- [x] Preserve manifest-driven product/CTA behavior and fail closed when the manifest cannot be verified.
- [x] Preserve the existing prelaunch/waitlist integration and UTM/source mapping while manifest status remains `waitlist`.
- [x] Separate public research education from product availability and verified capability.
- [x] Provide no-JavaScript, reduced-motion, keyboard, 320px reflow, and 200% text-size behavior.
- [x] Make initial homepage load same-origin only; external YouTube is a normal outbound link, not an eager embed/request.
- [x] Update homepage metadata, local search coverage, sitemap, and integrity checks.
- [x] Perform screenshot/adversarial visual review before commit.

## 12F. Homepage integration review — 2026-09-10

The Phase D homepage replacement was reviewed against the accepted Research Lab direction and the existing public product/waitlist contracts before commit.

| Severity | Finding | Resolution |
|---|---|---|
| High | Replacing the old homepage could silently turn synthetic research education into implied product output or performance evidence. | The new hero and atlas explicitly use deterministic synthetic data, label the axes/visuals as research geometry, state that no market data is used, and keep product availability in a separate manifest-governed section. |
| High | A redesigned product section could bypass the canonical manifest or expose a waitlist/CTA when product truth cannot be verified. | Static HTML fails closed with `STATUS: UNVERIFIED`, hidden waitlist and product CTA. Browser acceptance verifies the live `waitlist` state, Windows platform detail, canonical CTA, and a simulated manifest-500 failure that leaves conversion UI hidden. |
| High | Homepage rewiring could break the existing Kit double-opt-in and attribution contract. | The original field names, source mapping, UTM fields, and prelaunch activation path are preserved; browser acceptance verifies the Kit form action and YouTube/social attribution values. |
| Medium | The richer hero could create persistent animation or unusable no-JavaScript controls. | Motion has Pause/Resume and Reset controls, stops while hidden, hides the motion control under `prefers-reduced-motion`, and leaves a static explanatory fallback with inert controls hidden when JavaScript is disabled. |
| Medium | The new homepage could become a privacy/performance regression by eagerly contacting third parties. | Browser request capture confirms no initial external requests; search remains same-origin and YouTube remains an explicit outbound action. |
| Medium | Large typography and the visual grid could overflow narrow or enlarged-text layouts. | Browser acceptance passes at 320px and at 200% text size without horizontal overflow. |
| Medium | The homepage/search/sitemap/integrity rewrite was initially saved with CRLF, causing the repository whitespace gate to fail. | All changed text files were normalized to LF and `git diff --check` is required in the final checkpoint gate. |
| Medium | A visually attractive marketing homepage could dead-end instead of supporting exploration. | The homepage now exposes direct paths into Research Lab, Concept, Method, How-To, Docs, Examples, Updates, and the stable contextual-help contract. |

**Phase D result:** no unresolved high-severity findings. Windows Edge/Puppeteer acceptance passes manifest/waitlist truth, fail-closed behavior, local search, initial-request privacy, 320px reflow, 200% text enlargement, reduced motion, no-JavaScript fallback, and hero controls. Screenshot review covers the hero, research atlas, information-flow section, connected-learning system, and product/waitlist surface.

### Phase E — Academy and examples

- [x] Build multiple structured Academy learning paths rather than a video-thumbnail catalog.
- [x] Preserve the click-to-load video lesson template with written instruction as the primary source.
- [x] Publish the first end-to-end synthetic research example with question, selection context, reserved evidence, validation, interpretation, limitations, and next question.
- [x] Cross-link Concept, Visual, Method, How-To, Example, search, and stable help IDs.
- [x] Keep all example values explicitly synthetic and product-neutral.
- [x] Pass local-search, help-resolver, privacy, 320px reflow, 200% text, and visual review.

## 12G. Academy and synthetic-example review — 2026-09-10

Phase E was reviewed for performance-claim leakage, accidental product-workflow disclosure, weak learning structure, navigation dead ends, and responsive regressions.

| Severity | Finding | Resolution |
|---|---|---|
| High | An end-to-end example could read like a successful real strategy validation and imply future performance. | Example 001 uses deterministic synthetic values only, exposes no live strategy/account/market data, states “No performance claim,” says agreement across checks is evidence rather than proof, and ends with explicit limitations plus a next research question. |
| High | A public example could accidentally document unreleased product controls or internal workflow contracts. | The case study is product-neutral research education and links only to public Concept, Visual, Method, How-To, Example, and help destinations. No private route/control/backend identifiers are introduced. |
| Medium | The Phase E plan called for Academy learning paths, but the first implementation contained only one complete path. | Added a second six-step path for path risk and uncertainty, so Academy now has separate validation and path-risk/uncertainty journeys. |
| Medium | A selection example could hide how many alternatives were tried and make the chosen result look isolated. | The visual evidence chain explicitly shows `256 synthetic candidates → 1 development-selected candidate → 0 holdout feedback loops before selection`. |
| Medium | A research story could terminate with a verdict instead of exposing uncertainty that remains. | The example requires a dedicated limitations section and finishes with “What assumption would most change the conclusion if it were wrong?” plus concrete next branches. |
| Medium | Search/help plumbing could point to the example inconsistently or break once surfaced from the app. | The example is registered in content, local search, stable help routing, and sitemap; browser acceptance verifies `help.html?id=example.holdout-selection` and search ranking. |
| Medium | Six-step Academy rows and the example evidence chain could become horizontal-overflow traps on narrow/large-text layouts. | Responsive rules collapse the evidence chain and Academy paths; browser acceptance passes at 320px and under 200% text enlargement. |
| Medium | Educational pages could contact third parties merely by being opened. | Browser request capture confirms the example stays same-origin; video remains separately click-to-load. |

**Phase E result:** no unresolved high-severity findings. Two distinct Academy paths and the first complete public synthetic case study are implemented, searchable, help-addressable, responsive, and visually reviewed.

### Phase F — hardening

- [x] Browser/device crawl covers every sitemap page at desktop and 390px mobile widths.
- [x] Accessibility review checks named controls, semantic main landmarks, canvas text alternatives, and working skip-link focus.
- [x] Keyboard-only review covers the site-wide skip-link contract and interactive research controls.
- [x] Reduced-motion review confirms nonessential continuous motion is suppressed while static visuals remain meaningful.
- [x] Performance profiling enforces dependency-light text-asset budgets and records 4× CPU browser metrics for Home and Research Lab.
- [x] SEO/canonical/sitemap review reconciles all indexable public pages while excluding the help resolver utility from discovery.
- [x] Broken-link/deep-link validation covers local navigation, generated concepts, registries, and Research Lab hash targets.
- [x] Public-disclosure audit rejects local/internal path leakage and requires research/example boundary language.
- [x] Product-claim audit enforces the current `waitlist` state, zero verified capabilities, and fail-closed conversion surfaces.
- [x] CI runs architecture, hardening, claims, and syntax checks across all public `.js` and `.mjs` JavaScript files.
- [x] Original module inventory was reconciled; the previously orphaned Regime map is implemented as a synthetic 3D regime cube with Concept/Method/help/search coverage.

## 12H. Final hardening review — 2026-09-10

Phase F was adversarially reviewed across the full public surface rather than only the newly added pages.

| Severity | Finding | Resolution |
|---|---|---|
| High | The original Research Lab inventory named a Regime map, but no implementation phase actually owned it, allowing the plan to appear complete with an orphaned promised module. | Added the synthetic 3D Regime cube and a generated Regime Concept page, Methods entry, help ID, local-search entry, content-registry entry, sitemap URL, integrity requirements, and interaction/reflow acceptance. |
| Medium | The legacy strategy-claim checklist still executed JavaScript against capture fields that had been removed, throwing a runtime null error on a public page. | Removed the stale script without changing checklist content; the site-wide browser crawl now reports no page/console error. |
| Medium | The product-boundary/refund page lacked a main landmark, skip link, canonical metadata, and favicon handling, producing accessibility and console failures. | Added semantic/focusable main content, skip navigation, metadata/canonical, and zero-request favicon handling without changing the policy substance. |
| Medium | Existing skip links often scrolled visually but did not transfer keyboard focus because `#main` was not focusable. | Added `tabindex="-1"` to primary main landmarks across the public site and to the Concept generator so regeneration preserves the fix. |
| Medium | The first site-wide accessibility harness incorrectly flagged hidden attribution inputs as unnamed controls. | Corrected the test to exclude non-interactive hidden inputs rather than adding meaningless labels; visible controls remain name-checked. |
| Medium | The first reduced-motion harness assumed every sampled page contained a `.depth-card`, causing a harness exception. | Removed the brittle page-shape assumption and retained the direct reduced-motion state/control assertions. |
| Medium | The hardening checker originally required `id` to appear before `tabindex` in `<main>`, falsely rejecting a valid focusable checklist landmark. | Made the static focus check attribute-order independent and reran the full suite. |
| Medium | Static syntax CI protected only the original Research Lab script, leaving later search/help/video/home/visual scripts outside the syntax gate. | CI now runs `node --check` over every public `.js` and `.mjs` file and executes architecture, hardening, and public-claims audits. |

**Phase F result:** no unresolved high-severity findings. The browser crawl passes all 22 sitemap pages at desktop and mobile widths with no horizontal overflow, console errors, eager third-party requests, unnamed visible controls, or broken skip-link focus. Static hardening passes 25 HTML pages and 23 canonicals; `help.html` remains a resolver utility intentionally excluded from the 22-page sitemap. The current public-claims audit passes 42 public files with `status=waitlist` and zero verified capabilities. Under 4× CPU throttling, Home uses 8 local requests and about 65.5 KB transfer, Research Lab uses 7 local requests and about 98.3 KB transfer, and measured script duration remains roughly 20–25 ms with no eager external requests.

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
## 12D. Validation-geometry review — 2026-09-10

The walk-forward and holdout-boundary slice was reviewed for false precision, misleading information-flow semantics, duplicate deep-link targets, unsafe DOM updates, and responsive failures.

| Severity | Finding | Resolution |
|---|---|---|
| High | A repeated-peek diagram could look like measured leakage from a real TraderCockpit run. | The page states that the 36 candidates and four feedback loops are illustrative, shows no measured strategy result, and links the diagram to the independent Methods explanation. |
| Medium | The OOS canvas labeled the selection point “selected once” in both modes, which became misleading after holdout feedback was enabled. | The label now changes to “selection + feedback” in repeated-peek mode while remaining “selected once” only in the preserved-holdout case. |
| Medium | The first OOS notice update used static `innerHTML` even though markup injection was unnecessary. | Replaced it with `createElement`, `textContent`, and `replaceChildren`; the integrity checker now rejects `innerHTML` in the validation visual script. |
| Medium | Replacing placeholder cards with real sections could leave duplicate `id` values and ambiguous help/deep-link targets. | Removed the placeholder IDs and upgraded the integrity checker to detect duplicate HTML IDs and require both validation anchors and the lazy validation script. |
| Medium | Rolling and anchored modes could be visually different without actually representing different training spans. | Browser acceptance asserts the selected rolling span is 42 synthetic units and that the anchored span expands for the same fold; fold navigation must also change the readout. |
| Medium | New long validation modules could reintroduce mobile/large-text overflow or fail to initialize on direct hash navigation. | Both modules pass 320px reflow, 200% text stress, and independent 390px direct-link initialization below the sticky navigation. |

**Validation-geometry result:** no unresolved high-severity findings. Rolling/anchored mode switching, fold navigation, preserved/repeated-peek information flow, direct links, narrow reflow, and large-text behavior pass in Windows Edge/Puppeteer.
## 12E. Path-risk and selection review — 2026-09-10

The final Phase B slice was reviewed for invalid quantitative claims, accidental workflow prescription, random-sample overfitting in the acceptance test itself, encoding defects, and responsive failures.

| Severity | Finding | Resolution |
|---|---|---|
| High | The selection funnel could imply that “top 25% → top 5% → winner” is a recommended validation workflow. | The page now states that those planes are a simplified visualization of selection pressure only, under an independent standardized-Normal null; it directs users to the Methods limitations rather than presenting the funnel as product or research procedure. |
| Medium | The first drawdown headline said the synthetic paths reached the “same” endpoint, but the generated endpoints are only similar. | Softened the claim to “Similar endpoints” so the copy matches the actual deterministic paths. |
| Medium | The first drawdown JavaScript used unary minus directly before exponentiation, which is invalid JavaScript syntax. | Rewrote the Gaussian-valley terms with `Math.pow(...)`; `node --check` now passes before browser execution. |
| Medium | A corrupted non-ASCII arrow appeared in the selection canvas label during file transfer. | Replaced the label with ASCII-safe text and added a UTF-8 replacement-character scan during review. |
| Medium | Requiring the observed maximum of one null sample to increase monotonically with family size would make the acceptance test statistically unsound. | Browser acceptance checks monotonicity of the explicit Normal order-statistic reference instead. The observed maximum remains one deterministic example and is not used as the theorem. |
| Medium | “Final survivors” could imply that the simplified funnel proves a validated survivor. | Renamed the metric to “final selected synthetic example”; the highlighted point is explicitly described as noise, not a profitable strategy. |
| Medium | Drawdown modes could have labels without materially different path geometry. | Browser assertions verify: deep shock has larger maximum drawdown than long valley; long valley remains underwater longer; repeated-valley mode records multiple peak recoveries. |
| Medium | The two new long modules could break narrow/large-text layouts or fail when deep-linked. | Expanded Research Lab passes 320px reflow, 200% text stress, and independent 390px hash-link lazy initialization for both modules. |

**Phase B completion result:** no unresolved high-severity findings. The Research Lab now has nine real educational visual modules/sections spanning candidate geometry, uncertainty, parameter robustness, correlation, distributions, walk-forward partitioning, holdout information flow, drawdown path risk, and multiple-testing selection pressure. Phase B is complete without changing the legacy homepage or claiming unverified product capability.
## 12F. Phase C documentation-system review — 2026-09-10

The documentation-system slice was adversarially reviewed for content drift, brittle in-app links, product-claim leakage, privacy regressions, and visual/interaction dead ends.

| Severity | Finding | Resolution |
|---|---|---|
| High | If the desktop application deep-links directly to page paths, later documentation reorganization could break released in-app help. | Added `help.html?id=...` plus a versioned public help registry. Browser acceptance covers valid, unknown, and invalid IDs; the resolver only accepts public knowledge IDs and same-origin registry destinations. |
| High | Concept pages could drift independently and quietly contradict their shared taxonomy. | Added `concepts.v1.json` as the versioned source and `generate_concept_pages.py --check`; the integrity gate now fails if any generated Concept page differs from source. |
| High | Public Concept/How-To content could be mistaken for proof that a corresponding TraderCockpit feature ships today. | Every generated Concept page carries explicit public-research/product-boundary copy, while the full How-To is product-neutral. Product availability remains governed by `product-manifest.v1.json`. |
| Medium | The first Monte Carlo Concept hero exposed the visual and Method but not the completed How-To, leaving the learning chain incomplete. | Added optional data-driven How-To handoffs in both the Concept hero and page guide; Monte Carlo now exposes visual, Method, and How-To continuations. |
| Medium | A stable resolver could become an open-redirect surface if registry paths were trusted without origin validation. | Resolver logic accepts the versioned public registry only and rejects destinations that resolve outside the current site origin; the integrity checker also validates all registry/content paths. |
| Medium | Rich Academy video could reintroduce third-party requests inside the detailed How-To layer. | The detailed How-To reuses the click-to-load privacy-enhanced loader; browser interception confirms no YouTube request occurs before explicit user action. |
| Medium | Documentation pages could become visually dense or inaccessible while sharing one large-type design system. | Browser acceptance covers all eight Concepts plus Method/How-To/help resolver at 320px and under 200% text enlargement with no horizontal overflow or console errors. |

**Phase C result:** no unresolved high-severity findings. The public site now has a durable Concept/Method/How-To/Reference authoring model, eight source-controlled Concept pages, one complete deep Method/How-To chain, local search, and a stable help-ID resolver suitable for future in-app `What is this?` links.

## 12I. Appraisal / adversarial visual-quality review — 2026-09-10

After technical hardening passed, the public site was reviewed again against the original product brief: the site should invite exploration through graphical richness, not merely present the same styled text page repeatedly.

| Severity | Finding | Resolution |
|---|---|---|
| High | Learn, Docs, Methods, How-Tos, Examples, and Updates opened with nearly identical oversized text-first heroes and large empty bands. The design system was coherent but the primary destinations did not feel individually explorable. | Rebuilt all six primary landing heroes as two-column visual experiences with purpose-specific diagrams: a five-depth learning orbit, contextual-help routing map, method-assumption stack, six-part lesson contract, evidence-story chain, and public-release authority stack. Headline scale was reduced on these pages so useful structure appears in the first viewport. |
| High | Research Lab had grown beyond 15,000px with ten visual modules but lacked a first-class way to discover or jump between them. Richness had become navigation friction. | Added a complete ten-module Visual Atlas navigator with named research dimensions and direct hash links for Strategy Universe, Monte Carlo, parameter robustness, correlation, distribution, regime state, walk-forward, holdout flow, drawdown, and selection pressure. |
| Medium | The first visual-hero markup supplied `aria-label` on generic containers without an explicit semantic role, so the group description was not reliably exposed to assistive technology. | Added `role="group"` to all six labeled landing visual systems and retained normal descendant text/links for direct reading and keyboard navigation. |
| Medium | The orbit layout passed horizontal-overflow tests at 390px but the lower nodes could visually overlap even though the document width was valid. | Repositioned the mobile orbit nodes into separated upper/lower bands and visually re-captured Learn and Docs at 390px. This review therefore treats collision testing separately from overflow testing. |
| Medium | Adding more visual richness risked undoing the dependency-light and reduced-motion requirements. | The appraisal slice is HTML/CSS only: no new JavaScript framework, WebGL dependency, tracker, font, or external request. Motion is limited to short hover/focus elevation under `prefers-reduced-motion: no-preference`; content and meaning remain static without it. |
| Medium | Visual quality improvements could silently regress after this review because prior integrity checks only protected links/content contracts. | `check_website.py` now requires the six accessible visual landing heroes and exactly ten Research Lab atlas destinations. |

### Appraisal quality gate

- [x] Home and Research Lab retain distinct quantitative visual identities.
- [x] Learn, Docs, Methods, How-Tos, Examples, and Updates each communicate their job graphically above the fold.
- [x] Landing visuals explain information architecture rather than adding decorative 3D.
- [x] Research Lab exposes all ten modules through a first-class atlas navigator.
- [x] Visual navigation remains keyboard operable and semantically grouped.
- [x] Mobile visual collision review passes in addition to normal overflow checks.
- [x] Appraisal polish adds no new eager external requests or JavaScript dependencies.
- [x] Full 22-sitemap-page desktop/mobile regression remains green after the visual changes.
- [x] Product-manifest, waitlist, privacy, synthetic-data, and performance boundaries remain intact.

**Appraisal result:** the two blocking visual/navigation findings and all medium findings from this round are corrected. Static architecture/hardening/claims checks pass; the 22-page desktop/mobile browser crawl passes visual-hero contracts, atlas navigation, keyboard focus, privacy, reduced motion, and reflow. Homepage local text payload remains below the existing budget at approximately 78.4 KB after the shared CSS additions.


## 12J. Customer-language adversarial review — 2026-09-10

A second appraisal pass reviewed the site as a customer rather than as the implementation team. The underlying product-truth and contextual-help machinery was correct, but several public pages still explained that machinery instead of simply helping the visitor.

| Severity | Finding | Resolution |
|---|---|---|
| High | Home, Docs, Updates, Research Lab, the help resolver, and generated Concept pages exposed implementation/governance terms such as “product manifest,” “help registry,” raw help IDs/URLs, “public-safe,” “private roadmap,” and “hard-code.” Accurate engineering language made the site feel like an internal handoff rather than a finished consumer experience. | Kept the manifest, help registry, stable IDs, fail-closed behavior, and CI contracts unchanged underneath, while rewriting visible copy around current product status, exact contextual help, customer-facing reference, and published updates. A rendered-text scan now reports zero occurrences of the flagged engineering vocabulary. |
| High | Friendlier Updates copy briefly introduced “available now,” which violates the current waitlist claim policy even though the intent was descriptive. | The public-claims gate rejected the wording; the headline was changed to neutral “current product status” language without weakening the gate. |
| Medium | Updates still rendered the internal abbreviation “CTA” and asked “What can I use today?” while the product remains on a waitlist. | Renamed the dynamic field to “Current action” and the section to “Where does the product stand today?” while retaining the same manifest-backed values. |
| Medium | Docs visually exposed `help.html?id=…`, help-ID/registry terminology, a “Publication gate,” and a raw JSON-registry link. | The visual now asks “What do you need?” and routes to Concept/Method/How-To/exact answer. The page demonstrates contextual help without exposing raw routing syntax or registry files. |
| Medium | Research Lab ended with a list of public help IDs instead of useful next learning choices. | Replaced the implementation list with customer-facing deep dives into Monte Carlo, walk-forward, out-of-sample evidence, parameter robustness, and market regimes. |
| Medium | Generated Concept pages referred to the public product manifest in every product-boundary section. | Updated the source generator once and regenerated all nine pages with plain-language “research concept, not product instruction” wording; drift checking still protects the generated set. |
| Medium | The help resolver’s fallback/status messages described IDs and registries instead of helping a visitor recover. | Resolver messages now say whether the help link is recognized/available and direct the visitor to Docs or Search; same-origin and registry-validation security checks remain unchanged. |

### Customer-language quality gate

- [x] Rendered public HTML contains none of the flagged implementation/governance vocabulary.
- [x] Dynamic Home/Updates/help messages avoid manifest/registry/CTA jargon.
- [x] Raw help-routing syntax and JSON registry files are no longer promoted as customer actions.
- [x] Product truth remains `waitlist` with zero verified capabilities and fail-closed conversion surfaces.
- [x] All nine generated Concept pages preserve the product boundary in plain language.
- [x] Full 22-page desktop/mobile customer appraisal passes with no console errors, horizontal overflow, or eager external requests.
- [x] Static architecture, hardening, public-claims, generated-content, and whitespace gates remain green.

**Customer-language result:** no unresolved high-severity findings. The public site now presents customer concepts while keeping implementation contracts behind the interface. Product truth, contextual-help routing, privacy, and generated-content guarantees remain unchanged.

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
- 2026-09-10: Built the walk-forward validation landscape with rolling/anchored window geometry, seven selectable folds, explicit train/evaluation encodings, and no performance data.
- 2026-09-10: Built the in-sample/out-of-sample information-boundary visualization with preserved-holdout and repeated-peek modes; four feedback loops are explicitly illustrative.
- 2026-09-10: Validation-geometry adversarial review corrected repeated-peek labeling, removed unnecessary `innerHTML`, strengthened duplicate-ID/script integrity checks, and passed 320px/200%-text/direct-link browser acceptance.
- 2026-09-10: Built the drawdown-valley explorer with deep-shock, long-valley, and repeated-valley deterministic paths; browser checks verify distinct depth/duration/recovery behavior.
- 2026-09-10: Built the independent-null selection funnel with keyboard-controlled candidate family size, explicit Normal order-statistic reference, and simplified-stage disclosure.
- 2026-09-10: Final Phase B adversarial review corrected overstrong endpoint copy, invalid exponentiation syntax, a transferred label encoding defect, workflow-prescription risk, and an unsound observed-max monotonicity test.
- 2026-09-10: Phase B completion browser acceptance passed drawdown semantics, selection-family effect, keyboard interaction, 320px reflow, 200% text stress, and 390px direct links.
- 2026-09-10: Phase C added a versioned content taxonomy, four authoring templates, eight source-generated Concept pages, a full Monte Carlo Method, a full product-neutral interpretation How-To, and a stable help-ID resolver.
- 2026-09-10: Phase C adversarial review completed the Concept → visual → Method → How-To chain and passed 11-page help/search/video/reflow browser acceptance.
- 2026-09-10: Phase D replaced the legacy homepage with a research-first Strategy Universe hero, six-entry visual atlas, evidence/information-flow narrative, connected learning/help map, and a separate manifest-governed public product state.
- 2026-09-10: Homepage browser acceptance verified the canonical waitlist form/action, UTM/source mapping, manifest CTA/platform truth, no initial third-party requests, fail-closed manifest behavior, reduced motion, no-JavaScript fallback, 320px reflow, and 200% text enlargement.
- 2026-09-10: Phase D adversarial visual review accepted the hero/research/learning/development surfaces after normalizing CRLF formatting that had failed `git diff --check`.
- 2026-09-10: Phase E published Example 001, a synthetic holdout-selection research chain covering selection context, preserved holdout evidence, walk-forward checks, Monte Carlo interpretation, limitations, and the next research question.
- 2026-09-10: Academy now contains two six-step connected learning paths: research validation and path risk/uncertainty.
- 2026-09-10: Phase E adversarial/browser review verified help resolution, local search, same-origin example loading, 320px reflow, 200% text enlargement, and visual clarity of the Academy paths and 256 → 1 → 0 evidence chain.

- 2026-09-10: Phase F hardened legacy public pages, fixed stale checklist JavaScript, added keyboard-focusable skip targets across the public site, and expanded CI to architecture/hardening/claims plus all `.js`/`.mjs` syntax checks.
- 2026-09-10: Final scope reconciliation implemented the previously orphaned Regime map as a synthetic 3D cube with Concept, Methods, help, search, content-registry, sitemap, and browser acceptance coverage.
- 2026-09-10: Final full-site acceptance passed 22 sitemap pages at desktop/mobile, 25 HTML pages/23 canonicals, current waitlist/zero-capability public-claims audit, and 4× CPU Home/Research Lab performance budgets with no eager external requests.
- 2026-09-10: Appraisal/adversarial visual-quality review found repetitive text-first primary landing pages and missing Research Lab wayfinding; both were treated as blocking design findings rather than cosmetic polish.
- 2026-09-10: Added six purpose-specific visual landing heroes and a ten-module Research Lab Visual Atlas navigator; mobile collision and accessible-group issues found during the second review were corrected.
- 2026-09-10: Post-appraisal full-site regression passed architecture, hardening, public claims, generated-content drift, whitespace, and 22-sitemap-page desktop/mobile browser acceptance.
- 2026-09-10: Customer-language adversarial review removed manifest/registry/raw-help-routing jargon from visible Home, Docs, Updates, Research Lab, contextual-help, search, and generated Concept surfaces while preserving the underlying contracts.
- 2026-09-10: The claims gate rejected a brief “available now” wording regression; neutral current-status language replaced it, rendered-text scans reached zero flagged engineering terms, and the final 22-page desktop/mobile customer appraisal passed.
- 2026-09-10: Post-merge in-app-help integration identified three Test & Validate metrics without public explanations: Profit Factor, Expectancy, and Return / Drawdown Ratio.
- 2026-09-10: Added product-neutral anchored Method entries plus stable help/search/content-registry records for those three metrics; no new product capability claim or dedicated visualization was invented.
- 2026-09-10: Adversarial terminology review removed the incorrect `payoff ratio` alias for Profit Factor and retained an explicit warning that Return / Drawdown conventions vary by platform and definition.
- 2026-09-10: In-app Test & Validate coverage audit identified Performance Overview / Equity Curve as the remaining meaningful visualization without a matching public explanation.
- 2026-09-10: Added a product-neutral Equity Curve Method anchor plus stable help, search, and content-registry records; the definition explicitly separates historical path shape from future-performance claims.

- 2026-09-10: Reconciled the deeper Backtest Result Metrics reference onto current website main after short metric explanations had already landed separately. Stable Profit Factor, Expectancy, and Return/Drawdown help IDs now resolve to exact anchors on the full reference without changing the in-app contract.
- 2026-09-10: Metric-reference adversarial reconciliation retained the canonical `research.return-drawdown-ratio` ID, removed the obsolete `return-dd` anchor, and added an explicit warning that platform-specific metric formulas govern when they differ from the common forms explained here.

- 2026-09-10: Added bounded public-help search prefill for desktop/in-app handoff. `#search=` is preferred so the term stays out of the HTTP request; `?q=` remains a bounded web fallback. Auto-open is limited to 120 characters, ordinary content anchors remain unaffected, and search still uses only the same-origin static index.
- 2026-09-10: Search-prefill browser acceptance passed local-only request checks, Monte Carlo ranking, normal-anchor isolation, overlong-input fail-closed behavior, 1280px/390px reflow, and 200% text enlargement.
- 2026-09-10: Added product-neutral Validation Foundations covering acceptance conditions, calendar-year consistency, and evidence/provenance chains, plus Net Profit in the Backtest Result Metrics reference. Four new stable help IDs resolve directly to those anchors without asserting product availability.
- 2026-09-10: Validation-foundation browser acceptance passed all four help-ID routes at 1280px and 390px with no overflow or console errors; public-claims authority remains waitlist with zero verified capabilities.
- 2026-09-10: Adversarial wording review softened an overstrong reproducibility claim: evidence provenance helps support reproducibility and auditability but does not guarantee methodological validity or future performance.

## 16. Post-foundation public learning and support expansion — 2026-09-11

This expansion extends the completed Phases A–F without changing the manifest-governed product-availability boundary or the approved research-first visual direction.

- [x] Added product-neutral Higher-precision Retesting, Validation Foundations, Backtest Result Metrics, and Chart Evidence Method material with stable public help IDs.
- [x] Added complete written Academy guides for staged validation, reading result metrics together, and reading chart evidence.
- [x] Added Support, Trust, and a manifest-backed fail-closed FAQ without inventing a contact channel, pricing, download, or release availability.
- [x] Added Learn Start Here, the linked Research Glossary, and a Video Lessons index that lists only the one actually published companion video.
- [x] Preserved click-to-load video privacy: no YouTube request occurs until explicit user action, and the privacy-enhanced embed remains optional to the written lesson.
- [x] Added Example 002, a deterministic synthetic historical-replay boundary case comparing information-safe replay with an explicitly invalid future-leaking view.
- [x] Kept synthetic examples, research education, and current product availability as separate claims; `product-manifest.v1.json` remains the sole public product-state authority.
- [x] Avoided homepage edits during this expansion while the separate Helios homepage/parity lane remains independently owned.

Latest merged public-surface evidence after Example 002:

- Website integrity: **PASS — 22 primary pages, 32 help IDs, 47 search entries**.
- Site hardening: **PASS — 38 HTML pages, 36 canonicals**.
- Public claims: **PASS — status `waitlist`, 0 verified capabilities**.
- Generated Concepts: **PASS — 9 generated pages current**.
- Sitemap: **35 indexable URLs**.
- Fresh browser crawl: **35 sitemap URLs × 1280px/390px PASS** for main landmarks, visible-control naming, no horizontal overflow, no console/page errors, no eager iframes, and no eager third-party requests.
- Focused replay acceptance: slider and keyboard cutoff movement, safe-vs-leaky future-bar handling, Example-index discovery, contextual-help resolution, and desktop/mobile visual appraisal all **PASS**.
