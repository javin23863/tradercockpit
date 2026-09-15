# TraderCockpit Website — Current Authority

Status: **CURRENT / ONLY ACTIVE WEBSITE AUTHORITY**

This document defines the website state that agents, reviewers, and future work must use. Historical website designs, evidence folders, pricing drafts, and versioned visual-authority notes are superseded and are not active specifications.

Current implementation branch: `codex/mandatory-visual-skills-site-parity-20260915`  
Current PR: `#50`  
Current implementation baseline: `4e9462f7e32aff33c754aed16a81e797190f4c2a`

## Product and visual identity

TraderCockpit is presented as a futuristic quantitative-research universe, not a conventional SaaS card site or documentation portal. The Quant Universe is the primary spatial language across the public site.

- Home uses the dominant Three.js/WebGL Quant Universe: volumetric globe, orbital geometry, market terrain, research nodes, HUD instrumentation, particles, depth gates, and foreground structures.
- Ordinary public pages load the same production Quant Universe as a persistent ambient 3D field.
- Research Lab keeps its dedicated analytical WebGL/VTK renderers and deterministic synthetic data contracts.
- Support is a routing constellation, Trust is an evidence/boundary field, and Pricing is a four-tier constellation.
- Major page families must not collapse back into repetitive shaded panels with text.

## Four-tier pricing authority

The approved public monthly pricing ladder is exactly:

- **Core — $19.99/month**
- **Trader — $49.99/month**
- **Quant — $99.99/month**
- **ApolloPro — $150/month**

All four tiers must be visible on Home and Pricing. `docs/commerce-public.v1.json` is the machine-readable pricing record. ApolloPro remains the Stripe-bound plan at $150/month. Checkout remains disabled until subscription-to-desktop entitlement provisioning is verified end to end.

Do not reintroduce a retired single-plan presentation, placeholder future tiers, or speculative tier entitlements.

## Measured owner-reference grammar

The owner-supplied visual reference is 935 × 1683 px and remains the composition reference. Treat its measurements as ratios, not fixed browser pixels.

- Near-black base: `#010509` / `#01070B`; elevated field: `#040E14`.
- Primary luminous teal: `#3CFAD2`; supporting cyan: `#3DAED3`; negative/risk red: `#E54A5A`.
- Desktop hero copy occupies roughly 32–40% while the Quant Universe owns the remaining field.
- Home requires background/stars, globe/orbits, floating HUD layers, and foreground market terrain/device depth.
- Product proof is the real current TraderCockpit Guided Home capture, not a retired dashboard.
- Depth comes from overlap, perspective, scale, localized light, true 3D geometry, and foreground/background separation—not a blue/purple gradient.

## Public truth boundaries

- `docs/product-manifest.v1.json` controls product availability, platform state, and verified capability publication.
- `docs/commerce-public.v1.json` controls public pricing and checkout state.
- Synthetic research graphics remain explicitly synthetic and cannot be described as live market data, customer performance, or guaranteed outcomes.
- The current public state is waitlist/prelaunch; marketing visuals cannot override that state.
- The current desktop product proof contains Getting started, Charts, Builder, Custom Projects, Apollo, Models, Data organization, and Settings.

## Responsive and accessibility contract

- No horizontal overflow at 390px or desktop acceptance widths.
- Primary copy and controls may not collide with cinematic objects.
- Reduced motion freezes decorative movement while preserving depth and information.
- Keyboard focus remains visible; interactive research controls remain reachable.
- Mobile keeps the same Quant Universe identity; remove secondary ornament before shrinking critical text.

## Current acceptance

The current implementation passed the strengthened browser gate across **41 public routes × desktop/mobile = 82/82 renders with BAD=0**. The gate checks HTTP state, page errors, horizontal overflow, headline/scene collision, mojibake, Quant Universe presence, and four-tier pricing presence where required.

The production WebGL bundle rebuilt deterministically. Visual-skill authority, website integrity, site hardening, public claims, public UX, JavaScript syntax, and `git diff --check` also passed.

The current rendered appraisal is recorded in `.github/site-appraisal-current.md`. No earlier website appraisal is an active authority.
