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
