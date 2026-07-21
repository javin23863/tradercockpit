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

- Trust-first post-close market recap, published 17:00 US/Eastern after the 16:00 cash close.
  The subject is the session that just closed; the next session is the outlook, not the lead.
  No product pitch in narration.
- One story, one portfolio thesis, **10–12 minutes ALWAYS** (operator 2026-07-21: ad inventory —
  mid-rolls — not editorial preference). MEASURED clone rate is **~197 wpm** (2026-07-21: 1,931
  words rendered 9:47 — under the floor; 2,049 words rendered 10:24), so the band is
  **2,000–2,350 words**; size the script with this number before TTS and expand thin sections
  rather than shipping short. After the VO stage, ffprobe `build/vo-full.wav` BEFORE assemble —
  if it is under 10:00, extend sections with already-receipted unused claim facts and re-record
  only the changed sections (delete their `vo-NN.wav` + `vo-full.wav`; the runner reuses the rest).
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
- Narration uses the existing operator voice through `tools/tts_chatterbox.py` and
  `productions/_voice/operator-clean.wav`.
- Operator approval of the exact `vo.txt` hash is a separate hard gate before TTS, final chart
  capture, scene-plan/visual assembly, or render. Record it in `script-approval.json`; a claims,
  style, or editorial PASS does not substitute for operator script approval.
- Existing public uploads stay public. A new or revised hash always needs its own approval.

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

### Operator + Apollo script contract

Use `## NN slug [APOLLO]` for a whole Apollo section. Untagged sections default to `OPERATOR`.
Use `### APOLLO` and `### OPERATOR` inside a section when a handoff occurs without changing the
visual section. Apollo carries news, official records, statistics, receipts, and the catalyst
calendar; the Operator carries charts, levels, conditions, and judgment. Keep handoffs to six
words or fewer and do not repeat the other speaker's point.

The role split is an editorial contract, not a parser rule. An exact Apollo candidate file needs
operator approval before duo TTS, and the exact `vo.txt` hash needs its own separate approval before
any pilot narration or render. Voice approval never substitutes for script approval.

Run the advisory style audit before narration:

```powershell
<repo>\OpenMontage\.venv\Scripts\python.exe tools\script_style_gate.py productions\<video> `
  --out productions\<video>\build\script-style-audit.json
```

Warnings require an editorial pass, not an automatic rewrite. Never let a style pass alter a
number, name, quotation, attribution, probability, chart level, or causal direction.

## Fast production lane

Target a reviewable flagship within 120 minutes; 150 minutes is the hard escalation point.

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
   - **Mobile legibility standard (operator ruling 2026-07-21 — "I can barely see the numbers"):**
     every chart capture runs `tv_ta_capture.py` with `--expect-last-bar <session> --range-days 100`
     (zooms to ~100 days so candles are phone-readable; +4d right pad). The tool also bumps
     `scalesProperties.fontSize` to 17 and shoots at `--dsf 2`. A full-history chart is a defect
     even if the levels are correct. Do NOT re-attempt price-scale pinning — `setPriceRangeInPrice`
     takes internal units, not prices, and blanks the pane (reverted 2026-07-21; `pane.resetPriceScale()`
     recovers a blanked pane).
   - Symbols whose futures/CFD feed has already reopened (energy after ~20:00 ET, rates/indices
     after ~18:00 ET) will show Monday's settled candle PLUS a small live stub and a live-value
     header. Acceptable only if attested in the run notes; fully avoidable by capturing before the
     reopen — energy symbols first.
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
   than its narration beat — it will not loop entrance/exit animations. After the VO stage, read
   each news beat's length (`ffprobe build/vo-NN.wav`), set that shot's `holdSec` ≥ narration + 2s,
   delete the stale `visuals/<out>.mp4` (the renderer also skips existing outputs), and re-render
   with `fetch_news_shots.mjs --reuse-png` (no refetch, deterministic; arg order is
   `<sources.json> <prod-dir>`). Chart clips are immune — stills are held, not looped.
   ANY script recut re-opens this contract: section durations change, stale holdSec values
   survive in news-shots.json, and the assembler fails mid-run (2026-07-21 recut incident) —
   re-check every news beat's holdSec against the fresh `vo-NN.wav` lengths after re-recording.
5. Generate only changed narration sections with `tools/tts_chatterbox.py`. Reuse all unchanged
   audio and visual assets. Assemble through `tools/produce.py`.

   VO-stage precondition (2026-07-20 incident, reproduced 3×): Chatterbox model load needs
   roughly 4–5 GB of FREE SYSTEM RAM on this 16 GB box. A `0xC0000005` / segfault (exit
   3221225477) right after `[clone] loading Chatterbox on cuda` is RAM pressure, not a code or
   CUDA defect — CUDA smoke tests pass, the weights are intact. Close TradingView Desktop
   (chart work is finished by this stage; it holds ~2 GB) and other Chromium apps, then rerun
   `tools/daily_postclose.py` — it is rerun-safe: gates re-check, approval rewrites hash-bound,
   existing `vo-NN.wav` are skipped.
6. Inspect the actual final export at every declared subject-change boundary plus representative
   midpoints. Check symbol, timeframe, price axis, source/date, containment, safe area, audio,
   runtime, and 9:16 SAR. Declarations and contact sheets alone are not proof.
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
- At 150 minutes, stop and record the exact slow stage, cause, and next delta action.
