# SESSION HANDOFF — 2026-07-28d · the slate correction and the two vault gates

> **STATUS 2026-07-28 late.** **Supersedes `SESSION-HANDOFF-2026-07-28c-ep02-v41-and-batch.md`
> entirely on the slate.** That document describes ep03 as *timing* and ep04 as *cost*. Both are
> wrong as of this session — read §1 before touching anything.

---

## 0. THE ONE-LINE VERSION

Three operator corrections landed, each one exposing a defect a gate would have caught and prose
did not:

1. *"The next phase isn't timing, it's slippage."* → the slate did not follow the pipeline.
2. *"You're being super vague. No one knows what the fuck you're talking about."* → titles and
   thumbnails had no subject noun.
3. *"Whatever is inside your MD files that are causing you to skip these skills and playbooks."*
   → the skill was a **lossy copy** of the vault standard, and the copy is what loads into context.

**Every rule that held today was a gate. Every rule that was violated was prose.** That sentence
is the whole handoff; everything below is detail.

---

## 1. THE SLATE CHANGED. THIS IS THE CURRENT ONE.

| ep | phase | project dir | funnel |
|---|---|---|---|
| 01 | `phase01_intake` | `series-01-backtest-is-not-a-strategy` | 1,335 → 184 |
| 02 | `phase02_oos` | `series-02-out-of-sample` | 184 → 154 |
| **03** | **`phase04_cost`** (slippage) | **`series-03-slippage`** | 53 → 46 |
| **04** | **`phase06_mc_param`** | **`series-04-mc-param`** | 46 → 18 |

**`phase03_timing` is PARKED** at `projects/series-XX-timing-PARKED`, script written and gated.
The 154→53 cut it owns is narrated in one line of ep03's hook so the funnel stays honest.

**Why the correction was needed, so nobody re-derives it:** `phase04_cost` **is** the slippage
phase — its gate keys are literally `pf_slippage_2x` and `net_slippage_3x`. An earlier reading
inferred from `phase03_timing`'s docstring ("a same-direction fill one bar later") that phase03 was
slippage, and then an operator question was written whose three options all embedded that
inference. **A question built on a wrong premise does not become right by being answered.** Check
`registry.py` gate_keys, not a docstring.

There is no `phase05` — `phase05_xmkt` was removed entirely by operator ruling 2026-07-07.

---

## 2. THE TWO NEW GATES — read the standard, not a skill

Both live in `Documents/tradercockpit/tools/` (version-controlled, unlike the episode tree) and
both **parse the vault Production Standard live**. Edit the standard and they follow; if the
document is missing or a rule no longer parses, they BLOCK rather than pass quietly.

```bash
py tools/packaging_gate.py <ep>/artifacts/packaging.json   # §(a) title, §(b) thumbnail
py tools/script_arc_gate.py <ep>                           # §(c)1 pre-writing, §(c)3 arc
py tools/packaging_gate.py --demo   # must reject the bad fixture AND accept ep01's own packaging
py tools/script_arc_gate.py --demo
```

**Both run FIRST in the chain**, ahead of the project's own stack. A script that fails §(c) is a
lecture regardless of how green everything downstream is.

**Each gate's `--demo` caught a bug in that gate before it caught anything else.** `packaging_gate`
initially failed ep01 — the standard's own reference — because (b)6's *"Text 3–5 words"* is the
thumbnail's **total**, not a per-element budget. `script_arc_gate` rejected its own first
well-formed declaration, then turned out to contain a **literal backspace byte**: authored in a
heredoc as a non-raw Python string, so `ARC\b` compiled to `ARC<0x08>`. Python warned twice and it
was read past both times; `cat -A` found it in one line. **Raw strings, and read the warnings.**

---

## 3. BOARD

```
                    packaging       arc          script gates
ep02 out-of-sample     PASS       3 red          (shipped v41)
ep03 slippage         1 red        PASS          all PASS
ep04 mc-param         1 red        PASS          all PASS
```

- **ep03/ep04's single red is `(b)1 package BEFORE the script`** — both have `vo.txt` on disk while
  packaging `STATUS` reads `PROPOSED`. It is TRUE and it is **left red deliberately**. Flipping
  STATUS to green is gate-softening, which is presumed wrong. **Only operator approval closes it.**
- **ep02's arc red is a recorded KNOWN GAP, not a defect to fix.** v41 is rendered, gated, reviewed
  and approved; the gate postdates it. Retro-fitting an arc declaration would be either a lie —
  labelling topic-ordered slots as stages they do not carry — or a re-cut of an approved episode.
  Written into ep02's packaging so red reads as known.

---

## 4. RULINGS MADE TODAY — all recorded in `Decisions/`, none living only in a skill

| ruling | where |
|---|---|
| Phase 3 is slippage, not timing; and AI writes the scripts | `Decisions/2026-07-28 Phase 3 Is Slippage, Not Timing.md` |
| Skills cite the vault, never restate or supersede it | `Decisions/2026-07-28 Skills Cite the Vault, Never Restate It.md` |
| §(a) formula may take a beginner **BELIEF** where the phase tests a field | amendment inside Production Standard §(a) |
| AI authorship | dated amendment inside Production Standard §(c)5 |

**The belief amendment was forced by a measured collision.** §(a) wanted a famous beginner strategy
in the title; §(a)4 forbids naming a strategy that was not run; and this run contains **no named
strategy at all** — all 1,335 candidates are `formula-*`/`genetic-*`, with zero occurrences of
golden cross, sma, ema, rsi, macd, bollinger, breakout or donchian. A belief keeps the intent (a
recognisable entry point earns the click, then gets debunked) while naming nothing unrun. The gate
**detects the amendment in the document** rather than hardcoding it, so reverting the standard
tightens the check again by itself.

---

## 5. CURRENT PACKAGING

| ep | title | thumbnail | belief |
|---|---|---|---|
| 02 | Your Backtest Passed. The Hard Part Comes Next. | `SURVIVED` / `10 DAYS MADE IT` | my backtest was profitable |
| 03 | Doubling My Trading Costs Did Nothing. Tripling Killed 7. | `SAME TRADES` / `BIGGER BILL` | costs are a rounding error |
| 04 | I Tested My Best Setting 200 Ways. More Than Half Failed. | `SAME IDEA` / `WRONG NUMBER` | I found the best setting |

---

## 6. THE DEGENERACY CHECK PAID FOR ITSELF TWICE, AND FAILED TO FIRE ONCE — which is the point

- **ep03 (was ep04-cost).** Proposed `DOUBLE THE SLIPPAGE` → `7 MORE STRATEGIES DIE`. Measured:
  doubling kills **2**, and **zero** die from doubling alone; all 7 deaths land at triple, and 5
  strategies take the doubling fine then fall over at 3x. The correction **became the episode** —
  the damage is not linear in the multiplier.
- **The parked timing episode.** Proposed `ONE BAR LATE` → `TWO THIRDS GONE`. Measured: 60 of the
  101 dead never failed the fill test at all. The delay alone kills 12 of 154.
- **ep04 PASSED it.** 28 deaths, only 8 within 10% of the bar, dead median 0.37 against a 0.50 bar.
  A check that never blocks is void evidence; this one can say otherwise.

**Run it BEFORE the thumbnail, never after** — and note `degeneracy_check.py` decomposes a daily
return series, so a RATIO headline needs its own decomposition. Both blocks above came from that.

---

## 7. RUNBOOK — in order, and the first item is not mine

```bash
# 1. OPERATOR: approve ep03 + ep04 packaging. This is the ONLY thing closing the last red.
#    Nothing below should start before it — §(b)1 is "package BEFORE the script" and it is
#    already violated once.
# 2. OPERATOR: ratify the syllabus entries (series-plan.md:728, "sign per episode before
#    that episode is scripted"). Also already violated once, recorded not hidden.
# 3. then, per episode:
py Documents/tradercockpit/tools/packaging_gate.py <ep>/artifacts/packaging.json
py Documents/tradercockpit/tools/script_arc_gate.py <ep>
cd <ep> && py tools/emit_vo.py --voice-id WUBgDq3i8JpbDg75wNgm     # ONE setting per episode
py tools/voice_consistency.py hyperframes/assets/audio/v1 --vo artifacts/vo.txt
py tools/whisper_back.py --audio hyperframes/assets/audio/v1 --vo artifacts/vo.txt
py tools/beat_map.py <slot> --list          # RE-DERIVE every beat; never inherit
# compositions, then episode-assembly §6b's FOUR pre-render checks, then render
```

**Higgsfield: still 1,323 credits, ZERO spent.** Rule 7 — *"buy a clip only once the shot it serves
is cut and timed."* Nothing is cut or timed, so no boards have been generated. That is compliance,
not an omission.

---

## 8. STILL OPEN — nothing here is silently dropped

- **Ep01's caption + spoken half-sentence** (`four-episode-slate.md:20-26`) rides the operator's
  next recording. The release is **four at once**, so this gates the whole batch.
- **The four-video CTA + end-screen chain.** The batch ruling created it; nothing has built it.
- **`social-surface-audit`** (`GTM/README.md:120-123`) and the **§(f) kill/roll recalibration** for
  ~14-minute runtimes (`series-plan.md:713`).
- **§(d) editing, §(e) repurposing, §(f) kill/roll are still PROSE.** §(a)(b)(c1)(c3) are now
  executable; those three are not. Named so the next session knows the coverage boundary.
- **The Hero's-Journey arc is declared, not judged.** `script_arc_gate` proves the stages exist,
  are located and are in order. Whether ep03's crisis is genuinely vulnerable is a human read.

## 9. STANDING CONSTRAINTS

- **NEVER touch the futures pipeline.** Read-only, always.
- **A skill can never supersede the vault.** If they disagree, the vault wins and the skill is the
  defect. Doctrine changes go to `Decisions/` **plus** an amendment inside the governing document.
- **Gate-softening is presumed wrong.** A red that is true stays red.
- **Codex CLI is unreliable on this box** — attempted as a critic this session, ran 10 minutes at
  2.5s CPU and returned 0 bytes. Same hang signature as 2026-07-16/17. Do not budget on it.
- **The episode projects are NOT under version control** (`OpenMontage/` is gitignored at
  `.gitignore:5`). Scripts, packaging and compositions live on one disk with no remote. The two
  gates were deliberately put in `tools/` instead, which IS tracked.

---

## 10. EP03 PRODUCTION — appended 2026-07-29, live state

**Everything up to the render is done and green.**

```
VO 15/15          voice_consistency PASS (one voice, one pace)
whisper_back      done
compositions      15 + index.html, generated by tools/build_scenes.py
npm run check     PASSED - 0 errors, 46/46 WCAG AA
beats             115 across 15 scenes, min 6, none at 0 or 2
intro_pace        18 changes in 25s (bar 16) - margin 2
cutaways          35 from 15 distinct clips, none over the 3x cap, first cut 23.7s
packaging + arc   both PASS
runtime           11:40
```

### The scene generator is the durable artifact

`tools/build_scenes.py` (version-controlled) emits every tween as `DUR * <numeric literal>` inline,
gives every clip one full-scene window, and puts a line-height on every large-type rule. **The two
silent beat-parser blindings, the retime literal-rescale bug and the line-height overlap are now
unexpressible rather than checked for.** It reads `artifacts/scenes.json`; ep04 needs only a spec.

### Higgsfield — first spend of the programme

| clip | state |
|---|---|
| `board-cost-stack.mp4` | v1 trimmed to 3.2s; v2 regenerating at 12s frontal |
| `board-trade-count.mp4` | 12s, frontal and readable end to end — **keep** |
| `board-cliff.mp4` | rendering |

**`multi_shots: true` is wrong for a teaching board.** It plans a second camera setup inside the
12s; on a room shot any angle works, on a board the diagram goes oblique and unreadable. Measured:
`multi_shots:true` gave 3.2 usable seconds of 12; `multi_shots:false` holds a square readable
frontal view at 9.6s. Recorded in `laboratory-world`.

**A trap I wrote and then had to retract within the hour.** A `multi_shots:false` job failed, I
blamed `multi_shot_mode: "custom"` and wrote it into the skill — then an identical job with the
identical mode succeeded. n=1 is a flake, not a trap. Corrected in place; the retraction is in the
file because false doctrine in a trusted file is worse than none.

### Three ep02 hardcodes swept

`broll_conflicts --demo` read ep02's real `scene-terminal.html`, so the gate's **own negative
control could not run anywhere else**; it is synthetic now and pins BOTH blind shapes.
`cadence_gate --budget` defaulted to 2098 (ep02's v5 word count). `slop_gate SUBJECT_TERMS` was a
module constant holding ep02's subject. My first fix for the third was **worse** than the hardcode
— deriving terms from a subject string invented requirements the episode never agreed to. *A gate
may enforce a declared contract; it may not author one.*

### ep01 — clone ruled, and it is not a drop-in

Operator: *"use clone for ep1"*. VO done, `voice_consistency` PASS, caption fix landed in
`scene-02` where the 9,971 figures reach the screen. **MEASURED: 427.2s = 7:07 against the recorded
546.4s = 9:06.** ep01's compositions are timed to the OLD audio, so this needs retime, a fresh
whisper_back with every beat re-derived, and a re-render. The new master does not inherit approval.

### Next, in order

1. collect `board-cliff` + `board-cost-stack` v2, pull frames, trim only if the tail dies
2. `py tools/place_cutaways.py --write`
3. render `--workers 3`, absolute `-o`, background, never piped through `tail`
4. `build_bed --video` -> `check_bed` -> mux (two-pass loudnorm, true peak -2.0)
5. render gates: `intro_pace`, `presentation_gate`, `cut_census` rate, contact sheet + LOOK

---

## §11 — ep03 to picture-lock (2026-07-28, later)

### The Higgsfield boards are done, and `multi_shots` was the trap

Three teaching boards, all inspected frame-by-frame before use, all zero-text and on-world:

| clip | job | usable | teaches |
|---|---|---|---|
| `board-cost-stack.mp4` | `bc866dae` | **12.0 / 12.0s** | three chalk bars of rising length |
| `board-cliff.mp4` | `c1e52c68` | **12.0 / 12.0s** | a flat line that runs level, then drops |
| `board-trade-count.mp4` | `65e61a2e` | **12.0 / 12.0s** | a rising curve, downward ticks hanging off it |

**`multi_shots: true` is what made the ep02 bank need trimming.** With it on, the model spends the
12s cutting to new angles and the diagram is square to camera for a few seconds only — the
cost-stack v1 (`c33818d1`) gave **3.2 of 12s**. With `multi_shots: false` plus a prompt that says
*locked-off, square to the board, never oblique*, all three above needed **zero trim**. Keep
`multi_shots` for atmosphere, where a cut costs nothing; never for a board.

**Pass the params explicitly.** `generate_video` defaults this model to `mode: std` and `sound: on`
against a bank of `mode: pro` / `sound: off` / `genre: suspense` / `cfg_scale: 0.7`. Job
`11647d9e` was submitted without them, completed normally, and is off-bank. The defect is visible
only in the params echo.

### `place_cutaways` reported 35 cutaways into a file with zero video tags

The generated `index.html` had neither the `<!-- CUTAWAYS -->` markers nor the ep02
`TODO(ep02)` anchor, so the insertion fell through to a `str.replace()` that matched nothing. The
file was written back byte-identical and the tool printed `written.` **`broll_conflicts` then said
"no B-roll <video> clips found in index.html" and exited 0** — the second gate passed by having
nothing to inspect. Same void-evidence shape as the two beat-parser misses.

Fixed in `tools/build_scenes.py` (commit `43a24f0`): the marker pair is emitted into every
generated index, plus `#root > video{position:absolute;inset:0;width:1920px;height:1080px;
object-fit:cover}` — without that rule a 1344x768 cutaway lays out at intrinsic size in the corner.
`place_cutaways.py` now BLOCKs when it finds no insertion point and verifies the written tag count.
Ported to ep04's copy.

With the gate finally able to see, it found a real one: `board-cliff` ended **exactly on**
`scene-cliff`'s kicker beat, because the cue clamp was `hi - CUT_S` and `hi` IS a beat.
`CUE_MARGIN = 0.5` (> `broll_conflicts.LEAD` 0.4) fixes it. 0 conflicts now.

### `script_style_gate` was in the router and was not run

`GTM/README.md:32-45` ends *"Then run: `claims_gate.py`, `script_style_gate.py`, and the read-aloud
gate."* Run after the fact it BLOCKED on spoken copy:

* **edit-room narration ×2** — *"It's on screen, and I want you to notice something about it"*,
  *"Link's on screen."* Both break router item 3, `Backstage vs Receipts`: never name the machinery.
* **corrective contrast ×3, limit 1** — a triple negation in `scene-count`, and *"It isn't a hard
  bar, it's an impossible one"* in `scene-scar`.

Four lines rewritten → four slots re-voiced → `scene-survivor` re-rolled, because the four new
takes moved the episode median F0 and pushed it 1.59 st out of a ±1.5 band. PASS now, spread
2.59 st. The surviving correction is *"That's 7 in total, not 7 on top of the 2"* — earned.

### `ai_tell_gate` was scoring the file, not the narration

`script_body()` dropped `## slot` headers and kept everything else, including each vo.txt's `#`
provenance header and its `=== SLOT ===` markers. Its top reported offenders were literally
`ep narration, narration v, v written, written against, the contract, contract router` — header
words. Fixed in commit `77d9d93`; no threshold touched. After the fix:

| | unseen bigrams (bar 45.3%) | out-of-register (bar 36) |
|---|---|---|
| ep01 **shipped** | 47.6% | 21 |
| ep02 **shipped** | 46.0% | 46 |
| ep03 | 51.3% | 38 |

**The bar rejects both accepted episodes.** That is a calibration question for the §(f) pass, not a
shippability signal, and the corpus behind it has a known duplicate-variant defect. NOT softened.

### State at handoff

`artifacts/`: `vo.txt` (15 slots, 11:36), `scenes.json`, `whisper-back.json` (fresh),
`packaging.json` (LOCKED), `thumbnail-ep03.png` + squint pair, `_yt_desc.txt`, `_yt_tags.json`,
`publish-ep03.md`. All script gates green except `ai_tell_gate` as above.

`ep03-v2.mp4` rendering — 15 slots, 35 cutaways, 0 conflicts, `npm run check` 0 errors.
**v1 was killed mid-encode and deleted**: the VO changed under it. Its orphaned `ffmpeg` (pid
24488) survived the shell kill and had to be stopped by hand — check for one after any TaskStop.

### Next, in order

1. `build_bed --video` -> `check_bed` -> mux (two-pass loudnorm, true peak -2.0)
2. render gates on the muxed master: `intro_pace <video>`, `presentation_gate <video>`,
   `cut_census`, contact sheet + **LOOK at it**
3. operator decision, recorded in `publish-ep03.md`: *"first shot matches the thumbnail inside
   5.0s"* — ep01 and ep02 both ship a title card first with the first cutaway at 31s and neither
   plate appears in its episode. Either the rule means the promise, or all three need a cold open.
4. ep04 end to end — its `place_cutaways` already carries the ep03 fixes
5. ep01 retime + fresh whisper_back + re-render (clone is 7:07 vs recorded 9:06)

---

## §12 — the font shorthand, and four series assets resolving locally (2026-07-28, later still)

### Every element in two episodes rendered at 16px

`font: 700 74px/1.14 inherit` is **invalid CSS**. The shorthand requires a real font-family as its
last component; `inherit` is not one, so the browser drops the ENTIRE declaration — size, weight
and line-height with it — and the element falls back to the 16px default. Seven rules in
`build_scenes.py` were written that way, which is every piece of type the generator emits.

Measured on ep03's v2 master: the 74px title rendered **16px**, the 92px card values **16px**, the
frame 95% empty black with a strip of body copy in the upper left.

`intro_pace` read **2 visual changes in the first 25s** against a bar of 16. The animation was
fine — the contact sheet shows all 19 reveals firing on time — but 16px text moves almost no
pixels, so the meter saw nothing. **The BLOCK was true and its apparent cause was wrong.**

The generator's own self-check passed throughout. It asserted
`re.search(r"font:\s*\d+\s+\d+px/[\d.]+", CSS)` — the SHAPE of a shorthand no browser applies. It
now asserts what has to be true: no `font:` shorthand anywhere in the CSS or emitted HTML, a
line-height beside every font-size, and a largest size >= 74px so the title cannot become body
copy. Commit `07bc2f6`.

**Nothing automated caught this.** `npm run check` (0 errors, 46/46 WCAG AA), `broll_conflicts`
(0), `check_bed` (PASS), `slop_gate` (clean) were all green on a master whose type was 16px. It
took pulling frames and looking at them.

ep03-v2 and its bed are deleted. ep03-v3 and ep04-v1 re-render from the fixed generator.

### Four SERIES assets were resolving inside the EPISODE tree

Same shape as the cutaway anchor in §11, four more times. Each one turned a gate into either a
false BLOCK or a crash, and a gate that cannot read is indistinguishable from one nobody ran:

| asset | symptom | fix |
|---|---|---|
| finance corpus (`corpus-fin`, 91 docs) | `lexicon_gate` BLOCK: "only 0 corpus doc(s)" | fall back to ep02's copy |
| `intro_pace` fixture (`ep02-v32b-final.mp4`) | BLOCK: "fixture is gone" | fall back to ep02's renders |
| `hyperframes` package.json / meta.json | ep04 `npm run check` ENOENT | copied into ep04 |
| `slop_gate.py`, `thumb_gate.py` | absent from ep04's tools | copied |

`intro_pace --demo` now re-calibrates anywhere: counts 9 on the pinned fixture against a hand
count of 9, and correctly FAILS it at one change per 2.78s.

### ep04 is built end to end

15 slots voiced with the series clone, one setting, `voice_consistency` PASS (spread 1.89 st).
`scenes.json` written, whisper-back fresh, 34 cutaways from the shared library plus three new
boards, 0 conflicts, `slop_gate` clean, thumbnail built and squint-checked by looking.

Three ep04 boards, `multi_shots: false`, zero trim, all inspected:
`board-plateau` (`a3326ebd`), `board-fan` (`7625c2d7`), `board-percentile` (`4fe254c2`).

**ep04's card copy failed `slop_gate` with 19 errors on the first build** — 16 unresolvable
pronouns (`IT`, `THEY`, `THIS`, `EVERY ONE`) plus a `-0.06` whose leading minus is silent through
TTS and unreadable on a card, plus one anthropomorphism ("what this test never LOOKED at"). On
screen there is no antecedent: a viewer arriving mid-frame cannot resolve a pronoun. All 16
rewritten in `scenes.json`.

### Gate findings NOT actioned, deliberately

* **`ai_tell_gate`** blocks all three finished episodes on unseen bigrams (ep01 47.6%, ep02 46.0%,
  ep03 51.3%, bar 45.3%) — including two already accepted. Calibration question, not a ship
  signal. Not softened.
* **`lexicon_gate`** leaves ep04 at 81.52% novel trigrams against an 81.41% ceiling. 0.11pp. The
  flagged phrases are ordinary English; rewriting to move a metric by a tenth of a point would be
  fixing the gauge. Not softened, recorded.
* **`script_style_gate` BLOCKS ep02** (2 corrective contrasts, limit 1). Release is four-at-once
  so it matters, but ep02's v41 is an artifact the operator has already reviewed — re-cutting it
  is an operator call, not mine. **Open.**

### Next

1. ep03-v3 lands -> pull frames and LOOK (the type must be a headline) -> `build_bed --mux`
   -> `check_bed` -> `intro_pace` / `presentation_gate` / `cut_census` / contact sheet
2. same chain for ep04-v1
3. Telegram ping on both mastered (operator asked for it mid-run)
4. ep02 style-gate decision
5. ep01 retime + fresh whisper_back + re-render (clone 7:07 vs recorded 9:06)
