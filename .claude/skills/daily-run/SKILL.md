# Daily Run — The Whole Evening, One Flow

**Trigger:** it's a US-market weekday after the 16:00 ET close and the operator wants
today's video ("tonight's run", "do today's video", "post-close run"). This skill is the
ORCHESTRATOR: it sequences the production skill, the judging loop, promotion, and
4-platform distribution — proven end-to-end 2026-07-21 on daily-2026-07-20. Detail lives
in the two child skills; this file owns the ORDER, the commands, and the handoffs.
LLM-agnostic: any model that follows this file ships the same evening.

## The button

```
PYTHONIOENCODING=utf-8 OpenMontage/.venv/Scripts/python.exe tools/daily_lane.py
```

That is the whole night: preflight → TradingView up → init → charts → script → gates →
**AWAITING_HUMAN** → TTS → render → frame review → PRIVATE upload → Telegram. Verticals are
not a separate skill — `tools/promote_daily.py` cuts, gates and publishes them to four
platforms in one command after the operator approves.

**On any night the operator sleeps through the approval window, the output is a held approval,
not a video** (his ruling 2026-07-28, kept deliberately). `check_stage` returns
`AWAITING_HUMAN` and the lane exits 0 with a Telegram notice; nothing renders and nothing
uploads. Publishing is always operator-gated: the lane never passes `--allow-public`.

**Re-arm criteria** for `tradercockpit-daily-autostart-a`/`-b` (currently **Disabled**) — all
four, no partial credit: (1) the acceptance table in `docs/DAILY-LANE-OVERHAUL-PLAN.md` fully
green; (2) one supervised manual night the operator approves; (3) voice preflight promoted to
BLOCK via `--require-pvc`, or an explicit written waiver — without it the lane can re-arm on
approved charts and quietly return the instant-clone voice he rejected; (4) the tier/model
decision made. At ~8.6–10k chars/night an unresolved quota exhausts around night 12–14 and the
lane dies at preflight mid-month, which from the outside looks exactly like the 07-27 stall.

## Sequence

### 0. Pre-flight (seconds, before anything renders)
- `PYTHONIOENCODING=utf-8 OpenMontage/.venv/Scripts/python.exe tools/daily_preflight.py`
  — TradingView CDP, ElevenLabs key + remaining quota + voice category, YouTube token, disk,
  pagefile. Probed LIVE and refuses in seconds rather than stalling for hours. `daily_lane.py`
  runs it automatically at the head of `init_stage`; run it by hand before a manual night.
  Two WARNs are the lane's known state: the voice is still the instant clone (no PVC), and the
  pagefile is still pinned rather than system-managed.
- `PYTHONIOENCODING=utf-8 OpenMontage/.venv/Scripts/python.exe tools/publish.py --dry-run`
  — the other three platforms, from the LIVE probe only, never from memory/notes (2026-07-21
  scar).
- YouTube quota ledger: ~6 uploads/day total. Tonight spends 1 long-form + up to 2 Shorts
  = 3 minimum; every judging recut that re-uploads spends another. Count before promising.
- Capture window: energy symbols reopen ~20:00 ET, rates/indices ~18:00 ET — charts before
  the reopen = no live-stub attestations. Earlier is strictly better.
- TradingView Desktop must be RUNNING for capture, and CLOSED before TTS (RAM).

### 1. Produce → private upload (skill: **daily-news-video**)
Follow it in full: analysis brief → **rendered thumbnail** (`render_thumb.cjs`, never a
video frame; path into social-batch `"thumbnail"` — 2026-07-21 scar: publish.py used to
drop it silently and YT auto-frames went live) → chart plan + zoomed captures
(`--expect-last-bar`, `--range-days 245`) → vo.txt (**1,450–1,700 words @ 145 wpm** —
lands a 10.1–11.8 min master incl. the 12 × 0.45s section gaps; the old
"2,000–2,350 @ 197 wpm" could never fit the 10:00–12:00 rule at the real 145 wpm and
produced a 14.3 min master on 2026-07-27) →
claims.yaml + vo-receipts.yaml → scene-plan (per-asset beats) → **all four gates** → **second-model
critic pass** (triage against receipts; receipts win) → runner:

The gates now BLOCK on the 2026-07-28 rejection, and each has both acceptance poles proven
against real artifacts (`--selftest` on both tools):
- `claims_gate` — recital cap of 5 distinct feed claims per (section, instrument); feed claims
  must use a closed predicate vocabulary and resolve under the receipt's `dashboard`; feed
  values cross-checked field by field.
- `editorial_gate --levels-only` — every level drawn is spoken and every level spoken is drawn.
- `editorial_gate --spoken-only` — spoken instruments derived from receipts, not from the beat's
  own `spokenSubjects` declaration.
- `visual_qa` — one frame per beat of the rendered master, and a hard fail when it inspected
  nothing.

**Surface the critic's verdict inside the approval prompt.** The critic stays advisory by
decision — `daily_lane.check_stage` does not read `build/independent-critic.md` and will not —
but the operator signing a hash should see "critic: thesis undisputable / no stakes" beside it.
`script-approval.json` for 07-27 records that he approved the exact hash of the script he later
called boring, with it open in front of him; a human backstop that has already failed once does
not get quieter.
```
CLIP_SKIP_SHORTS=1 PYTHONIOENCODING=utf-8 OpenMontage/.venv/Scripts/python.exe \
    tools/daily_postclose.py productions/daily-<date>
```
Runner output = private YouTube upload + Telegram text AND master video (msgs carry the
actual cut — "i cant judge unless you show me").
**No AI-generated platform labels** (operator ruling 2026-07-21): `containsSyntheticMedia:
false` in every social batch — own voice, own charts, operator approves all gates; the
scene-plan kind declarations validate the false flag; policy risk stated once,
operator-owned. Never silently flip it back. Then ffprobe the master: 10:00–12:00 or
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
failure never stops the rest; ledger printed at the end). TikTok "uploaded-unverified" has
TWO cases (2026-07-21): (a) real review hold — the post IS in Studio ("Content under
review", privacy Only me) and clears to the chosen privacy on its own; (b) the upload
silently vanished — NOT in Studio posts or drafts. Studio post-count is the truth signal,
never the transport's exit code. Case (b) after TWO spaced Studio checks = safe to retry
the single item (`publish.py --item tiktok-<label>`); one clip took 3 attempts before
landing. NEVER blind-retry case (a) — that's the double-post.
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
| Lane refuses in seconds at `preflight` | read the BLOCK line; it names the one condition. Quota exhaustion and an expired YouTube token both look like a stall otherwise |
| TradingView CDP dies mid-capture (stack-buffer-overrun) | seen 3× on 2026-07-28. Kill the 12 processes, relaunch via `daily_lane.ensure_tradingview()`, re-shoot only the missing charts with `--reuse-png` |
| `capturedAt ... does not precede vo.txt mtime` | charts-before-script, working as designed: the charts were re-shot after the script was approved. Re-run the day properly (charts → script → gates → re-approve). **Never touch the mtime and never soften the gate** |
| Chatterbox segfault 0xC0000005 at load | close TradingView (needs ~4–5 GB free RAM), rerun runner |
| Assembler: news clip shorter than beat | recut re-opened the holdSec contract — bump `news-shots.json` holdSec ≥ VO+2s, delete stale mp4s, `fetch_news_shots.mjs <sources.json> <prod-dir> --reuse-png` |
| "production approval changed after operator approval" | file bytes drifted (e.g. git touched them) — re-mint: `daily_postclose.collect_gates` + `script_approval.machine_approve`, never hand-edit a receipt |
| Master under 10:00 | extend with already-receipted unused claim facts, re-record only changed sections |
| visual_qa caption-over-chart FAIL on a vertical | that segment needs `layout: "fit"` in derivatives-plan.json |
| Platform "blocked" claim from memory | it's stale until `publish.py --dry-run` says so |
