---
name: tiktok-upload
description: Publish an operator-approved TraderCockpit vertical MP4 through TikTok's official free Content Posting API with refreshable OAuth, creator-policy checks, and final post-ID read-back. Use when the user asks to post, upload, verify, or repair TikTok publishing.
---

# TikTok upload

Use TraderCockpit's existing publisher. Do not use Zapier, Postiz, browser cookies, CDP, or an
unofficial uploader.

## Contract

- Work in the canonical TraderCockpit repository and read its `AGENTS.md` first.
- Accept only an approved `social-batch/v2` item whose channel is `tiktok`.
- Treat TikTok as a public action. Do not transmit unless the operator authorized that exact item.
- Keep `tiktok-oauth.json` in operator credential custody outside the repository. Never display,
  copy, log, or save its values in a handoff or vault.
- A provider app, `video.publish` consent, and TikTok audit are one-time provider gates. Do not
  accept terms for the operator. Do not replace a missing provider gate with daily browser login.
- Success requires TikTok's final post ID and stable public URL in `publish_log.json`. A clean HTTP
  upload without that read-back is `uploaded-unverified`, never published.

## Readiness

Run the exact approved item in probe-only mode:

```powershell
python tools\publish.py --batch productions\<run>\social-batch.json --item <approved-id> --platform tiktok --dry-run
```

Interpret readiness:

- `valid`: refreshable OAuth works and creator-info currently permits `PUBLIC_TO_EVERYONE`.
- `private-only`: TikTok has not enabled public API posting for this client/account; do not upload.
- `audit-required`: TikTok's public-posting audit is not recorded as approved; do not upload.
- `absent`: the operator-held OAuth bundle does not exist.
- `custody-unavailable`: this process cannot read operator credential custody; do not weaken ACLs.
- `credential-invalid`: custody exists but is malformed or lacks `video.publish`.
- `verification-error`: token refresh or TikTok provider verification failed.

## Publish

After the final artifact and exact batch item are approved:

```powershell
python tools\publish.py --batch productions\<run>\social-batch.json --item <approved-id> --platform tiktok
```

Read the adjacent `publish_log.json`. Report the platform ID and URL only when its last matching
entry has `status=published`, a non-null `platformId`, and a non-null `url`.

## Free smoke test

This test mocks every TikTok network call and never publishes:

```powershell
python -B -m pytest tests/test_upload_tiktok.py tests/test_publish_readiness.py -q -k tiktok
```

It must prove token rotation, creator/privacy gating, file transfer, final provider read-back, and
the `social-batch/v2` receipt path. Keep the external boundary mocked; tests must cost nothing.
