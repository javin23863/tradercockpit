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

An operator session, if configured, is named `tiktok_session-tradercockpit.cookie` in the same
directory. The current unofficial uploader has no stable post read-back, so TikTok live publishing
remains disabled even when that session exists. A clean uploader exit is only
`uploaded-unverified`.

## Meta and B2

Instagram/Facebook and temporary B2 staging retain their existing operator-managed environment
setup. They are still subject to the same `social-batch/v2` exact-hash approval and live read-back
gate.

Never use an arbitrary file/title command for live publishing; that interface is disabled.
