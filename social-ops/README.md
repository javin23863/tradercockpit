# Social batch boundary

Codex Work may prepare a daily `social-batch/v1` file containing YouTube, Instagram, Facebook, TikTok, and email drafts. It does not approve or publish them.

An operator may change an item to `approved` only after reviewing the exact copy and asset and adding a repository-relative `claims-gate.json` whose verdict is `PASS`. The gate must record at least one checked section and no blocked claims. Generate the approval fingerprint after those fields are final, then store it as `approvalSha256` with `reviewedBy` and a timezone-qualified `reviewedAt`. Any later copy, asset, or gate change invalidates approval.

```powershell
python tools/social_batch.py validate social-ops/daily-batch.json
python tools/social_batch.py fingerprint social-ops/daily-batch.json --item ITEM_ID
python tools/social_batch.py ready social-ops/daily-batch.json
```

The `ready` command is a fail-closed handoff for a future authenticated publisher. It does not post, send email, handle credentials, or bypass platform review.

The operating week is Monday–Friday daily market news, Saturday weekly recap plus next-week official
catalysts, and Sunday analytics/process review with no post. Proven weekday/Sunday repetitions are
delegated through `.agents/skills/social-ops-luna/SKILL.md` to exact-project `gpt-5.6-luna` / `xhigh`.
Saturday uses `.agents/skills/weekly-market-recap/SKILL.md`; its first run stays with Sol until real
acceptance. New providers and changed workflows stay with Sol; email consent health is not delegated.

Sol owns final consumer-facing quality and pipeline implementation after every Luna run. Luna output
is a candidate until Sol inspects the actual artifact and receipts; Sol acceptance and operator
exact-hash publication approval are separate required gates. Quality regressions return to Sol.

## Daily loop

1. Build one timestamped fact pack from primary sources and one platform-neutral analysis brief.
2. Draft the sourced script from the approved voice corpus; run claims/style checks and a read-aloud.
3. Stop for explicit operator approval of the exact script hash in `script-approval.json`. No TTS,
   final asset capture, assembly, or render is allowed before this separate gate passes.
4. After script approval, create one clean master asset and platform-specific copy in a dated batch.
5. Run the claims and format checks. Keep every item `draft` while the asset or gate can still change.
6. Present the exact asset and copy to the operator. Publication approval is recorded separately per item with a fingerprint that includes the script-approval receipt.
7. Run `ready`, then pass only its output to the authenticated publisher. A dry run is not publication.
8. Record the public URL, publish time, corrections, and next-day metrics in `metrics.csv`.

## Corrections

Every factual post carries a visible source and as-of date. For a material error, stop any queued reuse,
set the affected batch item back to `draft`, add a timestamped `CORRECTION` to the description or pinned
comment, update the source artifact and claims gate, and mint a new approval fingerprint. Never silently
replace a factual claim. Deleting a post is reserved for harmful, legally sensitive, or platform-required
cases and must be recorded in the batch notes and metrics log.

## Metrics

`metrics.csv` is the single prelaunch scorecard. Add one row per asset/channel after 24 hours; leave
unavailable fields blank. Keep source campaign values to `youtube`, `instagram`, `facebook`, `tiktok`, or
`direct`. Establish a 14-day baseline before setting growth targets.

The automated source snapshot lives in `analytics-latest.json`; idempotent weekly history lives in
`analytics-history.json`. Both are sanitized and contain no tokens, cookies, or client secrets. Refresh
them and the local operations dashboard with:

```powershell
OpenMontage\.venv\Scripts\python.exe tools\social_analytics.py collect
py tools\growth_experiments.py validate
py tools\growth_experiments.py report --json
py tools\dashboard.py --no-open
```

On Sunday, refresh platform analytics first, validate `growth-experiments.v1.json`, then review its
`metrics.csv` joins and advisory verdict in the dashboard. Record an operator decision in the manifest
only after reviewing the evidence. Reuse a winning component under a new experiment ID; publication
still requires the existing exact-hash approval gate. The growth module never writes decisions,
publishes content, activates ads, or spends money.

Sources are YouTube Data/Analytics APIs, Facebook Page + Video Insights, Instagram Business Insights,
and the operator's logged-in TikTok Studio content table. Meta and TikTok post counters are snapshot
counters; weekly changes become comparable after the next scheduled collection. YouTube's connected
Analytics report supplies seven-day watch time, average duration, average percentage viewed,
engagement, subscriber changes, and daily/video rows.

## External service gate

The authenticated Gmail connector supports operational mailbox reads and draft/reply workflows. It
is not the subscriber list or consent authority and does not enable bulk marketing sends.

The landing page is pre-wired for Buttondown double opt-in and one Plausible tracker through
`docs/prelaunch-config.v1.json`. Buttondown's free plan is operator-approved and its official Google
signup is open for sign-in; collection remains disabled until the account supplies its username and
the pending/confirmed/unsubscribe flow passes with a real consent receipt. Plausible remains disabled
until its account, snippet, and domain are approved. Do not add a second tracker or custom email backend.
