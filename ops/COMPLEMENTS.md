# Pipeline Complements — free repos that close the gaps

OpenMontage covers research → script → assets → narration → captions → music → render.
These close the remaining gaps to a full YouTube/Shorts/Reels/TikTok pipeline. All free.

## Publishing

### YouTube (long-form + Shorts) — official API, free
`tools\upload_youtube.py` (this repo) — YouTube Data API v3 via `google-api-python-client` (installed in engine venv).
One-time setup (user, ~5 min):
1. https://console.cloud.google.com → new project → enable **YouTube Data API v3**
2. OAuth consent screen (External, add yourself as test user) → Credentials → **OAuth client ID (Desktop app)** → download as `tools\client_secret.json`
3. First run opens browser for consent; token cached in `tools\token.json`
Quota: 10,000 units/day default = ~6 uploads/day. Shorts = same upload, 9:16 + `#Shorts` in title/description.

### Instagram Reels + Facebook Reels — two routes
- **Official, free**: Meta Graph API content publishing — **one Meta developer app covers both**: IG Reels (`/media` + `media_type=REELS`, needs Instagram Business/Creator account linked to a Facebook Page) and Facebook Reels/Page video (`/{page-id}/video_reels`). Video must be at a public URL for ingestion. Most reliable; setup ~30 min once.
- **Unofficial**: [`subzeroid/instagrapi`](https://github.com/subzeroid/instagrapi) — `pip install instagrapi`, `clip_upload()` posts a Reel from a local file with username/password. Zero Meta-app setup. Risk: unofficial API, account flags possible — use a low-value account first.

### TikTok — two routes
- **Official, free**: TikTok Content Posting API — needs a TikTok developer app + audit approval before public posting (slow, but the legit path).
- **Unofficial**: [`wkaisertexas/tiktok-uploader`](https://github.com/wkaisertexas/tiktok-uploader) — browser-cookie-based upload from a local file. Zero app approval. Same caveat: unofficial, can break on TikTok UI changes.

**Default policy**: the agent renders the vertical file and writes caption/hashtags. Existing repository upload tools may run only after explicit operator approval. Do not add a hosted MCP or publishing service.

## Excluded from the zero-cost stack

- MuAPI, Generative-Media-Skills, and the Anil Matcha scheduler: generation or scheduling ultimately uses MuAPI credits.
- Hosted/remote MCP publishing layers and “free tiers”: they introduce an external service, account, quota, or later billing path.
- Postiz and other scheduler repos: the existing `tools/publish.py` path already covers the required platforms; another scheduler is duplicate infrastructure.
- Wan2GP, ComfyUI, SDXL, Z-Image, and larger local video checkpoints: duplicate or exceed this machine's approved 8 GB VRAM envelope.

## Quality upgrades

- **TTS**: use the project Chatterbox voice clone when `productions/_voice/` is configured; otherwise use OpenMontage Piper. No paid fallback.
- **Transcription/captions**: [`SYSTRAN/faster-whisper`](https://github.com/SYSTRAN/faster-whisper) — word-level timestamps for repurposed footage (Clip Factory, Podcast Repurpose pipelines). `small`/`medium` models fine on 8 GB.

## Disabled heavy options

- **MusicGen**: not installed. Prefer the local music library and properly licensed royalty-free sources.
- **Wan 2.1 1.3B**: disabled after Windows Enterprise App Control blocked the required PyTorch library; no model weights were downloaded. Do not weaken the policy or auto-install another video model.

## Already covered by OpenMontage — don't add repos for these

Stock/archive sourcing, Remotion/HyperFrames composition, FFmpeg post, thumbnails (local SD tool),
word-level captions, royalty-free music detection, avatar/talking-head, dubbing/localization.
