# Meta (Facebook + Instagram) SEO — match @Thetradercockpit YouTube channel
Updated 2026-07-14.

## ⭐ 2026-07-14 update (supersedes stale notes below) — see `BRAND.md`
- **Brand art is rendered + ready** in `tools/visuals/brand/`: `avatar.png` (800, one pic for all
  4 platforms), `banner.png` (YT 2560×1440), `fb-cover.png` (1640×624), `watermark.png`, `logo.png/svg`.
  Direction = "Instrument" gauge, **landing red/black** (`#FF1744` on `#08030a`). Regen: `node
  tools/visuals/render_brand.cjs`. Thumbnails: `node tools/visuals/render_thumb.cjs`.
- **Instagram IS connected now** (@tradercockpit, id 17841449822516311). Re-probed 2026-07-14:
  `media_count = 5`, and all 5 are OUR corrected Hormuz Reels — **nothing off-brand to delete.**
  (The "old posts" were the wrong-aspect ones, already deleted+replaced earlier.) IG bio/name/pic
  still have **no API** → paste copy from `BRAND.md`, set `avatar.png` manually.
- **FB Page cover + profile picture: DONE via API 2026-07-14** — pushed with a fresh user token
  (page token pulled via `/me/accounts`, written to `.env`; the long-lived exchange is still
  broken on the stale `META_APP_SECRET`, so page tokens keep expiring ~hours — for durable auto-
  refresh, still drop a correct app secret from FB app → Settings → Basic). BOTH endpoints work:
  `POST /{page}/photos`(published=false)→`POST /{page}?cover=<id>` for cover, and
  `POST /{page}/picture` (source=file) DOES set the Page profile picture (corrects earlier note).
  Live: picture + cover show the new red/black art. **FB category + @handle remain manual.**
- **TikTok is now wired** (was manual) — see `SEO-SOCIAL.md`. Uploader installed at
  `../TiktokAutoUploader`; one-time `python cli.py login -n tradercockpit`; then
  `publish.py --platforms ... tiktok`.

---
## (earlier notes — partially superseded above)

## Facebook Page "Tradercockpit" (id 1135874456287235) — DONE via API ✅
Page had 0 posts (nothing to clean) and empty metadata. Applied via Graph API:
- **about** (tagline): "Markets, read plainly. Oil, equities, rates, and the geopolitics
  moving them, translated into what it means for your portfolio. News & education only.
  Not financial advice."
- **description**: full channel blurb + YouTube + landing links.
- **website**: https://www.youtube.com/@Thetradercockpit
- **5 Reels posted** (Hormuz shorts): reel ids 2232678197271919, 926026737193961,
  1741622720509642, 27511227695210255, 1065543425967247.

### FB — you must do manually (NOT API-editable):
- **Category**: currently "Product/service". Graph API rejects category edits
  ("parameters do not match any fields that can be updated"). Change in
  Page → Settings → Page info → Categories → set **"Media/News Company"** (primary)
  + "Financial Service". SEO-relevant.
- **Username/handle**: set @thetradercockpit (Page → Edit → Username) to match YouTube/IG.
- **Profile pic + cover**: use the channel logo/banner so the three surfaces match.

## Instagram — BLOCKED at the API, mostly manual regardless
**Why blocked (corrected 2026-07-14):** the IG account IS already Professional — that's not
the gap. The gap is the **Page↔Instagram connection**: the Graph API only reaches an IG
account that is connected to a Facebook Page as that page's `instagram_business_account`.
Re-probed with fresh tokens: the one Page (Tradercockpit) has no `instagram_business_account`,
no `connected_instagram_account`, and an empty `instagram_accounts` edge; the business
portfolio's IG edges are empty too. So the Professional IG is linked to the personal profile
(Accounts Center) or to no Page — not to THIS Page.

**Fix (operator, interactive — needs IG login, can't be done via API):**
- Page **Tradercockpit** → Settings → **Linked accounts** → Instagram → **Connect account**
  → log into the IG account → confirm.
- OR business.facebook.com → Settings → Accounts → **Instagram accounts → Add** → log in →
  connect to the Tradercockpit Page (add into business portfolio id 2349612978898520).
Then re-probe / re-run meta_setup.py → `META_IG_USER_ID` fills, publishing works.

**Hard limit even after linking:** the Instagram Graph API has **no endpoint to edit bio,
name, or profile picture.** Those are manual-only in the IG app. (Media DELETE *does* work
for API-created media — confirmed 2026-07-14, DELETE /{ig-media-id} → success. So Reels we
post can be removed via API; only profile/bio edits are manual.)

### One-time link (unlocks API *publishing* for future auto-posts):
1. IG app → Settings → Account type → switch to **Professional (Business or Creator)**.
2. IG app → Settings → Business tools / Linked accounts → **connect the "Tradercockpit"
   Facebook Page**.
3. Re-run: `.venv\Scripts\python ..\tools\meta_setup.py --app-id 1415836063940108
   --app-secret <CORRECT_SECRET> --user-token <fresh>` — auto-fills META_IG_USER_ID.
   (Note: the app secret currently in .env is stale — "Error validating client secret".
   Grab the real one from developers.facebook.com → app → Settings → Basic.)

### IG cleanup checklist (manual, in the app):
- Archive/delete off-brand old posts that don't fit the markets-news channel.
- Keep grid consistent: chart-forward thumbnails matching the video style.

### IG profile copy — paste these:
- **Name field** (searchable, 30 char): `TraderCockpit · Markets News`
- **Username**: `@thetradercockpit` (match YouTube; claim if free)
- **Category**: Media/News Company (or Financial Service)
- **Bio** (150 char):
  ```
  📊 Markets, read plainly.
  Oil • equities • rates • geopolitics → your portfolio.
  News & education, not advice.
  ▶️ Daily breakdowns on YouTube 👇
  ```
- **Link**: https://www.youtube.com/@Thetradercockpit (or the landing
  https://javin23863.github.io/tradercockpit/ — use IG "links" for both).

### IG content (once linked, publish.py handles it):
The same 5 vertical Reels in `productions/video-02-hormuz-v4/shorts/` post via
`publish.py --platforms instagram` (B2 staging already wired). Captions in
`productions/video-02-hormuz-v4/shorts/POSTING.md`.
