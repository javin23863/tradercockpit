# ops — setup and SEO runbooks

Operational reference. None of it governs *what* we make (that's the doctrine at repo root) — it
governs how the machinery is wired.

| Doc | Use it when |
|---|---|
| [`SETUP-CREDS.md`](SETUP-CREDS.md) | Wiring publishing credentials (YouTube OAuth, Meta page/IG, TikTok) into `OpenMontage/.env`. |
| [`SETUP-LEMONSQUEEZY.md`](SETUP-LEMONSQUEEZY.md) | Retired checkout instructions and the current product-manifest boundary. |
| [`META-SEO.md`](META-SEO.md) | Facebook Page + Instagram profile SEO; what the Graph API can and cannot set. |
| [`SEO-CHANNEL.md`](SEO-CHANNEL.md) | YouTube channel + video SEO pack (`tools/channel_seo.py`). |
| [`SEO-SOCIAL.md`](SEO-SOCIAL.md) | Instagram + TikTok connection and profile SEO. |
| [`STUDIO-KIT-INTEGRATION.md`](STUDIO-KIT-INTEGRATION.md) | How `studio-kit/` (clipper, generators) wires into the pipeline. |
| [`COMPLEMENTS.md`](COMPLEMENTS.md) | The free repos filling pipeline gaps (publishing, Kokoro TTS, faster-whisper, MusicGen). |

Token facts worth knowing before you debug an auth error (2026-07-14):
- The Meta page token is **long-lived, `expires_at: NEVER`** — if it fails, the app secret is wrong, not the token.
- YouTube `videos().update` needs the **`youtube` scope** (`token_channel.json`); `token.json` is upload-only and 403s.
