# Social batch boundary

Codex Work may prepare a daily `social-batch/v1` file containing YouTube, Instagram, Facebook, TikTok, and email drafts. It does not approve or publish them.

An operator may change an item to `approved` only after reviewing the exact copy and asset and adding a repository-relative `claims-gate.json` whose verdict is `PASS`. The gate must record at least one checked section and no blocked claims. Generate the approval fingerprint after those fields are final, then store it as `approvalSha256` with `reviewedBy` and a timezone-qualified `reviewedAt`. Any later copy, asset, or gate change invalidates approval.

```powershell
python tools/social_batch.py validate social-ops/daily-batch.json
python tools/social_batch.py fingerprint social-ops/daily-batch.json --item ITEM_ID
python tools/social_batch.py ready social-ops/daily-batch.json
```

The `ready` command is a fail-closed handoff for a future authenticated publisher. It does not post, send email, handle credentials, or bypass platform review.

## Daily loop

1. Build one timestamped fact pack from primary sources and one platform-neutral analysis brief.
2. Create one clean master asset and platform-specific copy in a dated batch.
3. Run the claims gate and format checks. Keep every item `draft` while the asset or gate can still change.
4. Present the exact asset and copy to the operator. Approval is recorded per item with a fingerprint.
5. Run `ready`, then pass only its output to the authenticated publisher. A dry run is not publication.
6. Record the public URL, publish time, corrections, and next-day metrics in `metrics.csv`.

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

## External service gate

The landing page is pre-wired for Buttondown double opt-in and one Plausible tracker through
`docs/prelaunch-config.v1.json`. Both remain disabled until the operator creates/approves the accounts,
supplies the Buttondown username and Plausible site snippet/domain, configures the pending and confirmed
redirects, and verifies a real consent receipt. Do not add a second tracker or custom email backend.
