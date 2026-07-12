# Trader Cockpit — YouTube Traffic Strategy

Source playbook: "How To Beat The New YouTube Algorithm With Claude AI" (Shane Hummus,
2026-06-14, youtu.be/-0f-IpXfJpg). Applied to the esq cockpit (`javin23863/futures`,
`apps/cockpit`), product name: **Trader Cockpit**. Videos produced by OpenMontage
(this repo), published by `tools/publish.py`.

## The product (facts from the repo — all claims must stay inside these)

- esq = parity-honest multi-asset quant strategy research/backtesting harness.
- Cockpit = JARVIS-style command deck over a 12-phase robustness pipeline:
  ~19,931 strategy candidates, Monte-Carlo displays, alpha-decay, shadow equity,
  "no-lying-dashboard" honesty rules.
- **PAPER-ONLY. Not a live bot; order routing hard-blocked in code.**
- Standing operator rulings: evidence-based feature claims only, consumer language.

**Hard content rules (trust boundary — never soften):**
1. No profit claims, no "this strategy makes $X". The sibling research program's own
   honest result was *no robust edge* — the honesty IS the product.
2. Every number shown on screen must be a real render of the real cockpit.
3. AI-assisted videos get YouTube's altered/synthetic label where required; substance
   (footage, data, receipts) is always real. Slop = distribution death + ban risk.

## Pillar 1 — Category (be first, not better)

The trading niche ocean = signal sellers, lambo thumbnails, guru courses. Nobody owns
the opposite corner. Our puddle:

> **"I help retail futures traders find out their strategy is garbage — before the
> market tells them."**

Category: **honest quant tooling / anti-guru backtesting**. Niche doors used:
METHOD (evidence-gated 12-phase robustness pipeline) × PROBLEM (overfit backtests,
fake guru claims) × WHO (solo retail futures traders). First-in-category because
every competitor's incentive is to promise profits; ours is to disprove them.

Second lane (build-in-public): "watch an AI-assisted solo dev build a JARVIS trading
cockpit" — dev-tools audience, feeds the same funnel.

## Pillar 2 — Ideas (outlier filter)

Hunt criteria before scripting ANY video: existing video >100k views, channel <100k
subs, view:sub ≥5:1, weak packaging → starving audience. Copy the idea, never the
video. Sharpen title + angle with Claude.

Seed ideas (validate each against the filter before production):

| # | Idea | Format / OpenMontage pipeline |
|---|------|-------------------------------|
| 1 | "I backtested [famous guru strategy] 10,000 ways. Here's the honest number." | Long-form explainer + cockpit screen capture |
| 2 | "Why 97% of backtests lie (and the 12 checks that catch them)" | Explainer, motion graphics |
| 3 | "ICT / SMC / price action — coded, merged, tested. Receipts inside." | Documentary montage (mirrors the viral hook of the source video itself) |
| 4 | "I built a JARVIS for trading" | Build-in-public, cockpit b-roll |
| 5 | "19,931 strategies entered. Watch the funnel kill them." | Shorts series — one phase per short, 9:16 |
| 6 | "Monte Carlo says your equity curve is luck. Here's how to check yours." | Explainer |
| 7 | "Alpha decay: why the strategy you bought stopped working" | Explainer |
| 8 | "Paper trading is not a toy — it's the only honest mode" | Short |
| 9 | "What a real quant dashboard looks like (no lambo)" | Cockpit tour |
| 10 | "I let Claude run my research pipeline for a week" | Build-in-public |

Idea intake loop (weekly, ~30 min): YouTube search niche keywords → collect outliers
→ dump into Claude → sharpened titles/angles → pick 1-2 → produce.

## Pillar 3 — Right views (revenue pyramid)

Trading/quant tooling = high-ticket niche tier ($100–$5k+ per 1k views potential).
Views target is SMALL: 1k right viewers > 100k wrong ones. Monetization = product
front door, not AdSense: channel → waitlist/GitHub → Trader Cockpit product
(pricing model = later decision; nothing in repo yet). YouTube long-form is the
mother platform; the same 9:16 render syndicates to Shorts + IG Reels + FB Reels +
TikTok via `publish.py`.

## Rule zero — co-pilot, not replacement (our version)

**REVISED 2026-07-13 (supersedes on-camera decision): FACELESS + AUTOMATED.
Channel name: TraderCockpit.**

Format = data-essay: Kokoro VO over real cockpit/gauntlet footage, motion-graphic
concept cards (studio-kit compositions), kinetic captions. Pipeline runs via
`tools/produce.py` (VO → captions → assemble → shorts → publish).

Anti-slop guardrails (mandatory — faceless lives or dies on these):
1. Every video anchored on REAL screen captures + verified numbers. No generic
   stock-footage padding. The receipts ARE the face.
2. YouTube altered/synthetic disclosure set on upload (`--synthetic` flag,
   `status.containsSyntheticMedia`) — honest labeling, no gaming.
3. Target 8–12 min data-essays, not 20-min talking-head lengths — faceless
   retention math is different.
4. MONTAGE-CRAFT rulebook + attention QA (TRIBE, internal) gate every cut.
5. If retention/distribution stalls after 5–8 uploads, revisit the on-camera
   hybrid — the algorithm's verdict outranks preference.

## Production loop (per video)

1. Validate idea (outlier filter) → sharpened title/angle.
2. Script with Claude; numbers pulled from real cockpit runs.
3. Capture cockpit footage (screen record `apps/cockpit` desktop shell).
4. OpenMontage: assemble (pipeline per table above), Kokoro VO, 16:9 master + 9:16 cut.
5. `python tools/publish.py out.mp4 --title ... --platforms youtube instagram facebook`
   (IG/FB pending Meta creds; TikTok manual).
6. Log result; feed retention/CTR back into idea selection.

## Video #1 (picked)

Idea #3: **"I coded ICT, SMC, supply & demand and price action into one algorithm.
Then I tested all of them. Receipts inside."**

Why first: it is literally what the esq genesis pipeline already did (~19,931
candidates through the 12-phase funnel), and the exact cold-open that carried the
38k-view source video — a proven hook we own the real version of. Anti-guru payoff:
the honest numbers, whatever they are.

Production:
1. Outlier-check the hook variants (ICT tested / SMC tested / "I tested every
   trading strategy") — confirm starving-audience signature before scripting.
2. Claude script: cold open ≤15s, receipts from real cockpit runs, no profit claims.
3. Operator records A-roll takes against the script (bullet points, not word-for-word).
4. Screen-capture cockpit: genesis funnel, MC displays, alpha-decay panels.
5. OpenMontage assembly → 16:9 long-form + 9:16 shorts cut (funnel-phase moments).
6. `publish.py` → YouTube (live) — IG/FB once Meta creds land.

## Open items

- Operator: record A-roll for video #1.
- Landing page BUILT (`site/index.html`, 2026-07-13): "gauntlet" game-onboarding
  concept — visitor picks a guru strategy, 12-phase funnel executes it on-page
  (Algory-HUD palette from cockpit tailwind config; simulated demo clearly labeled;
  paper-only disclaimer). Concept sources: algory.app design truth + FB reel
  "video-game onboardings, gamify your product". Needs hosting (GitHub Pages) +
  final YouTube channel URL swap once channel exists.
- Create the TraderCockpit YouTube channel (brand channel on existing Google account).
- Meta creds → IG/FB legs live (`meta_setup.py`).
