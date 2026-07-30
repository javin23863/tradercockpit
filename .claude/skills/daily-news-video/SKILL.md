---
name: daily-news-video
description: Produce a sourced TraderCockpit market-news video or vertical end to end. Use for today's video, a daily market video, a finance-news script, a long-form market breakdown, or social derivatives from a market story.
---

# Daily news video

Resolve every path from the current TraderCockpit checkout. Read `AGENTS.md`, `BRAND.md`,
`GROWTH-AUTHORITY-PLAYBOOK.md`, the active vault hot cache/index, `market-analysis`, and
`tradercockpit-free-media` before producing. Use only `<repo>/OpenMontage`; external provider cost
is $0.

## Output contract

- Trust-first post-close market recap. Production starts exactly at the 16:00 US/Eastern cash
  close and runs until the evidence, approval, render, and review gates finish (plan roughly five
  hours end to end; there is no fixed early publish clock). The subject is the session that just
  closed; the next session is the outlook, not the lead. No product pitch in narration.
- One story, one portfolio thesis, **10–12 minutes ALWAYS** (operator 2026-07-21: ad inventory —
  mid-rolls — not editorial preference). MEASURED rate is **145 wpm**, so the band is
  **1,450–1,700 words**, which lands a 10.1–11.8 min master once the 12 × 0.45s section gaps
  are counted. **The old "~197 wpm → 2,000–2,350 words" figure was wrong** and could never fit
  the 10:00–12:00 rule at the real rate: it produced a 14.3 min master on 2026-07-27. Size the
  script with 145 before TTS and expand thin sections rather than shipping short. After the VO
  stage, ffprobe `build/vo-full.wav` BEFORE assemble — if it is under 10:00, extend sections with
  already-receipted unused claim facts and re-record only the changed sections (delete their
  `vo-NN.wav` + `vo-full.wav`; the runner reuses the rest).
  Depth comes from the v4 craft moves: drill sector → single names, walk every level's mechanism,
  three-beat chart sections (numbers walk → why mechanism → level framework).
- **Instruments keep their names** (operator 2026-07-21: "The S&P 500 is the S&P 500. It's not
  the referee. The Dow is the Dow. The Nasdaq is the Nasdaq."). No assigned personas, nicknames,
  or role metaphors for instruments — no "the referee", "the fear gauge", "the honesty check",
  "the quiet number". Chart-structure vocabulary (support/resistance/shelf/floor/ceiling) is
  trader speech and stays. The gate BLOCKs the known persona list; when a new one slips through
  review, add it to `PROCESS_PATTERNS["instrument persona"]` in `tools/script_style_gate.py`
  same-wave.
- **No negate-then-replace template** ("if it's not this, it's that" — operator 2026-07-21:
  the AI-tell). "X is priced, not panicked", "that is not A. That is B", "this isn't X anymore —
  it's Y" — state the positive claim directly instead. The gate counts these deterministically
  (corrective contrast, BLOCK at >1). One genuinely earned correction per script is the ceiling.
- Price/technical levels come from TradingView as end-of-day snapshots; events come from dated
  primary sources.
- Charts dominate. Use 4–6 story-required chart clips, 1–3 contained source visuals, and 0–1
  Godseye shot. Do not capture the entire dashboard merely because it was scanned.
- Every chart shot is the completed session: the closing candle printed, the day's full range
  visible, levels drawn off settled prints. No mid-session or pre-open snapshots.
- Narration is the operator's ElevenLabs voice clone through `tools/tts_elevenlabs.py`
  (`eleven_v3`, operator ruling 2026-07-28 after a three-way A/B). Chatterbox is the fallback
  only, and `produce.stage_vo` WARNs when it fires — a Chatterbox render is not the shipped
  voice. Two consequences of v3, already encoded in the tool: request stitching is impossible
  (API 400) and there is **no `speed` parameter**, so pace cannot be dialled at the engine.
  Pace is controlled by the SCRIPT — see the depth contract below.
- Operator approval of the exact `vo.txt` hash is a separate hard gate before TTS, final chart
  capture, scene-plan/visual assembly, or render. Record it in `script-approval.json`; a claims,
  style, or editorial PASS does not substitute for operator script approval.
- Existing public uploads stay public. A new or revised hash always needs its own approval.

## Depth contract — the 2026-07-28 rejection

The operator rejected daily-2026-07-27 as "boring", "surface level", charts "so zoomed in that
no one can see the ticker", "only shows a couple days", "no trend lines", "you don't speak in
levels", "you speak about a ticker and never put it on the screen". Four gates now enforce the
fixes; this section is how to write so they pass on the first attempt.

- **Recital cap — at most 5 distinct feed claims per (section, instrument).**
  `claims_gate` BLOCKs above that, attributing by the `#` fragment of the claim source. The
  07-27 sections cited 8–10 claims of ONE instrument: open, high, low, close, prior, gap,
  open-to-close, return. That is a list, not analysis. **This is also the pace fix**: section 04
  was the slowest section in all three voice A/B variants because it recites five nine-digit
  four-decimal figures, each of which costs seconds of speech and counts as one word. "It's
  boring" and "the speed varies" are the same defect and no model change reaches it.
  Spend the freed words on the mechanism, not more digits.
- **Every level you speak is drawn, and every level drawn is spoken.** `editorial_gate`
  BLOCKs otherwise. On 07-27 each chart drew the prior close and the session low while the
  script spoke five levels of that instrument — three named and never shown, per chart. Plan
  the horizontal lines from the levels the script actually quotes. Trendline anchors are exempt:
  they are swing pivots, not quoted figures.
- **What a beat speaks is DERIVED, not declared.** `spokenSubjects` is written by the same pass
  that writes the narration, so it can be satisfied while violated — 07-27 beat 01-03 declared
  `["nvda"]` and named XLK, the Nasdaq, the VIX and the S&P. The gate now derives instruments
  from the receipts quoted in the beat and from proper names, and BLOCKs an instrument that the
  section never charts. An un-splittable pair clause ("an S&P close below X and a VIX close
  above Y") is allowed when the section shows both charts across neighbouring beats. News beats
  are exempt.
- **Multi-timeframe and trendlines are the standing direction** (weekly/daily/60m, TF-qualified
  subjects; swing-pivot trendlines through `draw_stage`, which is already type-agnostic and
  supports `price2`/`time2`). Not yet gated — write them in.

## Voice authority

Use `productions/video-01/vo.txt` and `productions/video-02-hormuz-v4/vo.txt` as the current
operator-preferred reference corpus. Extract habits; do not copy sentences.

- Lead with the take. Use concrete actors, assets, dates, prices, and mechanisms.
- Make defensible first-person judgments. Sound like a market participant, not a compliance log.
- Vary sentence length and allow humor, edge, contractions, and the occasional aside.
- Keep claims, verification, receipts, editing decisions, and tool names backstage.
- Avoid stock signposting, ornamental triplets, repeated `not X, but Y`, and slogan repetition.
- **Never narrate the act of showing (operator 2026-07-21).** No "on screen", "as you can see",
  "here on the chart", "the headline you're looking at". The VISUAL certifies: the source page
  with its outlet badge, present and not cut off in frame, is the viewer's proof. Speak the
  attribution naturally ("Reuters reported…", "NPR has the shape of it") and put the rigor in
  QA — verify the badge/page is visible and uncropped in the rendered frame. The style gate
  blocks show-narration deterministically.
- A signature line may land once. It must not become the vocabulary of every section.
- End on the level, event, or condition that changes the thesis; add the CTA afterward.

### Daily narration contract — operator only

Every daily-news section is the operator's own voice — the ElevenLabs clone in production, and
`productions/_voice/operator-clean.wav` on the Chatterbox fallback. Do not add `[APOLLO]`,
`### APOLLO`, or another narrator to a daily script. Hybrid Operator/Apollo narration belongs
only to the separate Show lane under its own Show Bible and ruling; it does not apply to daily
or weekly market recaps.

`tools/tts_chatterbox.py` enforces this for `daily-*` folders: stale speaker tags are normalized to
`OPERATOR`, and `--apollo-ref` is rejected. The exact `vo.txt` hash still requires operator
approval before narration or render.

Run the advisory style audit before narration:

```powershell
<repo>\OpenMontage\.venv\Scripts\python.exe tools\script_style_gate.py productions\<video> `
  --out productions\<video>\build\script-style-audit.json
```

Warnings require an editorial pass, not an automatic rewrite. Never let a style pass alter a
number, name, quotation, attribution, probability, chart level, or causal direction.

## Fast production lane

Start at 16:00 US/Eastern. Keep research and editorial preparation within 120 minutes; local
TTS, rendering, and final QA may extend total wall time to roughly five hours.

| Stage | Budget | Receipt |
|---|---:|---|
| Story + title + thumbnail lock | 10 min | one thesis and one package |
| Primary facts + TradingView sweep | 20 min | fact pack and dashboard notes |
| Analysis brief + script | 25 min | seven-question brief and `vo.txt` |
| Claims + style + scene-plan preflight | 15 min | claims PASS, style audit, exact beats |
| Batch asset capture | 25 min | required charts/news/Godseye only |
| Delta narration + assemble | 25 min | cached sections reused |
| Final-export QA + handoff | 20 min | beat-boundary frames, aspect/runtime, hashes |

If the story cannot clear the long-form gates inside the budget, ship an approval-ready vertical
instead of padding or entering an open-ended rerender loop. Do not lower evidence or visual QA.

## Procedure

1. Build the dated primary-source fact pack, including market-relevant political, conflict,
   sanctions, defence, energy, shipping, election, and cyber events.
   **Source tier is a hard constraint (operator ruling 2026-07-21, issued approving
   daily-2026-07-21):** on-screen news shots and on-air attribution come from MAJOR reputable
   outlets only — Reuters (and its wire carriers), Bloomberg/BNN, New York Times, WSJ, FT, AP,
   Al Jazeera, CNBC, NPR, BBC, and official primary sources (Fed, EIA, SEC, company releases).
   Retail-stock-blog tier — fool.com, Benzinga, Investing.com, Seeking Alpha and similar — is
   BANNED from the screen and from spoken attribution, even when FETCHED; use it at most as
   internal corroboration while hunting the same fact on a major. `fetch_news_shots.mjs`
   enforces the on-screen half deterministically (`APPROVED_SHOT_HOSTS` — extend the list only
   with operator-grade outlets). The fact-pack agent must be told to FETCH majors first.

   **The outlet's OWN masthead is the provenance (operator ruling 2026-07-28).** The drawn
   `ASSOCIATED PRESS <date>` band is a FALLBACK, rendered only when no masthead survives, and
   recorded as such in the capture receipt. `fetch_news_shots.mjs` finds the masthead by SHAPE,
   not by tag — AP ships `<bsp-header class="Page-header">`, so `querySelector('header')`
   returned null and the declutter sweep that was written to remove cookie bars removed the
   publication's identity instead. Three more rules from that same shipped video:
   consent buttons are matched by SUBSTRING (AP's reads "I Accept All", an anchored
   `^accept all$` never fired); overlays are swept before EVERY screenshot, not once at load,
   because the floating video widget lazy-loads on scroll; and a declared highlight that is not
   found on the page THROWS — no mp4 is written, because a source card whose highlighted
   sentence is missing is not a receipt for the claim it sits under. Probe the real article for
   the exact sentence: "Nvidia and Micron" was never on the page; it reads "Nvidia fell 5% and
   Micron Technology slumped 2.3%".
2. Run the fixed TradingView dashboard and `market-analysis`. Choose the lead from confirmation or
   divergence. Emit `analysis-brief.md`, then lock title and thumbnail. Lock = RENDER it now
   (never a video frame; design rules = `thumbnails-first-impressions` house skill):
   `node tools/visuals/render_thumb.cjs --out productions/daily-<date>/thumb.png --eyebrow
   "<ASSET>" --num "<$number>" --phrase "<3-5 words, ≠ title>" --dir up|down` — the spec gate
   (`check_thumbnail.cjs`) hard-blocks rule violations. Put the path in every `social-batch.json`
   youtube item as `"thumbnail"`; publish.py sets it on YouTube (fails loud if the file is
   missing — 2026-07-21 silent-drop scar).
2b. **Charts before script (hard order).** Write the chart plan (symbols, timeframes, indicators,
   exact levels/trendlines to draw) and do the TradingView work NOW — adjust indicators as needed
   to make the point; capture working shots as end-of-day snapshots with the closing candle
   printed. The script may only reference charts that already exist from this step. A script
   citing an uncaptured chart is a defect (2026-07-17 incident). Levels talk is conditions and
   invalidations off today's close ("watch X if and only if Y breaks"), never predictions.

   **Derive the levels and trendlines first — do not eyeball them.**
   ```
   PYTHONIOENCODING=utf-8 OpenMontage/.venv/Scripts/python.exe tools/visuals/swing_levels.py \
       productions/daily-<date> --symbols SP:SPX NASDAQ:NVDA ... --tf 1D --count 245 --emit-draw
   ```
   Writes `swing-receipts-<date>.json` and prints `draw` blocks ready to merge into the chart
   plan's stages. It finds 7-bar fractal pivots, clusters them into at most three levels per
   side WITHIN 8% of the last close (a level 10% away is history — the first run surfaced SPX
   levels at 6,550 with price at 7,413, true and useless), and fits the best trendline through
   two same-side pivots spanning ≥15 bars with a recent second anchor. **Never "the last two
   pivots"** — that produced a 7-bar squiggle. Every trendline carries `spanBars`, `touches`,
   `broken` and `projectedNow`: quote the projection, and never call a broken line intact.
   A level's `kind` is where it came from, `position` is what it is now — a swing low price has
   closed below is resistance today, and calling it support is wrong on the page.

   Cite these through `swing-receipts-<date>.json#<SYMBOL>` with predicates `swing_high`,
   `swing_low`, `trendline_anchor`, `trendline_projection`. `claims_gate` checks each value
   against the receipt's own structure and BLOCKs a wrong-side or unmeasured number; swing
   levels count toward the recital cap like feed claims, and `swing_high`/`swing_low` are
   levels for the drawn↔spoken binding, while trendline anchors are exempt from it.

   Capture mechanics (deterministic — do not rely on judgment; 2026-07-20 incidents):
   - **No TV replay for post-close captures.** Between the 16:00 ET cash close and the futures
     reopen (~18:00 ET US10Y/indices feeds, 20:00 ET energy), the native last bar IS the settled
     session. Replay adds a burned "Replay" watermark and pins by bar offset per symbol, which
     lands different symbols on different dates. Capture before the reopen, energy symbols first.
   - **Verify every capture against the feed, not by eye:** the frame's OHLC header must equal
     the `tv ohlcv --count 1` bar for that symbol (same date, same close). Header showing any
     other bar = discard and re-shoot. Then Read one frame per shot as the final human-shaped
     check (levels tagged on axis, no crosshair/menus/watermark).
   - **`tv_ta_capture.py` skips existing outputs silently.** Re-capturing requires deleting the
     shot's `ta-work/*-s*.png`, its `visuals/<out>.mp4`, and `chart-capture-receipts.json` first,
     or the tool no-ops and prints "exists, skip".
   - Run every pipeline python with `PYTHONIOENCODING=utf-8` — cp1252 swallows tool output and a
     failed print reads as a silent success.
   - Dark chart theme is the shipped look (video-05 onward, operator-approved). The old white-
     background override silently no-ops on current TradingView builds; do not chase it mid-lane.
   - **Window: 245 days ≈ 8 months (operator ruling 2026-07-28, "8 months is fine").** This is
     the `--range-days` default; do not pass a tighter one. `--range-days 100` was the real cause
     of the squashed 07-27 charts — not the operator's indicators, which his own reference
     screenshot shows working fine at this width. Candles stay phone-readable
     (operator ruling 2026-07-21 — "I can barely see the numbers"); the tool also bumps
     `scalesProperties.fontSize` to 17 and shoots at `--dsf 2`. Do NOT re-attempt price-scale
     pinning — `setPriceRangeInPrice` takes internal units, not prices, and blanks the pane
     (reverted 2026-07-21; `pane.resetPriceScale()` recovers a blanked pane).
   - **The operator's own chart is captured untouched** (ruling 2026-07-28): his dark theme and
     his two daily indicators, never hidden or restyled for the shot.
   - **Pane-fill gate, at capture.** `tv_ta_capture.py` measures the share of the plot area the
     candles actually span and REFUSES the shot below 0.90. TradingView autoscales to the visible
     data, so candles fill the pane unless something else is driving the price scale — the exact
     07-27 squash, where price sat in the top fifth and the axis ran 5,800–7,800 for an index at
     7,413. The floor is measured, not invented: clean 245-day captures score 0.959–0.989, the
     squashed 100-day ones 0.702–0.880. Re-derive it with `--measure-fill <png>` if the theme
     changes. When it fires, set the price scale to **"Scale price chart only"** so auto-fit
     tracks the main series and every study is ignored — one persisted checkbox, nothing about
     his indicators altered. Fixing it at capture matters: caught in `visual_qa` it is a
     tombstone 90 minutes later, and he sees it before the gate does.
   - **Symbol + current-bar visibility (operator ruling 2026-07-23, method replaced 2026-07-28):**
     every captured chart must show a readable full instrument description/ticker and the newest
     referenced candle at the same time. This is now TradingView's OWN legend
     (`NVIDIA Corporation · 1D · NASDAQ` with the full OHLC line) plus the date axis, preserved by
     fitting the whole pane into frame and padding to 16:9. **The drawn identity card is deleted** —
     the operator's read was that a self-drawn label stands in for provenance the capture cut off.
     `APP_CHROME_PX = 64` is a MEASURED crop of the toolbar, not a guess. A vertical chart uses
     `layout: "chart"` (full approved frame plus a right-edge current-bar close-up). General
     visuals use `layout: "fit"`. A plain `crop` is forbidden in the derivative lane. Inspect the
     rendered 9:16 pixels; a declaration or source frame is not proof.
   - Symbols whose futures/CFD feed has already reopened (energy after ~20:00 ET, rates/indices
     after ~18:00 ET) will show Monday's settled candle PLUS a small live stub and a live-value
     header. Acceptable only if attested in the run notes; fully avoidable by capturing before the
     reopen — energy symbols first.
   - **TVC:GOLD (and any feed whose daily bar rolls at 18:00 ET) has NO settled same-day bar
     after the reopen** — the feed's "last bar" IS the live next-day stub, `--expect-last-bar`
     can pass on it, and the tiny-range bar looks plausibly like a quiet session (2026-07-21
     incident). Detection: header close tracks the live SELL/BUY quote and shows a countdown.
     If it happens, DROP the asset from the script rather than claim it (VIX carried the
     no-fear-bid point that night). Also: TVC:GOLD (~4,080) and OANDA:XAUUSD (~4,007) are
     DIFFERENT gold feeds — never mix them across days.
3. Write `vo.txt` from the brief, the captured charts, and reference corpus. Mint `claims.yaml` and `vo-receipts.yaml`.
   Run `tools/claims_gate.py` and `tools/script_style_gate.py`, read the script aloud, then stop with
   `script-approval.json` absent or `awaiting_human`. Proceed only after the operator explicitly
   approves that exact script hash; later script edits invalidate the receipt.

   Numeric-idiom check (writer-independent, run on every draft): every spoken numeric idiom must
   be derivable from the claimed bar by a stated operation — "an N-dollar range" = high − low;
   "gave it all back" = close ≈ open; "closed on the lows" only if close − low is small relative
   to the range (else "within N points of the low"); "pressing the high" only within a few ticks.
   An idiom that doesn't reduce to bar arithmetic is a chart-true defect (the "five-dollar round
   trip" class). Traders audit these; the gate cannot.

3b. **Independent critic pass (mandatory, model-agnostic).** Before requesting approval, have a
   SECOND model (Codex, or any available LLM that did not write the draft) critique the script.
   Prompt contract: give it `vo.txt`, `analysis-brief.md`, and the newest operator-approved
   reference script; house rules it must not flag (longhand numbers, no predictions, receipt-bound
   figures immutable, topical repetition OK); ask for a ranked list (max 10) of {severity, exact
   quote, defect, one-line fix} covering AI-tells, buried lede, missing mechanism, voice breaks,
   internal contradictions vs the brief, retention risks — and a ship/fix/rework verdict.
   Triage discipline: the WRITER decides each finding against the receipts — a critic finding
   that contradicts a verified receipt is rejected (the 2026-07-20 run rejected a "wrong
   attribution" flag because the captured page showed the Reuters byline); a finding that exposes
   a brief↔script mismatch gets fixed at whichever end the feed says is wrong (same run: the
   BRIEF carried a bad gap %, the script was right). Re-run both gates after edits, then
   `python tools/scene_sync.py productions/<video>` — it re-syncs single-beat narrations from
   the final `vo.txt` verbatim and fails loudly if a multi-beat section no longer tiles.
4. After script approval, write `scene-plan.json` with exact narration beats and visible subjects. Capture assets in
   batches. News uses `contain`; Godseye requires a specific explanatory/evidentiary purpose through
   the latest approved versioned contract.

   **Per-asset chart sync (operator ruling 2026-07-21 — "anytime you're referencing a chart, that
   chart must be on the screen, even if it's for a few seconds"):** a section that walks multiple
   assets gets one beat PER asset, split at the exact sentence where the subject changes — the
   named chart cuts in with its sentence, never lags on the prior asset. Applies to hooks, recaps,
   and map segments too (the 2026-07-20 recut hook is 4 beats: SPX → Brent → 10Y → SPX). Every
   spoken instrument with a captured chart appears when spoken; a sentence naming two instruments
   plays over the one whose level is tagged on the axis. Multi-beat sections must tile the section
   text exactly — `tools/scene_sync.py <prod> --check` verifies concat == section and fails loudly.

   News-clip length contract (2026-07-20 incident): the assembler HARD-FAILS a news clip shorter
   than its narration beat — it will not loop entrance/exit animations. **Pre-size holdSec
   BEFORE the first runner attempt**: narration words ÷ 145 wpm × 60 + ~8s buffer per news beat
   (2026-07-21: placeholder 24s holds vs 50–70s beats would have failed mid-run; generous holds
   cost nothing — the assembler trims to the beat). After the VO stage, read
   each news beat's length (`ffprobe build/vo-NN.wav`), set that shot's `holdSec` ≥ narration + 2s,
   delete the stale `visuals/<out>.mp4` (the renderer also skips existing outputs), and re-render
   with `fetch_news_shots.mjs --reuse-png` (no refetch, deterministic; arg order is
   `<sources.json> <prod-dir>`). Chart clips are immune — stills are held, not looped.
   ANY script recut re-opens this contract: section durations change, stale holdSec values
   survive in news-shots.json, and the assembler fails mid-run (2026-07-21 recut incident) —
   re-check every news beat's holdSec against the fresh `vo-NN.wav` lengths after re-recording.
5. Generate only changed narration sections with `tools/tts_elevenlabs.py`. Reuse all unchanged
   audio and visual assets. Assemble through `tools/produce.py`. Assemble mixes the sound layer
   automatically: music bed from `music_library/` first-sorted track auto-leveled ~21.5 dB under
   the voice, and a bass impact under the final section. **The per-transition whoosh is gone**
   (operator ruling 2026-07-28: "delayed and it just sounds corny"). It was removed from the
   filter AND from the fail-closed missing-check — deleting the file alone blocks the render. New bed tracks need a license row in `music_library/README.md` first;
   craft judgment reference = the `video-editing-craft` house skill.

   VO-stage precondition (2026-07-20 incident, reproduced 3×; sharpened 2026-07-21): the binding
   constraint is **COMMIT, not free RAM** — this box is 16 GB RAM + a FIXED 16 GB pagefile
   (32 GB commit ceiling), and Chatterbox generation needs ~8 GB of commit headroom. Failure
   faces: `OSError 1455 paging file too small` at safetensors load, `0xC0000005` (exit
   3221225477) at model load, or a tiny (<2 MiB) numpy allocation failing MID-SAMPLING. All the
   same cause. Check `Win32_OperatingSystem` commit used/limit, not just free RAM. Close
   TradingView, Firefox/ChatGPT/Chromium apps, orphan codex app-servers; if an esq test run or
   ingest holds multi-GB commit, SERIALIZE behind it (`Wait-Process` then rerun) instead of
   killing production processes. `tools/daily_postclose.py` is rerun-safe: gates re-check,
   approval rewrites hash-bound, existing `vo-NN.wav` are skipped. Standing fix candidate:
   raise pagefile max to 32 GB (reboot, operator-gated).
6. **Read `build/frame-review/beat-NN.png` — one frame per beat of the rendered master — before
   saying one word about the finished video.** `tools/visual_qa.py` samples them at each beat
   midpoint from `build/timeline.json` and hard-fails a blank frame. It also hard-fails when it
   inspected NOTHING: on 2026-07-27 it printed "nothing rendered was inspected" and returned
   PASS, and that single line is how a video with a cookie modal over the source shipped. A gate
   that checked nothing must BLOCK, and its verdict is worthless until you have looked at the
   pixels yourself. Check symbol, timeframe, price axis, source/date, containment, safe area,
   audio, runtime, and 9:16 SAR. Declarations and contact sheets alone are not proof.
7. Derivatives are a SEPARATE post-approval lane: once the operator approves the long-form
   (public on YouTube), invoke the **post-approval-derivatives** skill —
   `tools/cut_derivatives.py <production> [--upload]` cuts ≤2 verticals from the master via
   `derivatives-plan.json`, gates them (copy gate + visual_qa on the production's own
   `shorts/` dir), mints the social-batch/v2 items downstream of the operator approval,
   and publishes through publish.py. Never cut derivatives before long-form approval.

   Verticals + visual QA wiring (2026-07-20 incidents): the unattended runner sets
   `CLIP_SKIP_SHORTS=1` (produce.py) so the long-form never blocks on a shorts-lane defect —
   derivatives are cut in the post-acceptance lane where their QA verdict belongs.
   `visual_qa.gate()` now defaults to the production's own `shorts/` dir (the shared
   `studio-kit/clipper/output/` default remains only for legacy productions — stale clips
   from an old video blocked the 2026-07-20 long-form there).
   Chart derivatives default to `layout: "chart"`; `tools/cut_derivatives.py` rejects lossy
   `crop` plans so neither Sol nor Claude Code can silently cut off the symbol or latest bar.
   If verticals breach the bottom
   safe zone at y≈1772 (bottom margin ~148px), the burn path skipped the fixed caption style
   (`MarginV=64` in clip.js → bottom ≈1493) — fix the style path before re-cutting; do not
   hand-tune per clip. And every ad-hoc `json.load/dump` on this box needs `encoding='utf-8'`
   explicitly — the cp1252 default mojibakes em-dashes in social copy (caught 2026-07-21).
8. Build the exact-hash social batch. It must reference the valid `script-approval.json`.
   Item copy passes through `script_style_gate.audit_text` at publish time. "Backmatter" the
   gate skips = ONLY a paragraph that is exactly the disclaimer, or a CTA — a "Charts:/Sources:"
   paragraph is inspected like content, so if it sits last it triggers "missing invalidation
   level" (no digits). Structure every description: hook → read (sources folded in) → a FINAL
   content paragraph ending on the deciding numeric levels → the exact
   `social_batch.REQUIRED_DISCLAIMER` string alone as its own paragraph (reworded = code-first
   paired change, never copy-side). Pre-validate before running the publisher:
   `script_style_gate.audit_text(copy)['verdict'] == 'PASS'`.
   A publish attempt that fails AFTER machine approval leaves the item `approved` with an
   `approvalSha256` bound to the copy at approval time — any later copy edit hard-fails the
   next run ("approvalSha256 does not match"). After editing a stamped item, reset it to
   `status: draft` and drop `approvalSha256`/`reviewedBy`/`reviewedAt`; the runner re-approves.
   Publish
   only after separate operator approval of the exact platform asset and current channel
   authentication. Record public URLs/IDs; never remove an existing upload as part of routine
   forward optimization.
9. Update the vault current-state pages, index, hot cache, and append-only log.

## Rework rules

- A script change regenerates only affected VO sections and dependent beats.
- A bad chart/news/Godseye shot replaces only that beat.
- A failed social derivative never invalidates an accepted long-form master.
- Keep rejected renders as local receipts until the production is closed; keep public uploads.
- At five hours, record the exact slow stage, cause, and next delta action rather than hiding it.
