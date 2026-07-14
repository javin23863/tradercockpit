# Social batch boundary

ChatGPT Work may prepare a daily `social-batch/v1` file containing YouTube, TikTok, and email drafts. It does not approve or publish them.

An operator may change an item to `approved` only after reviewing the exact copy and asset and adding a repository-relative `claims-gate.json` whose verdict is `PASS`. The gate must record at least one checked section and no blocked claims. Generate the approval fingerprint after those fields are final, then store it as `approvalSha256` with `reviewedBy` and a timezone-qualified `reviewedAt`. Any later copy, asset, or gate change invalidates approval.

```powershell
python tools/social_batch.py validate social-ops/daily-batch.json
python tools/social_batch.py fingerprint social-ops/daily-batch.json --item ITEM_ID
python tools/social_batch.py ready social-ops/daily-batch.json
```

The `ready` command is a fail-closed handoff for a future authenticated publisher. It does not post, send email, handle credentials, or bypass platform review.
