# Daily Run — The Whole Evening, One Flow

**Trigger:** it's a US-market weekday after the 16:00 ET close and the operator wants
today's video ("tonight's run", "do today's video", "post-close run"). This skill is the
ORCHESTRATOR: it sequences the production skill, the judging loop, promotion, and
4-platform distribution — proven end-to-end 2026-07-21 on daily-2026-07-20. Detail lives
in the two child skills; this file owns the ORDER, the commands, and the handoffs.
LLM-agnostic: any model that follows this file ships the same evening.

## Sequence

### 0. Pre-flight (5 min, before anything renders)
- `PYTHONIOENCODING=utf-8 OpenMontage/.venv/Scripts/python.exe tools/publish.py --dry-run`
  — platform auth from the LIVE probe only, never from memory/notes (2026-07-21 scar).
- YouTube quota ledger: ~6 uploads/day total. Tonight spends 1 long-form + up to 2 Shorts
  = 3 minimum; every judging recut that re-uploads spends another. Count before promising.
- Capture window: energy symbols reopen ~20:00 ET, rates/indices ~18:00 ET — charts before
  the reopen = no live-stub attestations. Earlier is strictly better.
- TradingView Desktop must be RUNNING for capture, and CLOSED before TTS (RAM).

### 1. Produce → private upload (skill: **daily-news-video**)
Follow it in full: analysis brief → chart plan + zoomed captures (`--expect-last-bar`,
`--range-days 100`) → vo.txt (2,000–2,350 words @ 197 wpm) → claims.yaml + vo-receipts.yaml
→ scene-plan (per-asset beats) → both gates → **second-model critic pass** (triage against
receipts; receipts win) → runner:
```
CLIP_SKIP_SHORTS=1 PYTHONIOENCODING=utf-8 OpenMontage/.venv/Scripts/python.exe \
    tools/daily_postclose.py productions/daily-<date>
```
Runner output = private YouTube upload + Telegram text AND master video (msgs carry the
actual cut — "i cant judge unless you show me"). Then ffprobe the master: 10:00–12:00 or
recut BEFORE pinging (extend sections with already-receipted unused claim facts; delete
only the changed `vo-NN.wav` + `vo-full.wav`; rerun the runner — it reuses the rest).
Also `Start-Process` the master on the operator's screen.

### 2. Judging loop (operator-paced)
Operator reviews. Every ruling they issue gets encoded SAME-WAVE (gate pattern if
deterministic, skill text otherwise) before or with the fix — that's how the 6 permanent
script rulings landed. Recut mechanics: edit vo.txt → sync vo-receipts verbatim quotes →
scene-plan (single-beat sections auto via `tools/scene_sync.py`, multi-beat hand-tiled,
then `--check`) → both gates → delete changed wavs → rerun runner (new private URL
supersedes; keep old privates until the operator orders deletion — then verify
private-only before delete, re-check after: YT deletes lag read-after-write).

**During judging downtime, write `derivatives-plan.json`** (schema + layout guidance in
the post-approval-derivatives skill; ≤2 segments; layout=fit for chart-dense sections).

### 3. Operator says "approved" → one command
```
PYTHONIOENCODING=utf-8 OpenMontage/.venv/Scripts/python.exe tools/promote_daily.py \
    productions/daily-<date>
```
Does everything: flips the long-form public (read-back verified) → Telegram confirm →
cuts/gates/publishes the verticals to youtube, tiktok, instagram, facebook (per-platform
failure never stops the rest; ledger printed at the end). TikTok "uploaded-unverified"
during its minutes-long review hold is NOT a failure — verify in TikTok Studio before any
retry (retry = double post); the hold clears to the chosen privacy on its own.
Detail + scars: skill **post-approval-derivatives**.

### 4. Close-out (same wave, never "later")
- Vault note: `Desktop\Obsidian Vault From VPS\tradercockpit\tradercockpit\GTM\Videos\
  Daily <date> — <title>.md` — URLs (long-form + all derivative IDs), rulings, scars.
- Memory: project_tradercockpit_news_channel + MEMORY.md line.
- `graphify update .` after tool changes.
- Commit + push `github.com/javin23863/tradercockpit` main — logical chunks, text
  artifacts only (media gitignored; `.gitattributes * -text` keeps hash-bound receipts
  byte-stable; creds never in repo).
- New scars → encode in the owning skill/gate before ending the wave.

## Failure playbook (tonight's proven fixes)
| Symptom | Fix |
|---------|-----|
| Chatterbox segfault 0xC0000005 at load | close TradingView (needs ~4–5 GB free RAM), rerun runner |
| Assembler: news clip shorter than beat | recut re-opened the holdSec contract — bump `news-shots.json` holdSec ≥ VO+2s, delete stale mp4s, `fetch_news_shots.mjs <sources.json> <prod-dir> --reuse-png` |
| "production approval changed after operator approval" | file bytes drifted (e.g. git touched them) — re-mint: `daily_postclose.collect_gates` + `script_approval.machine_approve`, never hand-edit a receipt |
| Master under 10:00 | extend with already-receipted unused claim facts, re-record only changed sections |
| visual_qa caption-over-chart FAIL on a vertical | that segment needs `layout: "fit"` in derivatives-plan.json |
| Platform "blocked" claim from memory | it's stale until `publish.py --dry-run` says so |
