---
name: tradercockpit-free-media
description: Route TraderCockpit social images, video, narration, charts, news visuals, and packaging through verified zero-incremental-cost tools. Use for any request to create, edit, generate, repurpose, or package social media assets, and whenever a provider, model, or media workflow must be selected without paid APIs, credits, subscriptions, or hosted MCP gateways.
---

# TraderCockpit free media

Use the existing production stack. Spend exactly $0 in external provider charges.

## Start

1. Read AGENTS.md, BRAND.md, GROWTH-AUTHORITY-PLAYBOOK.md, and the relevant production skill.
2. For market content, read MARKET-ANALYSIS-DOCTRINE.md and run market-analysis before scripting.
3. For video, read the installed OpenMontage skill for its pipeline contract, but execute only in <repo>/OpenMontage.
4. State the selected tools and confirm their estimated external cost is $0 before generation.

## Route the asset

| Need | Route |
|---|---|
| Factual chart or stated price level | TradingView and the existing chart tools |
| News or evidence visual | Sourced capture with visible outlet/date, or a versioned Godseye evidence contract |
| Creative still | Codex image generation when available; otherwise open-generative-ai-local with DreamShaper 8 |
| Motion | Open/archive footage, Remotion, HyperFrames, or FFmpeg; use local Wan 2.1 1.3B only after its smoke test passes |
| Narration | Existing Chatterbox clone when its project assets exist; otherwise OpenMontage Piper |
| Shorts and packaging | Existing studio-kit, thumbnail renderer, and tools/handoff/recut_shorts.cjs |
| Publishing | Existing tools/publish.py, only after explicit operator approval |

## Hard guards

- Reject MuAPI, paid model APIs, credits, subscriptions, hosted generation, hosted MCP gateways, and paid fallbacks.
- Do not create accounts, enter API keys, top up balances, publish, schedule, or upload without explicit authority.
- Never use generated media as a factual chart, news screenshot, geospatial observation, product proof, or evidence.
- Keep cloud-provider fields blank in OpenMontage/.env and in Open Generative AI.
- If an approved motion treatment cannot run locally, stop and report the blocker. Do not silently downgrade it to stills.

## Record and review

- Use the active pipeline's existing asset manifest. Record source or prompt, model/tool, seed when available, license, output path, and synthetic status.
- Apply existing claims, frame-review, aspect-ratio, synthetic-disclosure, and operator publish gates.
- Export accepted assets under the active productions/<slug>/ workspace; never treat generated scratch output as evidence.
