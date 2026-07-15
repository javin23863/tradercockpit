# TraderCockpit Social & Marketing Pre-Launch Plan

- **Status:** Automated execution active in Codex Work
- **Date:** 2026-07-15
- **Audience assumption:** U.S.-market-focused self-directed investors and traders
- **Operating timezone:** U.S. Eastern for publishing; Asia/Bangkok for production

## Outcome

Finish the audience, publishing, measurement, and launch-handoff systems before the consumer
product is ready. At handoff, the only missing inputs should be the product's verified manifest,
real product media, release date, price/offer, checkout, support, and refund links.

TraderCockpit remains a trust-first financial-news brand. The product is not pitched in news VO,
and no capability or performance claim appears before the consumer product verifies it through
`product-manifest/v1`.

## Execution ownership transition — 2026-07-15

Planning and research are complete. This plan now runs as **Codex Work**, not as a manual checklist.

Codex Work owns the end-to-end automated loop: monitor primary sources, rank stories, prepare fact
packs and analysis briefs, generate platform assets/copy, run claims and format gates, assemble the
exact approval batch, dry-run authenticated publishers, collect metrics, update the repo/vault, and
continue to the next executable item without waiting for routine instructions.

Human involvement is limited to gates automation cannot safely cross:

- Approving the exact assets and copy before a public post or email.
- Completing interactive account login, consent, payment, or credential steps.
- Supplying or approving verified consumer-product facts.
- Choosing between materially different brand, offer, legal, or launch decisions.

An operator gate pauses the affected item only; Codex Work continues every independent safe task.
No parallel manual workflow should duplicate this execution.

### Recurring trigger

Codex automation `tradercockpit-daily-market-authority` is active and runs every day at 17:30
Asia/Bangkok (06:30 U.S. Eastern while daylight saving time is in effect). It re-derives primary-source
facts, refreshes the backlog, prepares the five-channel-plus-email draft batch, runs local gates and
publisher dry runs, and updates the repo/vault. It cannot post, send, authenticate, accept provider
terms, or approve its own output.

## Verified starting point

Already present:

- Brand, voice, thumbnail, and per-platform doctrine in `BRAND.md` and
  `GROWTH-AUTHORITY-PLAYBOOK.md`.
- A sourced daily-news production workflow and fail-closed claims gate.
- Operator-gated publishing paths for YouTube, Instagram, Facebook, and TikTok.
- A fail-closed `social-batch/v1` approval record for YouTube, TikTok, and email.
- A landing page that safely remains a non-transactional waitlist until a valid
  `product-manifest/v1` supplies verified product facts.
- A versioned Godseye evidence boundary; Godseye is optional b-roll/evidence, not the main visual
  lane or a marketing dependency.

Gaps to close before product handoff:

- The waitlist CTA is only a `mailto:` link; there is no real subscriber capture or nurture loop.
- The landing page has no verified analytics/event-measurement hook.
- Instagram and Facebook are not valid channels in `social-batch/v1`, despite existing publisher
  support.
- No dated daily batch exists for today's news.
- Profile/link parity, live credential readiness, and native scheduling must be rechecked from the
  platforms rather than inferred from old handoffs.
- A corrections policy, daily KPI scorecard, launch asset pack, and product handoff checklist are
  not yet complete.
- Buttondown and Plausible code paths are complete and locally tested, but their live accounts,
  paid-plan/terms consent, exact Buttondown username, Plausible snippet, redirect settings, and real
  receipts remain operator gates.

## P0 — publish today's market map

China's National Bureau of Statistics released the freshest confirmed macro story at 9:00 a.m.
Bangkok. The immediate post should lead with the divergence inside the report:

- Q2 real GDP grew 4.3% year over year and 0.9% quarter over quarter, versus 5.0% year over year
  in Q1.
- First-half industrial value added rose 5.4% and high-tech manufacturing rose 13.3%.
- Consumer-goods retail sales rose 1.3%, while fixed-asset investment fell 5.7% and real-estate
  development investment fell 18.0%.
- The portfolio question is whether production/export strength can continue to offset weak
  domestic demand. China equities/CNH, industrial metals, Asian exporters, global cyclicals, and
  luxury/consumer exposures are confirmation checks—not confirmed reactions.

The second same-day package is the U.S. inflation/policy handoff: June PPI at 8:30 a.m. ET /
7:30 p.m. Bangkok, the Bank of Canada decision at 9:45 a.m. ET / 8:45 p.m. Bangkok, Fed Chair
Kevin Warsh's Senate testimony at 10:00 a.m. ET / 9:00 p.m. Bangkok, and the Beige Book at
2:00 p.m. ET / 1:00 a.m. Bangkok on July 16.

Use the final primary-source news brief for copy and links; do not insert market prices until read
from the live chart/feed.

Source pack: [`productions/FACTS-2026-07-15.md`](productions/FACTS-2026-07-15.md).

### Today's minimum viable package

1. **Publish now:** one 45–60 second clean vertical: “China grew 4.3%—but the headline hides two
   economies.” Use the NBS figures and label every portfolio channel as a confirmation check.
2. **Before 7:30 a.m. ET:** schedule a separate U.S. setup: “CPI cooled. PPI, the Bank of Canada,
   and the Fed are next.”
3. **After the 8:30 a.m. ET PPI release:** update the facts, chart the rates/equity reaction, run
   the claims gate, and publish the reaction cut only after operator approval.
4. **By noon ET:** publish the existing 10–12 minute flagship if the story passes the asset-class
   litmus and the v4 quality floor. If it does not, the sourced vertical is the daily post; do not
   pad a weak long-form story.
5. Fan the same approved 9:16 master to YouTube Shorts, Instagram Reels, Facebook Reels, and
   TikTok with platform-specific copy. No foreign watermark.
6. Stay available for the first 30 minutes after each post. Answer factual questions with sources;
   do not give individualized financial advice.
7. Log publish time, correction count, 3-second hold/completion where available, shares/saves,
   landing visits, and confirmed waitlist signups after 24 hours.

## P0 — next 48 hours

| Work | Owner | Acceptance test |
|---|---|---|
| Replace `mailto:` with one hosted double-opt-in form | Codex Work; operator only for provider auth/choice | Test signup arrives, confirms, lands on thank-you state, exports cleanly, and records source/UTM. No custom backend. |
| Install one analytics system | Codex Work; operator only for account consent | Page view, waitlist CTA click, confirmed signup, YouTube click, and product CTA events are visible in a test report. Do not install competing trackers. |
| Make profile identity consistent | Codex Work audit/drafts; operator for interactive profile writes | Name, handle, avatar, bio, category, and landing link match `BRAND.md` on every active channel. Record screenshots/date. |
| Recheck account and publisher readiness | Codex Work | Dry-run or native scheduled draft succeeds for each active platform; expired tokens/cookies are recorded as operator gates. No public test post. |
| Add Instagram and Facebook to the existing social batch gate | Codex Work | Same fingerprint and claims-gate rules apply to all five distribution channels plus email; the existing self-test and one new channel-parity check pass. No new scheduler. |
| Publish source/correction rules | Codex Work; operator approves public wording | Every post shows source/date; material errors receive a timestamped correction in the description or pinned comment and the batch/log is updated. No silent factual edits. |

## P1 — seven-day operating system

### One daily source package, reused everywhere

Every day starts with one fact pack and one analysis brief. From that source, create:

- One “Market Map” vertical: what happened, why it matters, assets affected, what is next.
- One 10–12 minute flagship when a single story clears the topic and quality gates.
- Two vertical cuts from the flagship: the fact/reaction and the portfolio mechanism.
- One 200–300 word email brief with source links.
- One YouTube title/thumbnail package prepared before production.
- Platform-specific captions and first comments, all in one approval batch.

Do not build independent research/script flows for each platform.

### Daily cadence

| Eastern Time | Bangkok Time | Action |
|---|---|---|
| 6:30 a.m. | 5:30 p.m. | Rank stories by portfolio relevance, primary-source quality, and available charts. |
| 7:00 a.m. | 6:00 p.m. | Lock the one idea, title, thumbnail, hook, and expected event times. |
| Event + 10 min | Event + 10 min | Publish a facts-only flash only when the primary release is live and checked. |
| Event + 60–120 min | Event + 60–120 min | Publish the approved vertical with chart/feed-confirmed levels. |
| By noon | By 11:00 p.m. | Publish the flagship if it clears the quality gate. |
| First 30 min | Same | Reply, capture FAQs, and escalate corrections. |
| Next day | Next day | Record metrics and choose one lesson for the next package. |

### Weekly rhythm

- Sunday: week-ahead economic calendar with official release links and exact times.
- Monday–Thursday: daily market map plus the strongest event reaction.
- Friday: “what actually changed this week” recap; compare the week-ahead watch list with outcomes.
- Maintain a rolling 10-story backlog, but choose breaking relevance over the backlog.

### Editorial standards

- Primary sources first: BLS, Federal Reserve, BEA, Census, EIA, Treasury, SEC filings, exchange
  notices, and company investor-relations releases.
- Every number carries a source and as-of time. Chart = levels; release/news = event.
- Separate confirmed fact, mechanism, and scenario. Scenarios need triggers; no predictions.
- Visible source/date on news visuals. Each named asset receives its own correct symbol/timeframe.
- No product pitch in news VO. The landing link belongs in the description/caption.
- Maintain a visible corrections record and never delete a correction merely because engagement
  is weak.

## P1 — owned audience and nurture

The waitlist should also be the daily-news list; do not create two databases before product launch.

Build three emails now:

1. **Welcome:** what TraderCockpit covers, source standard, posting cadence, and not-advice notice.
2. **Daily/weekly brief template:** the one market fact, portfolio transmission map, next catalyst,
   and source links.
3. **Product-ready placeholder:** announces nothing until the product manifest supplies verified
   capabilities, platforms, offer, checkout, support, and refund facts.

Tag subscribers by source campaign only (`youtube`, `instagram`, `facebook`, `tiktok`, `direct`)
and keep export/consent receipts. Defer behavioral segmentation until the list is large enough to
justify it.

## P1 — measurement

Use one small scorecard; views alone are not success.

### Trust and operations

- Percentage of posts published on time.
- Claims-gate pass, block, and correction counts.
- Source/date coverage on every factual asset.
- Draft acceptance and edit distance.
- Approval-to-publication time.

### Audience quality

- YouTube: impressions CTR, first-30-second retention, average percentage viewed.
- Verticals: 3-second hold, completion, replays, shares/saves, and qualified comments.
- Email: confirmed subscribers, delivery, clicks, replies, unsubscribes, and corrections.
- Funnel: source-tagged landing visits → CTA clicks → confirmed waitlist signups.

Collect a 14-day baseline before setting numeric growth targets. Optimize the weakest step in the
funnel, not the largest vanity metric.

## P2 — finish before the product arrives

Prepare these artifacts with explicit placeholders, not invented product facts:

- A launch landing-page copy block mapped field-for-field to `product-manifest/v1`.
- A 60-second product-demo storyboard with slots for real capture and verified capability labels.
- Launch-day long-form outline, two vertical hooks, email, captions, thumbnail brief, FAQ, and
  correction/rollback copy.
- A small press/creator kit: brand assets, channel one-liner, audience promise, source policy,
  contact, and product fields marked `PENDING VERIFICATION`.
- A list of relevant market-news creators/guests for editorial collaborations. Draft outreach;
  do not claim a product partnership or send product-demo pitches before a real demo exists.
- A two-week launch content calendar that can be scheduled only after the release date is real.

## Product plug-in handoff

The consumer-product teammate supplies:

1. A valid `product-manifest/v1` with `generatedAt`, status, product name/summary, assistant state,
   verified capabilities, platforms, offer, CTA/checkout, support, and refund links.
2. Real product screenshots/video captured from the release candidate.
3. A demo account or reproducible scripted flow.
4. Verified price, release date, eligibility/platform limits, support SLA, refund terms, and known
   limitations.
5. Approval for the exact launch claims.

Codex Work then validates the manifest, replaces media placeholders, reruns accessibility and
claims review, generates the launch approval batch, and pauses only for operator approval before
publishing.

## Definition of marketing-ready

- Real double-opt-in capture and welcome email tested end to end.
- One analytics source records the complete landing-to-signup path.
- Every active profile matches the brand and links to the landing page.
- Every active distribution channel is covered by an exact-asset human approval gate.
- Daily, weekly, correction, reply, and metric-log procedures have been run on real posts.
- At least 10 sourced story candidates and two evergreen packages are ready.
- The launch asset pack exists with product facts clearly marked as placeholders.
- The `product-manifest/v1` handoff fields and validation command are agreed with the product
  teammate.
- No unverified product, performance, availability, pricing, or checkout claim is public.

When all items pass, the only remaining work is the product plug-in handoff above.

## Explicitly deferred

- A custom CMS, custom scheduler, custom email backend, or second analytics system.
- Unsupervised public posting or automatic replies.
- Paid acquisition before organic content-to-waitlist conversion is measurable.
- Referral/affiliate mechanics before the offer and economics exist.
- New social platforms before the current channels sustain the daily cadence for 14 days.
- Product testimonials, case studies, and performance claims before real users and approved
  evidence exist.
