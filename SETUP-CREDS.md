# One-time credential setup for publishing

After this, `tools\publish.py video.mp4 --title "..." --caption "..."` posts to YouTube + Instagram Reels + Facebook Reels in one command. All values go into `OpenMontage\.env` (already has empty placeholders at the bottom) except the Google JSON file.

## 1. YouTube (~5 min)

1. Go to https://console.cloud.google.com → create project (any name, e.g. `video-pipeline`).
2. **APIs & Services → Library** → search "YouTube Data API v3" → **Enable**.
3. **APIs & Services → OAuth consent screen** → External → fill app name + your email → save. Under **Audience → Test users**, add your own Gmail.
4. **Credentials → Create Credentials → OAuth client ID → Desktop app** → **Download JSON** → save it as `tools\client_secret.json`.
5. Done. The first upload opens a browser once for consent; the token is then cached in `tools\token.json`.

Quota: ~6 uploads/day free. Keep videos `--privacy private` until you've checked them.

## 2. Instagram + Facebook (~20 min, one Meta app covers both)

Prerequisites (in the apps, not the dev portal):
- Your Instagram account must be a **Professional** account (Instagram app → Settings → Account type → switch to Creator or Business — free).
- You need a **Facebook Page** (create one from your FB profile if you don't have one).
- **Link them**: Instagram → Settings → Business tools → Connect a Facebook Page.

Then:
1. Go to https://developers.facebook.com → **My Apps → Create App** → use case: **Business** → create. (Dev mode is fine — no app review needed for posting to your own accounts.)
2. Open https://developers.facebook.com/tools/explorer → select your app → **Generate Access Token** with these permissions:
   `pages_show_list, pages_read_engagement, pages_manage_posts, publish_video, instagram_basic, instagram_content_publish`
3. Make it long-lived: **Tools → Access Token Debugger** → paste token → **Extend Access Token** (60 days).
4. **Automated from here** — run (App ID + secret are on your app's Settings → Basic page):
   ```powershell
   cd C:\Users\MSI\Desktop\OpenMontage-Skill\OpenMontage
   .venv\Scripts\python ..\tools\meta_setup.py --app-id APPID --app-secret SECRET --user-token PASTED_TOKEN
   ```
   This exchanges the token for a long-lived one, fetches the non-expiring Page token + IG business id, and writes `META_PAGE_ID` / `META_IG_USER_ID` / `META_PAGE_TOKEN` into `.env`. No manual Graph Explorer digging.

## 3. Backblaze B2 (Instagram only) — DONE 2026-07-13

Wired automatically: existing B2 key reaches `openmontage-publish-staging`; `B2_*` written to `.env`. Steps below only needed if the key is ever rotated.

### (original manual steps, for reference)

Meta ingests Reels from a public URL, so `publish.py` stages the file on B2 with a 6-hour presigned link. You already have a B2 account.

1. B2 console → **Buckets → Create Bucket** → name e.g. `video-publish-staging` (private is fine, presigned URLs work).
2. **App Keys → Add a New Application Key** → scope it to that bucket → copy `keyID` → `B2_KEY_ID`, `applicationKey` → `B2_APP_KEY`.
3. `B2_BUCKET` = bucket name. `B2_S3_ENDPOINT` = the bucket's S3 endpoint shown on the bucket page, e.g. `https://s3.us-west-004.backblazeb2.com`.

## Verify

```powershell
cd C:\Users\MSI\Desktop\OpenMontage-Skill\OpenMontage
.venv\Scripts\python ..\tools\publish.py ..\OpenMontage\projects\demos\renders\world-in-numbers.mp4 --title test --dry-run
```

All three lines must say `ready`. Then drop `--dry-run` (keep `--privacy private`) for a real end-to-end test.
