# SESSION HANDOFF — 2026-07-28c · ep02 v41, the skill amendments, and the four-video batch

> **STATUS 2026-07-28 17:35.** The v41 master is **rendered and muxed**
> (`series-02-out-of-sample/hyperframes/renders/ep02-v41-final.mp4`, 826.627s). The chain was
> still inside its `=== GATE ===` block when this thread closed — **read the tail of
> `hyperframes/renders/v41-chain.log` before you trust anything about v41's gates.** Source
> gates already recorded PASS in that log: `term_gate` 13/13, `lexicon_gate` (both axes),
> `check_figures`, `broll_conflicts` 0 conflicts. `npm run check` passed with 0 errors.
> Everything else in this doc is done and pushed.

**Supersedes:** `SESSION-HANDOFF-2026-07-28b-ep02-lexicon.md`. That doc's ep02 state is stale.

---

## 1. What this wave actually changed

### The reason ep02's b-roll looked static, found for the second time

`tools/broll_conflicts.py`'s beat parser was blind to **array-driven** tween positions.
`scene-terminal` declares its four asset-class cards as a `[selector, fraction]` table and fires
them from a `forEach`, so the call site reads `tl.set(c[0], …, DUR * c[1])` — an expression, not
a literal. Measured: **2 beats across a 129-second scene**. Consequences, both mechanical:

- the gate **passed by detecting nothing** on that scene, and
- `place_cutaways.py` saw ONE 121-second gap and dropped ONE 3.6s clip into it — which is
  exactly where the v40 master's two longest static stretches (41.3s at 279.5s, 43.9s at
  324.4s) sat.

This is the **same failure class as the 2026-07-27 `DUR * <fraction>` miss, four days later, in
the same function.** The parser now resolves the table form and **BLOCKS** on any
`DUR * <expression>` it still cannot read — `py tools/broll_conflicts.py --demo` pins both
behaviours. Terminal: 2 → 6 beats, 1 → 6 cutaways.

> **Trap inside the fix.** `DUR\s*\*\s*(?![\d.])` does NOT work: `\s*` backtracks, the lookahead
> lands on the space before `DUR * 0.052`, and every literal in the project blocks. Require an
> identifier start instead: `DUR\s*\*\s*([A-Za-z_][^)\n]*)`.

### The 78-second opening

`cut_census` flagged a **78.17s hold at 0.0s** on v40. It is not a freeze — `presentation_gate`
measured longest freeze **0.000s** and `intro_pace` counted 16 changes in the first 25s. It meant
*no hard cut*. Cause: `MIN_GAP = 7.0` while the only two candidate gaps up there measure 5.95s
(hook 30.2–36.1) and 5.83s (windows 9.5–15.3). `MIN_GAP = 5.8` clears both and opens nothing
else. **First cut 78.2s → 31.3s.**

### Teaching boards now land on their words

Placed by list order, `board-warmup` played **64 seconds** from the spoken word "warmup" and
`board-survivorship` **38 seconds** from "delisted". `place_cutaways.board_cues()` looks each
board's cue word up in that take's own `artifacts/whisper-back.json`, centres the clip on the
word and clamps it inside the gap (a gap's upper edge IS a beat — running past it would bury a
reveal). Re-record a slot and the board follows the word with no hand-timing.

### The eleven clips nobody knew existed

`world-*.mp4` — eleven Cinema Studio shots, 12.04s, 1080p — had been sitting unused and absent
from `LIBRARY.md` while `lab-corridor-push.mp4` ran **4× against the 3× cap**. Frames pulled and
looked at: all on-world (dark concrete, one warm source, dark monitor, faceless). Six added to
`place_cutaways.NEUTRAL`, all eleven documented. `place_cutaways` now enforces `MAX_USES` **at
placement time** instead of discovering the breach afterwards.
**No `.provenance.json` exists for them** — the job ids were never captured. Recover from
`show_generations` if ever needed; do not back-fill a guess.

**v41 cut, measured:** 40 cutaways, 0 conflicts, no clip over 3×, first cut 31.3s.

---

## 2. Skills — all three pushed to `javin23863/claude-config`

| commit | skill | what went in |
|---|---|---|
| `3023859` | `into-the-laboratory` | narration register (screen ≠ spoken); `term_gate` exists and is in the chain; write positions as `DUR * <literal>`; boards go on their word; 192 wpm **pointing at** `syllabus.md` rather than forking the number; product-on-screen **SUSPENDED**; the four operator gates on a publish; scars |
| `3023859` | `laboratory-world` | the teaching-board bank (chalk geometry only, never letters); the eleven `world-*` shots written down |
| `ed12d9a` | `episode-assembly` | **§6b — the four pre-render checks**, chief among them a per-scene beat count; four-at-once release; auto-dub per YouTube Desk §4; verticals are post-publish; captions proved by audio hash |
| `1db7ca6` | memory | ep02 defects 5–8 + the operator calls that gate publish |

**`episode-assembly` §6b is the answer to "why did this take two days".** Almost none of the
time was rendering. It was writing a draft, rendering it, and only then finding something a
ninety-second source check would have shown.

---

## 3. Publishing state

**Release shape is settled and I got it wrong once — do not re-derive it.** The release is
**FOUR EPISODES AT ONCE**, per the operator and `youtube-channel-startup-growth` (a channel
under 1K launches with four videos, because people binge). A staged drop is not on the table.

**Auto-dub** is a YouTube Desk §4 accelerant — enable at upload, decide per video. The operator
**approved the synthetic-content disclosure** (tick yes at upload). It is no longer blocking.

**Ready:**
- ep01 `master-r46.mp4` (546.405s) — sheet at `series-01…/artifacts/publish-ep01.md`.
  Captions **verified, not assumed**: r43–r46 share audio MD5
  `c1d0b335a9ac3f717a57cc10639b4710`, and transcribing r46's first 12s returns SRT cue 1
  verbatim. Upload `assets/subtitles.srt`, **not** the `pre-openingline` twin.
- ep02 description + chapters rebuilt for the 13:47 cut in `artifacts/_yt_desc.txt`.
  **`artifacts/publish-ep02.md` still has a v31 header — update it to v41.**

**Structurally post-publish:** `tradercockpit/tools/cut_derivatives.py` hard-fails unless
`publish_log.json` already carries a published long-form. Verticals cannot exist before upload.
Its `containsSyntheticMedia: false` ruling belongs to the DAILY lane (own voice, own charts) and
does not transfer to this series.

---

## 4. THE BATCH IS BLOCKED ON ONE OPERATOR DECISION

`series-03-timing` and `series-04-cost` contain **`artifacts/packaging.json` and nothing else**,
both `STATUS: PROPOSED 2026-07-27 — awaiting operator approval (human gate 1 of 2)`. Packaging
is locked before a word is written, so two entire episodes wait on this one approval.

| ep | title | thumbnail |
|---|---|---|
| 03 timing | Out-of-Sample Killed 30. This Killed 101. | ONE BAR LATE / TWO THIRDS GONE |
| 04 cost | 1,335 Strategies Went In. 46 Came Out. | DOUBLE THE SLIPPAGE / SEVEN MORE DIE |

**Defect in both, fix before scripting:** `first_spoken_sentence` spells its numbers out
("One thousand three hundred and thirty-five…", "a hundred and one"). That field is copied
verbatim into `vo.txt`, and spelled-out numbers already got one script rejected. Make them
digits.

**Ep04 depends on ep03.** Its title claims the whole funnel (1,335 in, 46 out), so it closes the
arc and cannot be written first. The batch is sequential at exactly that one point.

---

## 5. Runbook for the next session, in order

```bash
cd C:/Users/MSI/Documents/tradercockpit/OpenMontage/projects/series-02-out-of-sample

# 1. the gates this thread did not live to read
tail -60 hyperframes/renders/v41-chain.log
py tools/intro_pace.py hyperframes/renders/ep02-v41-final.mp4     # needs >= 16 changes / 25s
py tools/contact_sheet.py hyperframes/renders/ep02-v41-final.mp4  # then LOOK at the frames

# 2. if clean, open it on the operator's screen -- never hand over a path
#    Start-Process <abs path to ep02-v41-final.mp4>

# 3. bring the ep02 sheet up to v41 (its header still says v31)
#    artifacts/publish-ep02.md

# 4. the scheduled task is still installed and still points at v41
schtasks /query /tn ep02-chain
#    delete it once no further ep02 render is expected:
#    schtasks /delete /tn ep02-chain /f
```

**Then the batch:** get ep03/ep04 packaging approved → fix the two `first_spoken_sentence`
fields to digits → `/episode-assembly` for ep03, **running §6b's four checks before the first
render** → ep04 → upload all four with auto-dub on.

---

## 6. Standing constraints (restated — violating these is what cost previous waves)

- **NEVER touch the futures pipeline.** Read-only, always. No runs, no lanes, no repo builds.
- **ONE disclaimer per episode**, byte-exact, in the **DESCRIPTION only**, never in the script:
  `Research tooling, not financial advice. No performance is promised or implied.`
- **Product on screen is SUSPENDED** until the operator says the software is demo-ready.
- **Voice: one setting per EPISODE** — `WUBgDq3i8JpbDg75wNgm`, speed 1.00 / stability 0.5 /
  similarity 0.8. No varispeed, ever. If an episode runs long, **cut words**.
- **Gate-softening is presumed wrong.** Widening a cap so a FAIL passes is a blocker, not a fix.
- **Numbers are DIGITS.** A leading `-` is silent through the TTS — write `minus`.
- Ops vault is `Desktop\Obsidian Vault From VPS\tradercockpit\tradercockpit`. Never create
  another vault, anywhere.

## 7. Open ceilings — deliberately not done

- **`cut_census` hold FAILs remain**, and are a standing operator pacing call, not a defect.
  Read its RATE line (4.72/min against a 4/min bar on v40) and cross-check any hold against
  `presentation_gate`'s freeze figure before re-cutting.
- **`lexicon_gate`'s max-over-LOO ceiling** is untouched and remains an explicit operator call.
  Do not grow the corpus to pass it — measured, the gap WIDENS (67 → 75 → 91 docs moved it
  +0.29 → +0.59 → +0.72).
- **`npm run check` warns** `gsap_timeline_set_initial_hide` on `#wn-rule2` in scene-windows: a
  zero-duration `.set()` at position 0 does not render while the playhead sits exactly at 0, so
  frame 0 shows the un-hidden state. Warning only, unexamined on a pulled frame. Worth one look.
- **Browser automation was unavailable** this session — the Claude extension is not connected and
  nothing answers on CDP 9333 or 9222. Anything needing YouTube Studio needs that fixed first.
