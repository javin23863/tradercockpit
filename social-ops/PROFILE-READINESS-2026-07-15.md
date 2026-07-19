# Profile and publisher readiness — 2026-07-15

Read-only live audit from the public profile surfaces plus the local publisher's `--dry-run`.
No profile field, post, credential, or external account was changed. Owner-session screenshots were not
stored because their surrounding navigation exposed unrelated private notifications; the visible DOM and
public metadata below are the audit receipt.

## Live identity

| Surface | Verified live state | Gap before parity | Operator-gated write |
|---|---|---|---|
| YouTube | `@Thetradercockpit` resolves to channel `UCBc6RR49Qk5vtDQaw8BjH3A`; display name `Tradercockpit`. | Description is still the old product/gauntlet pitch and links to the broken path `https://javin23863.github.io/soical/`, not the news-first landing. | Replace description with `ops/SEO-CHANNEL.md` news copy and the canonical landing URL; verify avatar/banner/watermark in Studio. |
| Instagram | `@tradercockpit`; name `TraderCockpit`; market-news bio is live; 5 Reels; 1 follower; link points only to YouTube. | Handle differs from the canonical `@thetradercockpit`; no landing link is visible. | If available, claim canonical handle; add `https://javin23863.github.io/tradercockpit/` as the primary link; verify avatar. |
| Facebook | Page `Tradercockpit`; page asset ID `1135874456287235`; public profile ID `61591774715570`; correct news-first intro; category is `Media/news company`; website points to YouTube. | No claimed username was visible; landing URL is not the website. | Claim the approved handle and make the canonical landing URL primary; keep YouTube as a secondary link if supported. |
| TikTok | Active account is `@trader.cockpit`; display `trader cockpit`; correct news-first bio; 1 follower; 16 likes. `@tradercockpit` returns “Couldn't find this account.” | Both documented handles differ from the active account; no landing link was visible. | Decide one canonical handle, update repo doctrine after it is actually claimed, then add the landing link if the account supports one. |

Current identity is therefore **not parity-complete**. The highest-risk defect is YouTube's stale product
description and broken outbound URL; fix that before sending new traffic.

## Publisher dry run

Command:

```powershell
python tools/publish.py productions/video-02-hormuz/ta-work/05-oil-ta-s0.mp4 `
  --title "READINESS CHECK — DO NOT PUBLISH" `
  --caption "READINESS CHECK — DO NOT PUBLISH" `
  --platforms youtube instagram facebook tiktok --privacy private --dry-run
```

Result after repairing the existing OpenMontage credential-path lookup:

| Lane | State | Next action |
|---|---|---|
| YouTube | `MISSING CREDS` | Operator completes OAuth/client-secret consent; rerun dry run. |
| Instagram | `ready` | Keep exact-asset/fingerprint approval gate; do not public-test. |
| Facebook | `ready` | Keep exact-asset/fingerprint approval gate; do not public-test. |
| TikTok | `MISSING CREDS` | Operator signs the active account into the uploader/CDP path; reconcile the `tradercockpit` cookie label with live handle `trader.cockpit`; rerun dry run. |

The dry run is local configuration validation only. `ready` does not authorize a post.

## Copy receipts for manual profile updates

- Name: `TraderCockpit · Markets News`
- Bio: `Markets, read plainly. Oil, equities, rates, and geopolitics → your portfolio. Primary-source news and education, not advice.`
- Primary link: `https://javin23863.github.io/tradercockpit/`
- YouTube: `https://www.youtube.com/@Thetradercockpit`
- Category: `Media/News Company`

After each operator write, capture a clean public-view screenshot, timestamp it with timezone, rerun the
publisher dry run, and update this file plus the vault from the live surface.
