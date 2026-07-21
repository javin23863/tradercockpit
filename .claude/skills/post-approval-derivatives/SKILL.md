# Post-Approval Derivatives — Shorts/Clips From the Approved Long-Form

**Trigger:** the daily (or weekly) long-form is operator-approved and public on YouTube.
Derivatives are cut ONLY downstream of that approval — never from an unreviewed master.
**Runner:** `tools/cut_derivatives.py <production> [--upload]` — deterministic, fail-closed,
LLM-agnostic (operator directive 2026-07-21). Any model following this file produces the
same outputs; every judgment call that comes up gets encoded here or in a gate same-wave.

## The one command

```
CLIP_SKIP_SHORTS unset here — this IS the shorts lane.
PYTHONIOENCODING=utf-8 OpenMontage/.venv/Scripts/python.exe tools/cut_derivatives.py \
    productions/<vid>            # stage: cut + gates + batch, prints publish commands
    ... --upload                 # same + publish through tools/publish.py
```

Run it WITHOUT `--upload` first, Read one extracted frame per clip (verify-the-rendered-app
doctrine), then re-run with `--upload`.

## What the runner enforces (do not re-implement by hand)

1. **Preconditions HARD-FAIL**: `build/master.mp4` + `build/captions.srt` +
   `build/sections.json` present, and `publish_log.json` carries a published YouTube
   long-form entry. No parent approval → no derivatives.
2. **Editorial input** = `derivatives-plan.json` in the production dir — the writer picks
   segments the way they write vo.txt; execution is deterministic:
   ```json
   {"segments": [{"section": "01", "offset": 0, "duration": 39,
                  "label": "hook-bounce-failed", "anchor": "right", "layout": "fit",
                  "title": "...", "copy": "hook ... exact disclaimer"}]}
   ```
   - Max 2 segments (YouTube quota is ~6 uploads/day; the daily lane already spends some).
   - Segment start is DERIVED: the captions.srt cue that opens the named section + offset.
     No whisper re-pick, no hand timestamps. If the prefix match fails, captions and
     sections.json disagree — re-run produce, don't hand-patch.
   - `layout`: `crop` (right-anchored punch-in, keeps the price axis) for single-chart
     sections whose lower frame is empty; **`fit` for chart-dense sections** — the
     2026-07-21 proving run's hook FAILED visual_qa in crop (captions on candle bodies)
     and passed in fit (chart panel top, captions over the dark backdrop).
   - `title`: no `>` (YouTube invalidTitle scar).
   - `copy`: must contain the exact disclaimer and pass `script_style_gate.audit_text`
     (persona ban + negate-then-replace ban apply to social copy too).
3. **Cut** via studio-kit clipper `--mode script` into `productions/<vid>/shorts/` —
   NEVER the shared `studio-kit/clipper/output` (stale-clip collision 2026-07-21).
   One clipper run per segment so anchor/layout apply per segment;
   `CLIP_CLEAN_VERTICAL=1` renders the caption-free twin visual_qa diffs against.
4. **Gates, fail-closed**:
   - copy gate first (cheapest): disclaimer + style audit per segment;
   - `visual_qa --clips <prod>/shorts` on the rendered pixels: platform safe zones
     (TikTok tightest: top 15% / bottom 20% / right 15%), caption geometry
     (MarginV=64 ≈ ink bottom 1512 — VERIFIED inside the 1536 limit on 2026-07-21),
     caption-over-chart detail check, native-render provenance via manifest.
   - `visual_qa` defaults to the production's own `shorts/` dir now; the shared-dir
     default remains only for legacy productions.
5. **Batch** = `social-batch-verticals.json` (social-batch/v2, **containsSyntheticMedia
   false** — operator ruling 2026-07-21: no AI-generated platform labels; the narration is
   the operator's own cloned voice reading operator-approved scripts, the visuals are real
   TradingView/news captures, and the scene-plan `kind` declarations validate the false
   declaration deterministically. Platform-policy risk of unlabeled synthetic audio was
   stated once and is operator-owned — do not re-litigate it, and do not silently flip the
   flag back). Items are machine-approved ONLY because the parent long-form carries operator
   approval — `reviewedBy` records that chain; `approvalSha256` =
   `social_batch.approval_fingerprint` (binds copy + asset bytes + claims gate +
   production approval). Any post-mint edit → re-run the runner, it re-mints.
6. **Publish** through `tools/publish.py` (auth probes fail closed, read-back verified,
   publish_log receipts). Per-channel caption contract is encoded in the runner:
   YouTube = caption-free `.vertical.clean.mp4` + native captions; IG/FB/TikTok = burned.

## Platform status — PROBE, never quote memory

**`publish.py --dry-run` is the ONLY valid source for platform auth status.** It costs 10
seconds. Quoting a remembered blocker cost a full stale-claims cycle on 2026-07-21: memory
said "Meta app-blocked, TikTok cookie absent" while the live probe said all four valid —
TikTok had been logged in the whole time and the Meta block had cleared. Recalled state
reflects when it was written; the probe reflects now.

All four lanes proven live 2026-07-21 (one command each,
`cut_derivatives.py <prod> --platform <ch> --upload`):
| Platform | Path | Notes |
|----------|------|-------|
| youtube | native captions + clean twin | default platform |
| instagram | Graph API via B2 URL staging | burned captions |
| facebook | Graph API binary upload | burned captions |
| tiktok | CDP on debug Chrome :9333 (`.chrome-cdp` profile) | burned captions; new posts sit briefly in "Content under review" (privacy Only-me) and clear to the chosen privacy within MINUTES — publish.py's read-back reports "uploaded-unverified" during the hold, which is NOT a failure. Verify in TikTok Studio (posts count + top row) before ANY retry (retry = double post), and re-check before reporting the hold as current state. |

If a probe reports blocked: stage the batch items and report the blocker honestly — never
claim posted, never bypass the auth probe.

## Scars (why the rules above exist)

- **Hash-bound approvals break on git line-ending normalization**: `git checkout`/merge
  rewrote `analysis-brief.md` LF→CRLF and invalidated `production-approval.json`
  (2026-07-21). Fix: re-mint via the runner's own `collect_gates` + `machine_approve`
  (gates re-run, honest bundle) — never hand-edit a receipt hash.
- Clip renumbering: the clipper numbers per-run (`clip-001-*` each invocation); the
  runner renames to per-plan indices and rewrites `manifest.json` so provenance holds.
- Watermark WARN on our own corner branding (@thetradercockpit) is a known heuristic
  false positive; a FAIL or a foreign TikTok/CapCut mark is real.
- Quota: count the day's uploads (long-form attempts included) before `--upload`;
  publish.py fails closed on quota but the failure costs a retry cycle.
