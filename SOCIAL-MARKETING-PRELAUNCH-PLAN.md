# TraderCockpit Social and Marketing Operating Plan

- **Status:** Automated execution active in Codex Work
- **Updated:** 2026-07-16
- **Operating timezone:** U.S. Eastern for market events; Asia/Bangkok for production
- **External media spend:** $0
- **Working branch:** `codex/social-marketing-execution`

## Outcome

Finish the audience, publishing, measurement, and launch-handoff system before the consumer
product is ready. At product handoff, the only missing inputs should be a verified
`product-manifest/v1`, real product media, release date, offer/price, checkout, support, refund
terms, and approval of the exact launch claims.

TraderCockpit remains a trust-first daily market-news brand. News videos do not pitch the product.
The landing link may appear in descriptions and profiles; unverified product capabilities never do.

## Public baseline: preserve it

These current uploads remain public. Forward optimization must not delete, private, replace, or
re-upload them:

- YouTube long: https://youtu.be/zFQ3gJCVD6Y
- YouTube Short: https://youtu.be/HW8VpcxvdAY
- Facebook Reel: https://www.facebook.com/reel/1069078669122511
- Instagram Reel: https://www.instagram.com/reel/Da1DaPXALWO/
- TikTok: https://www.tiktok.com/@trader.cockpit/video/7662888296942685460

Corrections to future posts use the documented correction path. Weak performance is never a reason
to erase a factual upload.

## Editorial position

The channel is known for tracing a market-moving event through the portfolio, then naming the
observable condition that confirms or breaks the trade. The host has a view, but the view is
separate from the facts and remains falsifiable.

Coverage includes:

- economic releases, central banks, rates, earnings, and market structure;
- elections, fiscal/trade/regulatory decisions, and political transitions with a market mechanism;
- war, sanctions, defence, energy, shipping, supply-chain, cyber, and infrastructure events with
  exposed assets and a timestamped official catalyst.

The script voice is calibrated from `productions/video-01/vo.txt` and
`productions/video-02-hormuz-v4/vo.txt`, not from a generic “humanizer.” Research and rules are in
`research/ai-script-style-2026-07-16.md` and the vault script-voice guide. Internal verification,
claims receipts, tool names, edit decisions, and production jargon stay out of spoken copy.

## Daily automated lane

One fact pack and one analysis brief feed every surface. Do not create separate research flows for
each platform.

1. Rank official-source stories by portfolio relevance and chartability.
2. Run the TradingView dashboard, choose the strongest confirmation/divergence, and lock one thesis,
   title, and thumbnail.
3. Write the seven-question analysis brief, claims store, and script from the preferred voice
   corpus. Run claims and advisory style audits before TTS.
4. Build an exact narration-beat scene plan. Batch-capture only the required 4–6 charts, 1–3
   contained source visuals, and 0–1 purposeful Godseye shot.
5. Reuse accepted assets and narration; generate deltas only. Inspect the final export at every
   subject-change boundary.
6. Prepare the exact-hash approval batch. Publish only approved hashes to authenticated channels.
7. Record post IDs/URLs, corrections, stage timings, costs, and next-day metrics in the repo/vault.

### Cycle-time diagnosis

Video 03 took about 8 hours 26 minutes from the first live TradingView receipt to accepted master,
and about 13 hours 35 minutes to the corrected cross-platform launch. The bottleneck was rework,
not ten minutes of encoded runtime: the script/voice was not locked before asset production,
13 sections and roughly 50 cuts plus six verticals were built before acceptance, technical gates
passed declarations that did not prove pixels, and publisher credentials were rediscovered after
the master was approved. The forward lane fixes those causes with an early script/style freeze,
4–6 required charts, no more than two pre-approval verticals, delta-only regeneration, final-export
boundary review, and publisher readiness before handoff.

### Runtime budget

Target a reviewable 10–12 minute flagship in 120 minutes; escalate at 150 minutes without lowering
accuracy or visual QA.

| Stage | Budget |
|---|---:|
| Story/package lock | 10 min |
| Facts + TradingView sweep | 20 min |
| Analysis + script | 25 min |
| Claims/style/scene-plan preflight | 15 min |
| Asset capture | 25 min |
| Delta VO + assembly | 25 min |
| Final-export QA + handoff | 20 min |

If a story cannot support the flagship inside the budget, prepare a sourced 45–90 second vertical
instead of padding or entering an open-ended rerender loop. Create at most two initial verticals;
produce additional derivatives only after the long-form master is accepted.

## Automation

`tradercockpit-daily-market-authority` runs Monday–Friday at 17:30 Asia/Bangkok. It owns daily
market-news research, drafts, asset preparation, validation, exact-hash batch assembly,
authenticated publisher readiness, metrics, and vault freshness. It cannot create accounts, enter
new credentials, accept provider terms, alter profiles, invent product facts, or approve a
revised/future hash.

One blocked platform does not stop the rest of the daily workflow.

`tradercockpit-saturday-weekly-market-recap` runs Saturday at 17:30. It uses
`.agents/skills/weekly-market-recap/SKILL.md` to synthesize the completed week's economic and market
news, cross-asset conclusions, and the coming week's official catalysts in the current format. Its
first real run stays with Sol and stops at an approval-ready package; after acceptance it moves to
Luna Max.

`tradercockpit-weekly-social-review` runs Sunday at 18:00 as the no-post analytics/process review.
It refreshes the sanitized four-source dashboard, compares like-for-like history, assesses channel
numbers plus production time, script/voice, visual/editing, QA, corrections, and business-process
receipts, then records one repeat, one stop, and one controlled test for the next week. The collector
and page are `tools/social_analytics.py` and `tools/dashboard.py`; source history is
`social-ops/analytics-history.json`.

The weekday and Sunday lanes run as exact-project `gpt-5.6-luna` automations at `max` reasoning.
Sol retains Saturday's first run, new setup, workflow/contract changes, credentials/terms, and failed
acceptance gates; Luna executes only proven packets under `.agents/skills/social-ops-luna/SKILL.md`.
Email consent health joins that lane only after a real subscribe → confirm → unsubscribe receipt.

Sol remains the final quality owner and pipeline implementer for every delegated run. Luna returns a
candidate plus exact receipts; Sol reviews the actual script, evidence, charts, cuts, audio, final
export, and packaging before the operator's separate exact-hash publication approval can apply. A
quality regression returns to Sol for root-cause pipeline repair; delegation never lowers a gate.

## Current external gates

- TikTok's purpose-created Chrome profile is logged in and the signature short is public. The
  repository-local CDP path remains session-based; if the profile is offline, collection fails
  visibly and the other connected sources continue.
- YouTube Data and Analytics reporting are connected. The live seven-day report includes views,
  estimated watch minutes, average view duration, average percentage viewed, engagement, and
  subscriber changes; no values are inferred.
- The Gmail connector is authenticated for operational mailbox reads and draft/reply workflows.
  The operator approved Buttondown's free plan and the official Google signup is open for sign-in.
  Landing-page collection remains disabled until the account supplies its username and the real
  double-opt-in/confirmed/unsubscribe flow passes. Plausible attribution remains operator-gated.
- Any live profile edit requires exact copy approval and the platform's interactive authorization.
- Product launch assets remain placeholders until the consumer teammate supplies the verified
  manifest and real release-candidate media.

## Measurement

Track stage duration, first-review acceptance, edit distance, claims blocks, corrections, and
approval-to-publication time. Audience metrics are YouTube CTR/first-30-second retention/average
percentage viewed; vertical 3-second hold/completion/replays/shares/saves; qualified comments; and
source-tagged landing visits to confirmed signup. Use a 14-day baseline before setting growth
targets.

The 2026-07-16 baseline is live at `http://127.0.0.1:8788`: YouTube Analytics reports 97 views,
28 estimated watch minutes, 38 seconds average view duration, and 38.15% average viewed for
2026-07-09 through 2026-07-15. Facebook reports 0 observed Reel plays, Instagram 88 observed Reel
views, and TikTok 746 Studio views across the six visible posts. These are source-system counters,
not a cross-platform attribution model; compare the next scheduled snapshot before changing cadence.

## Product plug-in handoff

The consumer teammate supplies:

1. Valid `product-manifest/v1` data.
2. Real screenshots/video from the release candidate and a reproducible demo flow.
3. Verified price, release date, platform/eligibility limits, support, refund terms, and known
   limitations.
4. Approval of the exact launch claims.

Codex validates the manifest, replaces placeholders, reruns claims/accessibility review, prepares
the launch batch, and pauses for exact publication approval.

## Marketing-ready definition

- Daily production reaches a review master within the 150-minute ceiling on a normal story.
- The current public baseline remains intact.
- Each active platform has an exact-hash approval and authenticated publisher path.
- Double-opt-in email and one analytics system pass end to end.
- Profiles match `BRAND.md` and the landing page.
- Corrections, replies, timing, and metrics have real operating receipts.
- The launch placeholder pack is complete and accepts only verified product-manifest fields.

Historical production, rejection, correction, and publication receipts belong in the append-only
vault log. This document states current forward operations only.
