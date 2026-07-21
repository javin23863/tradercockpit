# HANDOFF — video-03-weekly-2026-07-18

First **weekend-review** production (Saturday weekly, Ciovacco-style). Skill:
`.claude/skills/weekend-review/SKILL.md` (new this session, references daily-news-video).

## State
- [x] Fact pack `FACTS-2026-07-18.md` (week 07-13..07-17; conflicts → §7 banned list)
- [x] `analysis-brief.md` (7-question brainstorm; 3 divergences promoted = spine)
- [x] `claims.yaml` 32 claims (15 chart-read 1W + 17 event) — TOP-LEVEL LIST format
- [x] `vo.txt` 15 sections ~2,870 words ≈ 15.1 min @191wpm; `vo-receipts.yaml` 75 receipts
- [x] **Gate PASS** `build/claims-gate.json`
- [x] 7 q-cards `visuals/NN-qcard.png` (qcard.html via render_thumb --html/--size)
- [x] `thumb.png` + title/desc/tags in `SCRIPT-VIDEO-03.md`
- [x] VO 15.2 min (vo-full.wav)
- [x] 14 TA chart clips + frame-verified (SPX/UKOIL levels drawn, chart-true)
- [x] Reuse copies done (8)
- [x] Vertical captures (spx/ukoil/smhspx/ndx + title card), icon-strip+toolbar cropped (-56 right, -110 top)
- [x] captions+assemble: master-clean.mp4 15:15 1920x1080, 5 spot frames verified
- [x] 5 shorts via vsrc lane, all 1080x1920 SAR 1:1; whisper caption mangles hand-fixed in slice SRTs, re-burned
- [x] OPERATOR APPROVED via Telegram 2026-07-18 ("Approved — docker needed for postiz")
- [x] PUBLISHED YouTube 6/6 (daily quota spent): long-form https://youtu.be/a-d0ND20Dzc ;
      shorts cC6TZCTJ3l4 / clxfXQ2FqmU / rSF2Ou-CkvA / ANwcW1udU64 / 2LmAWN4yQCs
- [ ] IG/FB Reels BLOCKED — **Meta APP-LEVEL block** (2026-07-18 probe): ALL Graph calls,
      including app-token (app_id|app_secret) calls, return "API access blocked" code 200.
      NOT a token problem — no re-mint helps. Operator fix: developers.facebook.com → Trader
      Cockpit app (1415836063940108) → violations/appeal, or new app → rewire .env → repost.
      Also learned: Chrome 136+ IGNORES --remote-debugging-port on the default profile —
      browser-drive of live sessions is dead as a lane.
- [ ] TikTok BLOCKED: no session cookie anywhere. Same debug-Chrome login (tiktok.com), then
      tools/handoff/tiktok_post_cdp.cjs pattern.
- [ ] Postiz: containers UP (localhost:4007) but DB EMPTY — no org/channels; operator must
      register + connect before it can post anything. publish.py direct remains the working lane.

## Gotchas hit this build
- claims_gate.py contract: claims.yaml = top-level LIST; vo-receipts.yaml = {"NN": [{quote,claim,attributed}]},
  quote verbatim substring; ordinals/cardinals ("first", "two thousand") count as number
  regions — rhetorical ones REPHRASED, honest ones covered by sentence-quotes.
- No replay pinning needed on Saturday: last completed 1W bar = the reviewed week
  (verify bar time via ohlcv before claims — done, wk-of-07-13 bar close matches Friday).
- Ratio symbols (AMEX:RSP/AMEX:SPY etc.) work directly as tv symbols on 1W.
- Operator directives this session: keep standing indicators ON for weekly charts
  (no blank/clean charts); weekend format = pure charts + q-cards, 15-20 min.
- Chart-read weekly %s differ from press %s (instrument + window): UKOIL +17.35% chart vs
  press "12-14%" (Sept futures) — chart is SoT for levels, press %s in banned list.

## Caption-fix recipe (whisper number mangles)
Slice SRTs in studio-kit/clipper/output/clip-00N-*.srt; fix text; re-burn with the
clip.js vsrc ffmpeg args (see this repo's clip.js reframeVertical vsrc branch or the
burn() one-liner in session log). Known mangles: index levels -> "$75 .75", Hormuz ->
"Farmers", homophones ("wheat's high").
