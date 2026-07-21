# Instagram + TikTok — connection & profile SEO

## Connect Instagram (pipeline leg already built — needs 3 values from you)

Prereq: IG account switched to **Professional (Creator/Business)** and linked to a
Facebook Page (IG app → Settings → Account type; then Accounts Center → link Page).

1. developers.facebook.com → Create App (type: Business) → note **App ID + App Secret**.
2. Graph API Explorer → your app → generate **User Token** with these 6 permissions:
   `pages_show_list, pages_read_engagement, pages_manage_posts, publish_video,
   instagram_basic, instagram_content_publish`.
3. Paste all 3 here — I run `tools/meta_setup.py` and the IG + FB Reels legs go live
   in `publish.py` (B2 staging already verified).

## Connect TikTok

- **Permanent route — official Content Posting API (free; no Zapier, Postiz, Docker, or browser cookies):**
  `tools/upload_tiktok.py` is wired into the existing `social-batch/v2` publisher. It silently
  rotates access tokens from the long-lived refresh token, queries current creator/privacy rules,
  uploads the approved local MP4, polls TikTok processing, and returns the final post ID/URL for
  `publish_log.json`.
- **One-time provider onboarding:** create a TikTok developer app, enable Login Kit and Content
  Posting API with `video.publish`, authorize `@thetradercockpit`, and store the resulting token
  bundle as `tiktok-oauth.json` in the operator credential directory from `ops/SETUP-CREDS.md`.
  TikTok restricts unaudited clients to private posts; record `client_audit_status=approved` only
  from TikTok's portal confirmation. Until then the repository reports `audit-required` and blocks
  the public lane.
- **Readiness:**
  `python tools\publish.py --batch productions\<run>\social-batch.json --item <approved-id> --platform tiktok --dry-run`.
  `valid` means public posting and provider read-back are available. `absent`,
  `custody-unavailable`, `credential-invalid`, `verification-error`, `audit-required`, or
  `private-only` fail closed without uploading.
- The retired cookie/CDP uploader is not a fallback. It caused recurring session loss and could
  not supply a stable post read-back. Do not re-enable it.

## Profile SEO — Instagram (@handle: get `tradercockpit`; fallback `thetradercockpit`)

- **Name field** (searchable, ≠ handle): `TraderCockpit · Markets News`
- **Bio:**
  > Markets, read plainly. Evidence-first analysis of oil, stocks, rates, and geopolitics.
  > News and education, not advice. ⬇
- **Link:** https://javin23863.github.io/tradercockpit/
- Category: Media/News Company. Reels-first; covers = HUD frames
  with 3–4-word hooks; pin the 3 best-performing Reels.
- Hashtag mix per Reel (5–8): #trading #quanttrading #backtesting #ict
  #smartmoneyconcepts #algotrading + 1–2 video-specific.

## Profile SEO — TikTok (@handle: `thetradercockpit`) — news channel, per BRAND.md

- **Name:** `TraderCockpit · Markets News`
- **Bio (80 chars):** `📊 Markets, read plainly. Oil • stocks • rates → your portfolio. Not advice ⬇`
- Link in bio (needs 1k followers for clickable — put URL as text + in comments until then):
  youtube.com/@Thetradercockpit
- TikTok SEO = SPOKEN + on-screen + caption keywords — the cloned VO already says the tickers +
  events; burned word-captions cover on-screen. Caption: first-3s hook + a reply-baiting question,
  trending sound, `#stockmarket #investing #markets #finance #FinTok` + 2–4 topical.
- Post the SAME 9:16 renders as YT Shorts/IG Reels (one render, 4 platforms).

## Cross-platform rules

- Handle consistency: tradercockpit everywhere (or thetradercockpit everywhere).
- Every profile links the landing page; landing page JSON-LD `sameAs` lists all
  profiles (YouTube already in; add IG/TikTok URLs once created).
- First 5–8 posts: the shorts cut from video #1 (cold open / horoscope line /
  refused-receipt) — same starving-audience hooks, per-platform captions.
