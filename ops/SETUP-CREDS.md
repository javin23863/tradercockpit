# Operator-only publishing credentials

Live YouTube and TikTok credentials live at:

`C:\Users\MSI\.tradercockpit\operator-credentials`

That directory is outside the repository and its ACL grants the Windows operator, SYSTEM, and
Administrators access—not the Codex sandbox account. Do not copy credentials into `tools/`, a
worktree, `.env`, or an agent-readable handoff. `tools/publish.py` never reads repository-local
YouTube or TikTok credentials.

The operator may choose another outside-repository directory by setting
`TRADERCOCKPIT_OPERATOR_CREDENTIAL_DIR` only in the operator-run publishing shell.

## YouTube

The directory contains:

- `client_secret.json`
- `token.json` (upload/read-only scopes)
- `token_channel.json` (broader channel-management scope, when needed)

Run OAuth authorization as the operator with `tools/upload_youtube.py`; live publishing then uses
only an approved `social-batch/v2` item:

```powershell
python tools\publish.py --batch productions\<run>\social-batch.json --item <approved-id> --dry-run
python tools\publish.py --batch productions\<run>\social-batch.json --item <approved-id>
```

The dry run refreshes OAuth when possible and verifies channel
`UCBc6RR49Qk5vtDQaw8BjH3A`. A missing/revoked token or another channel blocks publishing.

## TikTok

The official Content Posting API bundle is `tiktok-oauth.json` in the same directory. It contains
these provider-issued fields and no post payloads:

- `client_key`, `client_secret`
- `access_token`, `refresh_token`
- `access_token_expires_at`, `refresh_token_expires_at` (Unix timestamps)
- `open_id`, `scope` (`video.publish` required)
- `client_audit_status` (`approved` only after confirmation in TikTok's developer portal)

The one-time OAuth authorization occurs only after the operator has created/approved the TikTok
developer app and consented to its provider terms. `tools/upload_tiktok.py` then refreshes access
tokens silently and atomically replaces this file when TikTok rotates either token. Values must
never be pasted into chat, source files, logs, batch manifests, or vault notes.

Public readiness requires both the recorded provider audit and `PUBLIC_TO_EVERYONE` from current
creator-info. A missing/pending audit reports `audit-required`; an account without public creator
visibility reports `private-only`. Neither state transmits the asset. Zapier and Postiz are not part of the production lane.

**Operator ruling 2026-07-20 — CDP uploads ARE authorized for TikTok.** The official Content
Posting API remains preferred (it read-backs), but `tiktok-oauth.json` does not exist and the
`cli.py`/undetected-chromedriver login is broken on this box (Chrome 150, no matching driver). The
established working path is driving TikTok Studio over CDP against the operator's logged-in debug
profile on port 9333 — `tools/handoff/tiktok_post_cdp.cjs`, wired into `publish.py` via
`publish_tiktok()`, which prefers the API and falls back to CDP. This line previously excluded CDP
uploads outright and was superseded; it had already caused one false "TikTok cannot post" call.
Accepted risk: the uploader's own README warns automated posting may get the account banned. Keep
volume human-paced.

```powershell
python tools\upload_tiktok.py
python tools\publish.py --batch productions\<run>\social-batch.json --item <approved-id> --platform tiktok --dry-run
python tools\publish.py --batch productions\<run>\social-batch.json --item <approved-id> --platform tiktok
```

The final command remains a public action and requires the exact approved batch item. Success is
only recorded when TikTok returns a post ID and the publisher derives its stable public URL.

## Meta and B2

Instagram/Facebook and temporary B2 staging retain their existing operator-managed environment
setup. They are still subject to the same `social-batch/v2` exact-hash approval and live read-back
gate.

Never use an arbitrary file/title command for live publishing; that interface is disabled.
