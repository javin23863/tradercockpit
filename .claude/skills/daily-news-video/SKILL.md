---
name: daily-news-video
description: >
  Produce today's TraderCockpit finance-news video end-to-end: fact pass, machine-persona
  script, God's Eye b-roll capture, real-data chart cards, VO/captions/assemble/shorts,
  publish gate. Use when the user says "today's video", "daily video", "make the news
  video", or names a market story to cover.
---

# daily-news-video

Repo: `C:\Users\MSI\Desktop\OpenMontage-Skill`. Engine python:
`OpenMontage\.venv\Scripts\python.exe` ($py below). Knowledge base:
`C:\Users\MSI\Desktop\TraderCockpit-Vault` (read `_meta/hot.md` first).

> **✅ HALT LIFTED (operator, 2026-07-14).** Skills proven; production resumed. Carry the
> bootcamp doctrine into every cut: TA charts dominant + full price axis, visible news source
> badges, GE sparingly, StockedUp portfolio-first voice (vault [[Production Halt — Skills First]],
> [[TradingView TA Runbook]], [[Script Voice Guide — StockedUp Decode]]). Upload still gated on
> operator review of master.mp4.

> **⭐ QUALITY BASELINE (operator, 2026-07-14): v4 IS THE FLOOR.** `productions/video-02-hormuz-v4/`
> (vo.txt + claims.yaml + vo-receipts.yaml + ta-work/ + HANDOFF.md) is the reference build —
> published https://youtu.be/IJjUNeuJSNE (bar-free re-upload; original b_EvEGbOHUc is private). Every future video matches it on: chart-true numbers
> through the claims gate, replay-pinned frame-verified TA charts, expanded StockedUp script
> craft (see "Script craft" below), cloned VO, 10-12 min. Anything beyond v4 is improvement;
> anything below it is a regression — do not ship.

## Standing rules (operator, 2026-07-13 — do not relax)
- Trust-first news. Product NEVER pitched in VO; landing link in description only.
- Topic litmus: name the affected asset class in one sentence, or skip the topic.
- **10-12 minutes** (operator 2026-07-14: "8+mins always 10-12 best"); optimize retention, never pad.
  Cloned voice measures **~191 wpm** → target **1,900-2,300 words** across 13 sections. Size the
  script with this number, not a guess — v4's first cut ran 9.3 min at 1,779 words and had to be expanded.
- Every number traces to the day's fact pack; UNVERIFIED items are banned from script.
- Voice = CLONED OPERATOR (2026-07-14, bm_george retired as "too robotic"): VO stage is
  `productions/_voice/.venv-clone/Scripts/python.exe tools/tts_chatterbox.py <prod>
  --ref productions/_voice/operator.wav` (drop-in for produce.py --stage vo; same build/
  artifacts). Persona rules unchanged: reports, never hypes, never predicts, not financial advice.
- Captions = YouTube auto (operator 2026-07-14): DELIVERABLE IS `master-clean.mp4` (no
  burned captions). Still run --stage captions (shorts clipper needs the SRT).
- NO upload without operator review of master.mp4.
- **Visual doctrine (reject #2/#3, vault [[Video Format v2 — StockedUp Model]]):** live
  TradingView TA charts are the DOMINANT visual (full price axis, never cut off); news
  clippings MUST show a visible source badge (outlet + date); God's Eye SPARINGLY
  (~15% runtime, b-roll only — cold open / one flyover / outro), never the main lane.
- **Chart accuracy (operator 2026-07-14, traders WILL roast mismatches — see vault
  [[TradingView TA Runbook]] "Accuracy discipline"):** every asset named in VO gets its
  OWN chart shot; stated timeframe == chart TF (verify `chart_get_state` + read the
  frame header); symbol shown == asset discussed; and on-chart numbers == spoken
  numbers — read levels OFF the chart (`ohlcv`/`quote`/pine lines) and script THOSE
  (chart = source for LEVELS, news = source for EVENTS; v3 died on live drift: VO said
  "~79" from a morning news snapshot, chart showed the 83 close). Date-pinned story →
  `replay` to the broadcast date so the last bar is the day you narrate.
- **Language = portfolio-first, StockedUp voice** (vault [[Script Voice Guide — StockedUp Decode]]).
  Talk about the viewer's money and where the action is; ban "how it affects your screen".
- **Brand + growth doctrine are MANDATORY inputs (operator 2026-07-14):** read `BRAND.md` and
  `GROWTH-AUTHORITY-PLAYBOOK.md` (repo root) before packaging. Non-negotiables from them:
  - **Package BEFORE you produce (Galloway):** decide the ONE idea, render the thumbnail, write the
    title — *first*. Thumbnail via `node tools/visuals/render_thumb.cjs --out <prod>/thumb.png
    --eyebrow "<TICKER>" --num "<$/%>" --phrase "<≤5 words, *red* on the key word>"` (landing
    red/black, gauge corner). Title = primary keyword in first ~60 chars.
  - **Identity:** red `#FF1744` on black `#08030a`, monospace, gauge mark. Assets in
    `tools/visuals/brand/` (regen: `node tools/visuals/render_brand.cjs`). Unified handle
    **@thetradercockpit** everywhere.
  - **Verticals ship clean + hook-first (Mosseri/TikTok):** first 3s hook, NO foreign watermark,
    burned word-captions, our VO. TikTok cut wants a trending sound + a reply-baiting first comment.
  - **Core hashtags:** `#stockmarket #investing #markets #finance #FinTok` + 2-4 topical.
- **Publish fans to FOUR platforms (operator 2026-07-14):** `tools/publish.py ... --platforms
  youtube instagram facebook tiktok --thumbnail <prod>/thumb.png`. TikTok is opt-in via the sibling
  `TiktokAutoUploader` (one-time `cli.py login`; wrapper `tools/upload_tiktok.py`, `--dry-run`
  reports cookie readiness). Public uploads STILL operator-gated.

## Steps

1. **Fact pass** — spawn the `fact-pack` agent (see `.claude/agents/fact-pack.md`) with
   the day's story. Save result as `productions/video-NN-<slug>/FACTS-<date>.md`, and
   mint the claim store `claims.yaml` from it (schema: id, subject, predicate, value,
   unit?, as_of, source, retrieved_at, status). Claims are minted HERE ONLY.
2. **Script** — write `productions/video-NN-<slug>/vo.txt`: `## NN visual-slug` sections,
   numbers written longhand for TTS, cold open ≤15s, 12-14 sections for 8+ min.
   Model on `productions/video-02-hormuz/vo.txt`. **Write in the StockedUp voice** (vault
   [[Script Voice Guide — StockedUp Decode]]): signature line, portfolio-first, conditional
   plays, price RANGES not single ticks. Write `vo-receipts.yaml` alongside:
   every number-bearing fragment quotes → claim id (single_source claims need
   `attributed: true` and on-air attribution).
2b. **ONTOLOGY GATE (blocking)** — `& $py tools\claims_gate.py productions\<vid>`.
   BLOCK = fix script or claims until PASS; never proceed on BLOCK. The gate verdict
   (`build/claims-gate.json`) is the receipt that everything the machine says traces
   to a sourced, dated claim.
2c. **Script craft (v4 baseline — what "good" reads like, model on
   `productions/video-02-hormuz-v4/vo.txt`):**
   - Every chart section = three beats: the NUMBERS walk (Fri close → Mon close → % —
     all read off the feed), the WHY mechanism (one paragraph of plain-English causality:
     "an oil shock is an inflation shock, and inflation keeps the Fed careful"), and the
     LEVEL FRAMEWORK ("Above, Friday's close at X. Below, Monday's low at Y. Between
     those lines, everything is noise.").
   - Drill down inside sections: sector fund → its single-name heavyweights (XLE → XOM/CVX),
     index → its pain trade (SPX → NVDA), asset → its driver chart (gold → 10Y yield).
     Multiple visuals per section via `NN-` prefix files, sorted order = narration order.
   - Scenario sections: EVERY spoken level drawn ON the chart with axis tags — a spoken
     "one fifty" with no 150 line is a chart-true FAIL. Walk the map bottom-up, name whose
     model each line is, close on the asymmetry ("nobody models it sitting still").
   - Outro = recap ("Quick recap so you walk in ready") over REUSED chart clips
     (copy 2 chart clips to 13-a/13-b so the GE outro clip never loop-restarts), then
     signature close.
   - Rhetorical number-words trip the gate ("two lines", "re-price first", "a quarter
     that ends") — rephrase them; only mint receipts for honest data claims. Arithmetic
     derived from a chart claim (83→100 = "roughly a twenty percent move") maps to that claim.
3. **VO** — `productions/_voice/.venv-clone/Scripts/python.exe tools/tts_chatterbox.py
   productions/<vid> --ref productions/_voice/operator-clean.wav`. Wrapper SKIPS existing
   wavs and **parses vo.txt ONCE at launch** — any text edit after launch means: wait for
   the run, delete only the affected `vo-NN.wav` + `vo-full.wav`, rerun (only those regen).
   Measure the result: if vo-full is under 10 min, expand sections and regen the deltas —
   do not ship under the band.
4. **God's Eye b-roll** — write `tools/visuals/shots-<slug>.json` (schema + cinematography
   rules in vault [[God's Eye Footage Engine]]; also comments in godseye_capture.mjs).
   Launch app with `--remote-debugging-port=9222`, run capture, **Read one extracted
   frame per shot to verify** before accepting. Copy keepers into
   `productions/<vid>/visuals/` with section-number prefixes.
5. **Charts (PRIMARY visual lane).** Two options:
   - **Live TradingView TA (preferred, dominant — the v4 recipe, per symbol):**
     `tv` CLI = `node C:\Users\MSI\repos\tradingview-mcp\src\cli\index.js`. Launch
     `scripts\launch_tv_debug.bat`, MAXIMIZE, `tv ui panel watchlist close` (panel eats
     ~290px of canvas). Then per chart: `tv symbol X` → `tv timeframe 1D` →
     `tv replay start --date <broadcast+1>` (replay persists across symbol switches; the
     +1 gets the COMPLETE prior session bar) → `tv ohlcv --count 2` (Fri+Mon bars — these
     are THE numbers the script speaks; mint clm-chart-* from them) → `tv draw shape -t
     horizontal_line -p <level> --time <bartime> --overrides '{"linecolor":"#26A69A",...}'`
     (Fri close teal #26A69A, second level amber #F0B90B, scenario reds #EF5350) →
     `node tools/visuals/cdp_chart_shot.mjs <out.png> 2560 1440 [--fit]` (--fit only to
     reset a panned view; NEVER --fit after a manual price-scale set) → **Read the png:**
     header = symbol · 1D · exchange, last close matches ohlcv, level tags on axis, no
     crosshair/context-menu/tooltip → `tv draw remove <id>` before switching symbol.
     Off-screen scenario levels: `tv ui eval` →
     `getPanes()[0].getMainSourcePriceScale().setAutoScale(false); setVisiblePriceRange({from,to})`,
     shoot, then `setAutoScale(true)`. Drawings do NOT survive an app relaunch.
     Stills→clips: ffmpeg loop pattern in v4 HANDOFF.md (scale -2:1080, right-crop keeps
     axis, drawtext ticker label top-left, h264_nvenc cq19).
     Full command reference + hard ceilings in vault [[TradingView TA Runbook]].
     **Plan cap: Basic = 2 indicators/chart
     (operator's Supertrend + SMC fill both) — do NOT try to `indicator add`; it silently
     fails + pops an upsell.** ALWAYS restore at the end: remove drawings, autoscale on,
     `tv replay stop`, back to TVC:UKOIL 1D, watchlist reopen. NEVER `.remove()` a TV DOM
     node (use `display:none`) — see Failure notes.
   - **Static cards (fallback):** edit CHARTS/CARDS dicts in `tools/visuals/render_visuals_v02.py`,
     run `fetch_chart_data.py`, then the renderer with `-u`, **sequentially — never two
     renders at once (shared cfg.json)**.
6. **Assemble** — stages `captions`, `assemble`, `shorts`. Heed `WARN ... loop restart
   visible` for real-footage clips (still-image clips are immune) — pad that section with
   reused chart clips (`NN-a-*.mp4`) instead of shipping a visible restart. Verify:
   ffprobe **master-clean.mp4** duration ≈ VO length; extract + **Read 5 spot frames**
   (hook, one TA chart, one news card, one late chart, outro) — no burned captions, no
   crosshair, labels readable.
   **Shorts lane:** run with `CLIP_ANCHOR=right` env (`CLIP_ANCHOR=right $py tools\produce.py
   <vid> --stage shorts`) — chart-dominant footage needs the RIGHT-edge crop to keep the
   price axis; a center crop cuts the axis + candles off (v4 first shorts pass wasted this way).
   Clipper writes to `studio-kit\clipper\output\` (accumulates across runs — grab the newest
   6 by mtime, copy into `productions/<vid>/shorts/`). **Read one frame per kept clip.** Drop
   any clip under ~8s (outro-tail picks are too short to stand alone). Best hook is usually
   the cold-open segment (the clipper labels it `segment-1`, not `hook-1`).
   **Aspect check (mandatory before posting):** `ffprobe -select_streams v:0 -show_entries
   stream=width,height,sample_aspect_ratio,display_aspect_ratio` on each vertical MUST read
   `1080,1920,1:1,9:16`. A non-1:1 SAR (e.g. 1331083:1330425) = FB/IG render it stretched —
   clip.js now forces even crop width + `setsar=1`, but verify. To replace already-posted
   Reels: FB `DELETE /{video-id}` and IG `DELETE /{ig-media-id}` both work via the page token
   for API-posted media, then repost the corrected file. (IG bio/profile edits have NO API —
   manual only.)
7. **Publish gate** — write title/description/tags into `SCRIPT-VIDEO-NN.md`
   (patterns in SEO-CHANNEL.md; chapters computed from sections.json durations + 0.45s gaps),
   then STOP and ask operator to review **master-clean.mp4** (master.mp4 = burned captions,
   never ship). Render the thumbnail FIRST (see Standing rules → package before produce).
   On operator go: `& $py tools\publish.py <master-clean> --title "..." --description "$DESC"
   --tags ... --thumbnail <prod>\thumb.png --platforms youtube --privacy public` with
   `PYTHONIOENCODING=utf-8` set (emoji in description breaks cp1252 extraction). Shorts fan out
   to all four: `--platforms youtube instagram facebook tiktok` (tiktok opt-in, cookie required).
8. **Log** — update vault: `wiki/videos/` note, `_meta/hot.md`, `_meta/log.md`.

## Failure notes
- Wedged card render = concurrent cfg.json race; kill by exact PID, rerun sequentially.
- God's Eye shot failure auto-reloads once; stale in-app FRED oil dock stays off-frame.
- vo.txt edited after VO stage → delete ONLY the changed sections' vo-NN.wav + vo-full.wav,
  rerun tts_chatterbox.py (skips existing = only deltas regen).
- **Chart shots: hands OFF the TV window while shooting.** The operator's real mouse over
  the canvas swaps the OHLC header to the hovered bar + draws a crosshair into the frame;
  a stray right-click leaves a context menu in-shot (`tv ui keyboard Escape`, re-shoot).
  cdp_chart_shot.mjs parks the pointer (after connect AND right before the screenshot),
  but physical mouse movement between those wins races — verify every frame by Reading it.
- **TV: NEVER `.remove()` a DOM node** (modals/overlays) — TV portals are shared; removing
  one killed the indicators-dialog app-wide until relaunch. Use `style.display='none'` ONLY.
- **TV CLI screenshot can wedge** (node process hangs, other commands still work): print
  exact PID → kill exact PID → retry once → if still wedged relaunch via
  `scripts\launch_tv_debug.bat` (layout is cloud-saved, restores). Relaunch comes up
  UNMAXIMIZED (narrow chart) — maximize before captures; tv_ta_capture.py handles both aspects.
- News shots: source badge (outlet + date) is mandatory — verify it's burned + readable
  (fetch_news_shots.mjs). Declutter is MINIMAL (iframes + small fixed overlays); broad
  class-hiding nuked an article container (blank page) — do not reintroduce it.
- **News shots MUST fill the frame (operator flagged 2026-07-14):** `fetch_news_shots.mjs`
  kenBurns uses `scale=...:force_original_aspect_ratio=increase,crop=3840:2160` (COVER, not
  `decrease`+`pad:black`). The old fit-and-pad left ~8% black bars on wider-than-16:9 article
  crops, which carried into the 9:16 shorts (traders notice). Verify: `cropdetect` every news
  visual reads `1920:1080:0:0`, and each short reads `1080:1920:0:0`. Re-render cached shots
  without refetching: `node fetch_news_shots.mjs --reuse-png <news.json> <prod>`.
