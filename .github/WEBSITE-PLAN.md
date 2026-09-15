# TraderCockpit Public Website Plan — Current

Status: **current implementation accepted on the active PR branch**

Canonical visual authority: `.github/WEBSITE-CURRENT.md`
Current appraisal: `.github/site-appraisal-current.md`
Current PR: `#50`

This file contains only the active website plan. Superseded phase logs, retired pricing assumptions, and prior visual-version notes are intentionally kept out of the current tree; Git history remains the archive.

## Goal

Maintain TraderCockpit as an explorable futuristic quantitative-research environment, not a conventional SaaS brochure or a documentation site made of repeated panels.

The public experience combines:

- an immersive Quant Universe;
- real TraderCockpit product proof;
- interactive research education;
- documentation and How-Tos;
- evidence/trust boundaries;
- current public access and pricing state.

## Current public architecture

- Home — immersive Quant Universe and product proof.
- Research Lab — analytical WebGL/VTK atlas.
- Learn — structured research education.
- Docs — exact product/reference answers.
- Methods — quantitative reasoning and limitations.
- How-Tos — task-focused workflows.
- Examples — complete synthetic research stories.
- Pricing — four approved monthly tiers and current product proof.
- Support — routing constellation.
- Trust — provenance, interpretation, privacy, and evidence boundaries.

## Pricing and commerce

The active monthly ladder is exactly:

1. Core — $19.99
2. Trader — $49.99
3. Quant — $99.99
4. ApolloPro — $150

`docs/commerce-public.v1.json` is the public pricing/checkout record. ApolloPro is the Stripe-bound plan. Checkout stays disabled until entitlement provisioning is verified. Do not publish invented benefits, discounts, future tiers, or a retired single-plan presentation.

## Visual implementation

- Three.js/WebGL source lives in `.github/site-build/src/site-webgl.js`; generated output is `docs/assets/generated/site-webgl-v1.js`.
- Home uses the full Quant Universe scene.
- Ordinary public pages progressively mount the same universe as an ambient spatial field.
- Research Lab owns its dedicated WebGL/VTK analytical renderers.
- The current Guided Home capture under `docs/assets/desktop-current.png` is the public product-truth image.
- Major page families must use distinct spatial compositions and may not regress to repetitive shaded text blocks.

## Truth boundaries

- `docs/product-manifest.v1.json`: availability, platform, verified-capability state.
- `docs/commerce-public.v1.json`: approved tier prices and checkout state.
- Research examples: synthetic unless an explicitly publishable dataset is approved.
- No performance promises, guaranteed edge, invented market data, or fabricated customer proof.

## Completion gate

A visible change is complete only after the checks in `AGENTS.md` and `DESIGN.md` pass, including rendered desktop/mobile acceptance. The current strengthened browser gate covers all 41 public pages at desktop and mobile and explicitly checks renderer presence, four-tier pricing, overflow, mojibake, page errors, and headline/scene collisions.

Current acceptance: **82/82 rendered routes PASS; BAD=0**.
