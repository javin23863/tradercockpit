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

- **Route C — makiisthenes/TiktokAutoUploader (WIRED 2026-07-14, recommended, free, no Docker):**
  Installed at `../TiktokAutoUploader` (venv + playwright-chromium ready). Wrapper
  `tools/upload_tiktok.py`; integrated into `publish.py --platforms ... tiktok`.
  **One-time (manual, interactive Chrome):** `cd ../TiktokAutoUploader && python cli.py login -n tradercockpit`.
  After that, cookies persist in `CookiesDir/` and uploads are automatic. `publish.py --dry-run`
  reports cookie readiness. Unofficial cookie tool — carries an account-ban disclaimer (operator accepted).
- **Route A — Postiz (vendored `postiz/`):** official Login Kit + Content Posting API, but needs
  Docker + TikTok app review. Heavier; use only if Route C's cookie flow gets throttled.
  1. developers.tiktok.com → register app → add **Login Kit + Content Posting API**
     → note Client Key + Secret (TikTok reviews the app; sandbox posts = private
     until audit passes, ~days).
  2. Blocked locally until Docker exists (install needs a reboot — after batv3).
     Then: `postiz/.env` ← TIKTOK_CLIENT_ID/SECRET, `docker compose up -d`,
     connect the account at localhost:4007, publish/schedule from there.
- **Route B — manual (works today):** produce.py shorts land in
  `studio-kit/clipper/output/` → post from phone. Caption files sit next to clips.

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
