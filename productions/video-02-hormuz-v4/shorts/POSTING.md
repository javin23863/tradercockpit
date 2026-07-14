# Shorts — video-02-hormuz-v4 (2026-07-14)

## ⭐ CORRECTED RE-POST 2026-07-14 (news b-roll letterbox fixed → bars gone, all surfaces)
Root cause was baked-in black bars on news-article b-roll (fetch_news_shots.mjs fit-and-pad).
Fixed to cover-crop; re-rendered visuals + master + shorts (all `1080:1920:0:0`). Old posts retired.
- **Long-form (NEW URL):** https://youtu.be/IJjUNeuJSNE  (old b_EvEGbOHUc → private)
- **YT Shorts (NEW):** hook FmZB2dj5eHY · scenario EQ7pUZF68Jc · transits vweIA4Bc3ak ·
  energy MUPr0x8-cAc · banks tzBCVGqMEvI
- **IG Reels (NEW):** hook Daw02rkgkU1 · scenario Daw09z3lH84 · transits Daw1HvdDJs0 ·
  energy Daw1OVBjREf · banks Daw1UY9jPpY  (verified live: 720×1280, 0 bars)
- **FB Reels (NEW):** 4357168464496095 · 27470633242576762 · 1047470668194415 ·
  1058932556575181 · 1083637374193768
- **TikTok:** 1 of 5 posted (hook) to `@trader.cockpit`. cli.py login broken (undetected_chromedriver
  vs Chrome 150); working path = CDP: `tools/handoff/tiktok_post_cdp.cjs` posts the remaining 4.
---


Source: master-clean.mp4 (https://youtu.be/IJjUNeuJSNE). 9:16 1080x1920, word captions
burned, **right-anchored crop** (keeps TradingView price axis + candles in frame — center
crop cut the axis off). One vertical serves YouTube Shorts / IG Reels / FB Reels / TikTok.
Files in this folder. All chart-true (same claims gate as the long-form). No product pitch.

Common hashtags: #oil #brentcrude #hormuz #stockmarket #trading #investing #markets
#energystocks #geopolitics #tradercockpit

## POSTED to YouTube 2026-07-14 (all public)
- Hook (20% toll): https://youtu.be/Dy_XvwUi6Ng
- Scenario map: https://youtu.be/178YBzc4o2I
- Transits: https://youtu.be/SHVn6IdgIUo
- Energy rotation: https://youtu.be/CfUqwhFc45k
- Bank earnings: https://youtu.be/mu5rd8kVets
- (clip-005 outro tail: SKIPPED, 6.3s)
IG/FB Reels + TikTok: not yet posted (operator-gated / manual).

Ranked best hook first:

## 1 — clip-006-segment-1 (30s) — THE HOOK (globe → 20% toll)
Cold open, strongest scroll-stopper. God's Eye globe + the headline.
Caption: "Trump just put a 20% toll on every ship through the Strait of Hormuz — and oil
ripped 10% in a day. Here's what it means for your portfolio. 🛢️ Full breakdown on the channel."

## 2 — clip-003-hook-3-so-how-high-can-crude (30s) — SCENARIO MAP (best chart)
Brent daily, all 5 desk levels drawn (100/110/120/130/150), full price axis.
Caption: "How high can oil actually go? Every big desk's number — Goldman, JPMorgan, gov
models — on one chart. $100 to $150. None of them models it sitting still. 📈"

## 3 — clip-001-hook-1-is-the-straight-actually-closed (30s) — TRANSITS
"Is the strait actually closed? Wrong question." 5 vessels vs 130/day.
Caption: "Is the Strait of Hormuz actually closed? Wrong question. The right one moves oil. 🚢"

## 4 — clip-002-hook-2-because-83-crude-flows-straight (30s) — ENERGY ROTATION
XLE → Exxon/Chevron single-name walk with chart.
Caption: "$83 crude flows straight into producer earnings. Exxon +4%, Chevron +3% on the
day. The war-premium rotation, one chart deeper. ⛽"

## 5 — clip-004-hook-4-but-the-headline-number-matters (30s) — BANK EARNINGS
JPMorgan preview: the 3 lines that matter more than EPS.
Caption: "5 big banks report before the bell. The headline EPS matters less than 3 lines
inside: net interest income, trading revenue, credit provisions. 🏦"

## SKIP — clip-005-hook-5-if-this-saved-you-a (6.3s)
Outro CTA tail, too short to stand alone. Do not post.

## Publish
- TikTok: no free self-owned API → operator posts file + caption manually.
- YT Shorts / IG Reels / FB Reels: `& $py tools\publish.py <clip>.vertical.mp4 --title "..."
  --caption "... #hashtags" --platforms youtube instagram facebook --privacy public`
  (per-clip; operator-gated — same public-surface confirm as the long-form).
