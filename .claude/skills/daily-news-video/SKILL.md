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

- Trust-first market news. No product pitch in narration.
- One story, one portfolio thesis, 10–12 minutes only when the story earns it.
- Price/technical levels come from TradingView; events come from dated primary sources.
- Charts dominate. Use 4–6 story-required chart clips, 1–3 contained source visuals, and 0–1
  Godseye shot. Do not capture the entire dashboard merely because it was scanned.
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
   divergence. Emit `analysis-brief.md`, then lock title and thumbnail.
2b. **Charts before script (hard order).** Write the chart plan (symbols, timeframes, indicators,
   exact levels/trendlines to draw) and do the TradingView work NOW — adjust indicators as needed
   to make the point; capture working shots. The script may only reference charts that already
   exist from this step. A script citing an uncaptured chart is a defect (2026-07-17 incident).
   Levels talk is conditions and invalidations ("watch X if and only if Y breaks"), never
   predictions.
3. Write `vo.txt` from the brief, the captured charts, and reference corpus. Mint `claims.yaml` and `vo-receipts.yaml`.
   Run `tools/claims_gate.py` and `tools/script_style_gate.py`, read the script aloud, then stop with
   `script-approval.json` absent or `awaiting_human`. Proceed only after the operator explicitly
   approves that exact script hash; later script edits invalidate the receipt.
4. After script approval, write `scene-plan.json` with exact narration beats and visible subjects. Capture assets in
   batches. News uses `contain`; Godseye requires a specific explanatory/evidentiary purpose through
   the latest approved versioned contract.
5. Generate only changed narration sections with `tools/tts_chatterbox.py`. Reuse all unchanged
   audio and visual assets. Assemble through `tools/produce.py`.
6. Inspect the actual final export at every declared subject-change boundary plus representative
   midpoints. Check symbol, timeframe, price axis, source/date, containment, safe area, audio,
   runtime, and 9:16 SAR. Declarations and contact sheets alone are not proof.
7. Prepare at most two initial vertical derivatives from the approved thesis. More derivatives are
   made after the long-form cut is accepted, not before.
8. Build the exact-hash social batch. It must reference the valid `script-approval.json`. Publish
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
