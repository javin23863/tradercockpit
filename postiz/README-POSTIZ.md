# Postiz — self-hosted scheduler leg (vendored)

[gitroomhq/postiz-app](https://github.com/gitroomhq/postiz-app) (AGPLv3, 33k★).
`docker-compose.yaml` + `dynamicconfig/` are byte-identical to
[gitroomhq/postiz-docker-compose](https://github.com/gitroomhq/postiz-docker-compose)
(vendored 2026-07-13) — update by re-copying from upstream. Local secrets go in
`.env` (gitignored), injected via `docker-compose.override.yaml`.

## What it adds over `tools/publish.py`

| | publish.py (direct) | Postiz |
|---|---|---|
| YouTube / IG / FB now | ✅ immediate CLI | ✅ |
| **TikTok** | ❌ no free route | ✅ own TikTok dev app |
| Scheduling / calendar / queue | ❌ | ✅ |
| X / Threads / LinkedIn / Reddit | ❌ | ✅ |
| Extra infra | none | 8 containers, ~3–4 GB RAM |

Division of labor: `publish.py` stays the render-pipeline's direct arm
(script-driven, zero infra). Postiz = scheduling brain + TikTok + long-tail
platforms once running.

## Bring-up (BLOCKED until Docker exists on this box)

Docker Desktop is NOT installed. Installing needs WSL2 + likely a reboot —
do NOT do this while batv3 workers are running.

1. Install Docker Desktop (WSL2 backend), reboot when safe.
2. `cd postiz && copy .env.example .env` — fill `JWT_SECRET` (any long random
   string) + provider keys you have (Meta app doubles for FACEBOOK_*,
   Google OAuth client doubles for YOUTUBE_*).
3. `docker compose up -d` (first pull ~2 GB images; Temporal stack included).
4. http://localhost:4007 → register the admin account (first user = owner),
   then Settings → Channels → connect accounts via your own dev apps.
5. TikTok: create an app at developers.tiktok.com (Login Kit + Content Posting
   API), paste TIKTOK_CLIENT_ID/SECRET in `.env`, restart, connect.

RAM note: full stack (postiz + postgres×2 + redis + elasticsearch + temporal)
≈ 3–4 GB. Run it after batv3 finishes, or park it on a box with headroom.

## API hook for the pipeline (later)

Postiz has a public API (`/api/public/v1`, key from Settings) — `publish.py`
can gain a `--via postiz --schedule "2026-07-20T18:00"` leg that POSTs the
rendered file instead of hitting platform APIs directly. Add when scheduling
becomes a real cadence, not before.
