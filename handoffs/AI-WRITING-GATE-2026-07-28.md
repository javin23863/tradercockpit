# AI writing gate — social department

> STATUS 2026-07-28: PR open, **not merged, therefore not live**. The gate exists on
> `feat/ai-writing-gate` (commit `01bad41ee352f4a4d798e360b29a81ca7f9610eb`,
> [tradercockpit-ops PR 1](https://github.com/javin23863/tradercockpit-ops/pull/1)). The daily
> lane runs from `Documents\tradercockpit`, so **no social copy is being checked by this yet**.
> Board card `social.ai-writing-gate` sits in Verify. Only the operator moves it to Done.

## What changed

Operator instruction: install `conorbronsdon/avoid-ai-writing` and add it to the AI write gates
for the social media department.

Every audience-facing field in a `social-batch/v2` now runs through **two** gates that ask
different questions:

| Gate | Question | Owns |
|---|---|---|
| `tools/script_style_gate.py` | is this TraderCockpit doctrine? | no predictions, no vague authority, no backstage narration, lead with the take |
| `tools/ai_writing_gate.py` | did a chatbot write it? | generic AI-isms — the rules that until now lived only as prose in `.claude/skills/no-ai-slop/SKILL.md` |

The detector is vendored verbatim at `tools/vendor/avoid-ai-writing` (MIT, upstream commit
`27156c7`, package v3.16.0) and driven as a node subprocess. It was not ported: 1,754 lines of
regex and stylometry, and a port forks upstream on day one.

## The two traps

**1. Importing the skill unchanged would have LOOSENED house doctrine.** Nine words
`no-ai-slop` bans *outright* — foster, facilitate, empower, streamline, multifaceted,
paramount, transformative, supercharge, harness — are only **Tier 2** in the detector, meaning
two must appear in one paragraph before either fires. A lone "empower" in a caption passes.
`HOUSE_BANNED` in `tools/ai_writing_gate.py` hard-blocks them regardless. Same shape as the
ep02 lexicon scar. Standing rule now recorded in
`.claude/skills/avoid-ai-writing/PROVENANCE.md`: **where the two skills disagree on a word,
no-ai-slop wins** — it is the operator's list.

`elevated` is the deliberate exemption. It appears in 4 of 109 known-good documents and every
one is market vocabulary ("volatility is elevated and still contained"). Only the transitive
verb forms are banned.

**2. The detector's 0-100 score is not a gate.** It is normalised by `log2(words/50)` and means
nothing against our copy until baselined on a corpus of ours.
`research/ai-script-style-2026-07-16.md:26,54` already ruled that a tool's score is not an
editorial gate. BLOCK is a **category list**; the score rides in the receipt as a metric.

## Calibration — the numbers, and how to reproduce them

```
py tools/ai_writing_gate.py --survey productions/*/vo.txt          # 16 docs
py tools/ai_writing_gate.py --survey <shipped social copy fields>  # 93 docs
```

All **18 armed BLOCK categories silent on all 109 known-good documents.** Five categories do
fire on correct copy and are demoted to WARN with the reason inline: `em-dash` (20/93),
`low-ttr` (14/16), `hashtag-stuff` (5/93), `hollow-intensifier` (3/16),
`cross-para-burstiness` (1/93).

`--survey` **exits non-zero** if an armed category ever fires on known-good copy. That is the
re-arming gate after any detector bump.

Corpus note: the first extraction pulled 889 copy fields from `social-ops/*.json`, but most were
competitor-watchlist and liked-video text. Calibrating on those would have taught the gate that
other people's slop is our normal. The corpus is our own shipped copy only.

## Remaining runbook

1. Review and merge [tradercockpit-ops PR 1](https://github.com/javin23863/tradercockpit-ops/pull/1)
   into `ops/main`. Until then the gate is not in the lane.
2. Pull `ops/main` into the shared clone, then confirm the gate is live:
   ```
   py tools/ai_writing_gate.py --selftest
   py tools/ai_writing_gate.py productions/<latest-daily>
   ```
3. Move `social.ai-writing-gate` Verify → Done (operator only).
4. `git worktree remove C:\tmp\tradercockpit-ai-write-gate`.

## Stated ceilings — what this does NOT do

- **Not a rewriter.** It blocks and names the pattern; it has no write path, so it cannot touch
  numbers, named entities, attributions or the causal direction of a claim.
- **Social batch only.** `daily_postclose` and the series lane are untouched. Extending is a
  separate ask, and needs its own `--survey` against that lane's copy first.
- **All stylometric signals stay WARN** (burstiness, punctuation distribution, function-word
  trigram entropy, type-token ratio). They fire on correct market copy. Promoting one requires a
  clean survey, not an opinion.
- **Three surfaces now cover AI-writing** — `no-ai-slop` prose, `avoid-ai-writing` prose, this
  gate's code. Reconciled by hand in `.claude/skills/avoid-ai-writing/PROVENANCE.md`, one owner
  per word. A fourth surface will drift it.
- **Node is now a hard dependency of the social batch.** Already present (v24, Remotion). If it
  vanishes the gate BLOCKs rather than passes — correct direction, but it will read as a false
  alarm.

## Standing constraints restated

- A gate that documents without blocking reads as approval; silence is never a pass.
- Gate-softening is presumed wrong — a blocker, not a merge.
- Calibrate the instrument before production: a positive must fire and a negative must pass, or
  the gate is not information.
- Vendored code is stale by default. `VERSION` pins the upstream commit and upstream's own suite
  is vendored so a bump is checkable; re-run `--survey` before re-arming.

## Graph state

The code graph at `graphify-out/` was rebuilt this wave (11,598 nodes / 22,939 edges) but it
indexes the shared clone, which is on `ops/main` — **so it does not contain `ai_writing_gate.py`
or the vendored detector until PR 1 merges.** Querying the graph for them returns nothing, and
that absence is the graph being correct, not the gate being missing. Re-run
`graphify update .` after the merge.

The ops-vault graph is rebuilt by `vault_sync.py` and carries no repo sources — it is the wrong
graph for this question either way.

## Coordination

Wave ran in its own worktree `C:\tmp\tradercockpit-ai-write-gate` on branch
`feat/ai-writing-gate`, rebased onto `ops/main` so the PR carries one commit and does not bundle
the ep02/v41 handoff commits from `fix/news-shot-capture-and-visual-qa-master`. The shared clone
was left untouched. `origin` is the slimmed **public** repo and carries no `tools/`; all of this
went to `ops`.
