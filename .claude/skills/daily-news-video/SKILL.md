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

## Standing rules (operator, 2026-07-13 — do not relax)
- Trust-first news. Product NEVER pitched in VO; landing link in description only.
- Topic litmus: name the affected asset class in one sentence, or skip the topic.
- 8+ minutes (mid-roll ads); optimize retention, never pad.
- Every number traces to the day's fact pack; UNVERIFIED items are banned from script.
- Machine persona (kokoro bm_george): reports, never hypes, never predicts, not financial advice.
- NO upload without operator review of master.mp4.

## Steps

1. **Fact pass** — spawn the `fact-pack` agent (see `.claude/agents/fact-pack.md`) with
   the day's story. Save result as `productions/video-NN-<slug>/FACTS-<date>.md`.
2. **Script** — write `productions/video-NN-<slug>/vo.txt`: `## NN visual-slug` sections,
   numbers written longhand for TTS, cold open ≤15s, 12-14 sections for 8+ min.
   Model on `productions/video-02-hormuz/vo.txt`.
3. **VO** — `& $py tools\produce.py productions\<vid> --stage vo --voice bm_george`
4. **God's Eye b-roll** — write `tools/visuals/shots-<slug>.json` (schema + cinematography
   rules in vault [[God's Eye Footage Engine]]; also comments in godseye_capture.mjs).
   Launch app with `--remote-debugging-port=9222`, run capture, **Read one extracted
   frame per shot to verify** before accepting. Copy keepers into
   `productions/<vid>/visuals/` with section-number prefixes.
5. **Charts** — edit CHARTS/CARDS dicts in `tools/visuals/render_visuals_v02.py` for
   today's sections (copy verified numbers only), run `fetch_chart_data.py`, then the
   renderer with `-u`, **sequentially — never two renders at once (shared cfg.json)**.
6. **Assemble** — stages `captions`, `assemble`, `shorts`. Verify: ffprobe master.mp4
   duration ≈ VO length; extract + Read 2 frames.
7. **Publish gate** — write title/description/tags into `SCRIPT-VIDEO-NN.md`
   (patterns in SEO-CHANNEL.md), then STOP and ask operator to review master.mp4.
   On operator go: `& $py tools\publish.py <master> --title "..." --category 27 --privacy public`
8. **Log** — update vault: `wiki/videos/` note, `_meta/hot.md`, `_meta/log.md`.

## Failure notes
- Wedged card render = concurrent cfg.json race; kill by exact PID, rerun sequentially.
- God's Eye shot failure auto-reloads once; stale in-app FRED oil dock stays off-frame.
- vo.txt edited after VO stage → rerun VO (regenerates all sections).
