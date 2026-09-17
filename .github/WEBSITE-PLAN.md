# TraderCockpit Public Website Plan — Theme 2

Status: **implementation complete / PR review candidate**
Authority: `.github/WEBSITE-CURRENT.md`

## Goal

Replace the retired Quant Universe / neon sci-fi presentation with a reproducible cinematic research-lab system that can be implemented faithfully in the existing static HTML/CSS/JS stack.

The new direction is product-led rather than effect-led. Real TraderCockpit captures, restrained physical materials, strong typography, and deliberate composition carry the experience. WebGL is optional and is not a visual-quality requirement.

## Non-negotiable truth boundaries

- Keep public assets under `docs/` and governance under `.github/`.
- Preserve `docs/product-manifest.v1.json` and `docs/commerce-public.v1.json` as product/commerce authorities.
- Keep the current waitlist/prelaunch boundary.
- Preserve the four approved monthly prices exactly.
- Do not invent performance, users, strategies built, data-source counts, customer evidence, entitlements, or testimonials.
- Research examples stay synthetic unless a publishable source is explicitly approved.
- Maintain keyboard, reduced-motion, mobile navigation/reflow, and no-horizontal-overflow requirements.

## Theme system

- warm black/graphite environmental canvas;
- ivory typography;
- champagne/brass interface accent;
- real product screens framed as black-metal/smoked-glass instruments;
- directional warm light and realistic shadow;
- minimal radii and restrained borders;
- page-family-specific information composition instead of one repeated card template;
- no generic cyan glow language;
- no site-wide globe/orbit/HUD identity;
- no purple/blue AI gradient language;
- no dependence on decorative 3D for perceived quality.

## Rollout

### Phase 1 — Home visual proof — COMPLETE
- rebuilt the Home hero and product proof;
- removed Home dependency on ambient WebGL;
- preserved pricing/access/waitlist/video/privacy truth;
- established the approved Theme 2 implementation baseline.

### Phase 2 — Pricing and shared public system — COMPLETE
- rebuilt Pricing without constellation/orbit imagery;
- preserved the exact four approved monthly prices with no invented tier entitlements;
- added `cinematic-site-v1.css` to ordinary public routes;
- removed retired visual-depth CSS outside Research Lab;
- removed article-depth SVG generation and site-wide Quant Universe loading from `site-search.js`;
- migrated generated Concept pages through their generator.

### Phase 3 — full-page visual appraisal — COMPLETE
- differentiated Docs as a reference-routing instrument;
- differentiated Learn as a curriculum ladder;
- differentiated Methods as an evidence ledger;
- differentiated How-Tos as a staged workflow surface;
- differentiated Examples as an evidence chain;
- differentiated Updates as a status timeline;
- differentiated Support as a routing index;
- differentiated Trust as bounded evidence claims;
- retained a deliberately sparse utility treatment;
- corrected mobile navigation so primary routes and Search remain reachable;
- brought the printable strategy-claim checklist into the public shell on screen while keeping navigation hidden in print;
- retained Research Lab as the analytical-renderer exception.

### Phase 4 — final acceptance — COMPLETE FOR PR REVIEW
Reviewed implementation: `21f579739793cdded947da4a4a258a389bf4d529`.

Final evidence: `.github/evidence/theme2-pr-final/acceptance.json`.

Acceptance includes:
- **41 public pages × desktop/mobile = 82/82 route renders, badRoutes=0**;
- **13 major page families × desktop/mobile = 26/26 full-page renders, badMajor=0**;
- reduced-motion checks on Home, Pricing, a generated Concept page, and Research Lab: **badReduced=0**;
- keyboard focus and local Search: PASS;
- no external Search requests: PASS;
- click-to-load video privacy: PASS;
- public waitlist/checkout and exact four-price contract: PASS;
- printable strategy-claim checklist print chrome suppression: PASS;
- zero retired ambient Quant Universe leakage on ordinary public pages.

Repository/build gates are rerun on the final PR head after evidence/governance is committed.

## Visual acceptance rule

DOM correctness, WebGL presence, route count, and no-overflow checks cannot establish visual quality.

A Theme-2 PASS requires a rendered page that visibly achieves:
- coherent foreground/midground/background depth where appropriate;
- believable material/lighting behavior where cinematic treatment is appropriate;
- product integration with adequate scale;
- strong typography and negative space;
- clear primary action;
- minimal generic cards/pills;
- page-family-specific hierarchy;
- responsive continuity;
- a distinct TraderCockpit identity that does not depend on copying the reference site.

The implementation has passed that gate for PR review. A reviewer may still identify new findings; those findings, not the retired theme, become the basis for subsequent changes.
