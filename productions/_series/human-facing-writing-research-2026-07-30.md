# Human-facing writing research and minimal integration design

Date: 2026-07-30  
Status: research and interface design only; no dependency installed, episode edited, or remote system changed

## Decision

Do not install or clone `blader/humanizer` or StoryScope.

TraderCockpit already has a broader Humanizer-derived editing skill and a pinned deterministic
AI-writing detector. The useful delta is smaller:

1. freeze facts, claims, disclosures, hashes, and operator voice before any prose rewrite;
2. refine only the human-facing prose, never the evidence objects;
3. verify the rewrite against that frozen contract;
4. run the existing prose and teaching-claim gates on every declared public surface;
5. bind the resulting receipt to the exact files delivered.

The success metric must be accurate, useful writing in the operator's real register. "Undetectable
as AI" is neither a defensible quality target nor a claim these sources support.

## Primary sources reviewed

| Source | Version/status reviewed | What it establishes |
|---|---|---|
| [blader/humanizer `SKILL.md`](https://github.com/blader/humanizer/blob/main/SKILL.md) | Skill metadata reports v2.9.1 | A prose-editing workflow: preserve information over shape, do not invent facts, calibrate against author samples, audit the first rewrite, then revise. |
| [blader/humanizer repository](https://github.com/blader/humanizer) | `main`, reviewed 2026-07-30 | The project describes 33 surface/content patterns and explicitly warns that isolated patterns have false positives. |
| [blader/humanizer license](https://github.com/blader/humanizer/blob/main/LICENSE) | MIT, copyright 2025 Siqi Chen | Reuse or substantial copying requires retaining the copyright and permission notice. |
| [StoryScope paper](https://arxiv.org/abs/2604.03136v4) | arXiv v4, 2026-04-13; preprint under review | A study of discourse-level narrative attributes in long-form fiction, not nonfiction video scripts. |
| [StoryScope PDF](https://arxiv.org/pdf/2604.03136) | v4 paper text | The dataset, method, results, limitations visible from study design, and the authors' AI-use and Books3 statements. |
| [StoryScope repository](https://github.com/jenna-russell/storyscope) | `main`, reviewed 2026-07-30 | Code, taxonomy, trained models, and configuration are published for the fiction study. |
| [StoryScope code license](https://github.com/jenna-russell/storyscope/blob/main/LICENSE) | MIT, copyright 2026 Jenna Russell | Code reuse requires the MIT notice. |
| [StoryScope paper license](https://creativecommons.org/publicdomain/zero/1.0/) | CC0 link selected by the arXiv record | The paper is dedicated to the public domain to the extent allowed by law; citation remains good research practice and endorsement must not be implied. |

## What Humanizer contributes

Humanizer's directly useful rules for factual teaching scripts are:

- preserve every original claim even when paragraphs are merged, split, or compressed;
- never add a fact, name, number, date, quote, or citation;
- use the author's own sample to calibrate sentence rhythm, vocabulary, punctuation, recurring
  phrases, and transitions;
- keep specific, unusual detail and real self-corrections instead of sanding them into generic
  prose;
- cut vague attribution, inflated significance, generic conclusions, fake-candid openers,
  assistant pleasantries, synonym cycling, and ceremonial signposting;
- run a draft, audit, and final rewrite loop;
- in file mode, leave code blocks, frontmatter, data, and link targets untouched.

These are editing instructions, not an authorship test. Humanizer itself says clean human writers
can trigger its patterns, recommends looking for clusters rather than isolated signals, and lists
common false positives such as an em dash, formal vocabulary, polished grammar, or one short
emphatic sentence. Its own no-fabrication rule is stronger and more relevant here than its
"sounds human" framing.

### What is already present

TraderCockpit's `.claude/skills/avoid-ai-writing/SKILL.md` already attributes multiple rules to
`blader/humanizer`, including direct-positive rewrites, manufactured-punchline cleanup,
aphorism cleanup, fake-candid openers, and "personality and soul." The executable
`tools/ai_writing_gate.py` wraps the pinned `conorbronsdon/avoid-ai-writing` detector and adds the
house-ban vocabulary. Its provenance and MIT notice already live under
`tools/vendor/avoid-ai-writing/`.

Adding another installed Humanizer copy would create two owners for the same patterns and an
upgrade/reconciliation problem. Reuse the existing skill and detector; add only the missing
fact-preservation and surface-coverage contract.

## What StoryScope contributes, and what it does not

StoryScope studies 61,608 stories derived from 10,272 prompts. The stories average about 4,753
words and come from human-written short fiction plus five LLM sources. It extracts hundreds of
narrative variables and reports 93.2% macro-F1 for human-versus-AI classification using strict
non-style narrative variables. In a 278-story Gemini subset edited with LAMP, the narrative
classifier reports 93.9% macro-F1, only 1.6 points below its result on the unedited stories.
The authors' interpretation is that surface cleanup does not change the underlying narrative
choices their classifier measures.

That result supports one narrow production lesson: a word-substitution pass cannot repair a
generic content architecture. The lesson must be conceived around real evidence, a real question,
and the operator's actual point of view before a surface editor touches it.

The following findings are useful as editorial questions, not gates:

- Is the script explaining the moral after the evidence has already made it clear?
- Does every beat resolve too neatly, with no honest uncertainty or limitation?
- Does the script use named sources and concrete artifacts, or vague allusions?
- Is the viewer addressed as a participant with something to inspect and decide?
- Does the sequence contain a real reversal from the evidence, rather than a manufactured
  rhetorical reveal?

### Fiction-only or unsafe to transfer

Do not port StoryScope's classifier, taxonomy, model weights, or thresholds into this lane.

- Its evaluation domain is long-form fiction, not 1,200-1,900-word spoken finance lessons.
- Fiction attributes such as protagonists, moral ambiguity, subplots, dream sequences, sensory
  embodiment, flashbacks, and ambiguous endings are not evidence of quality in a technical
  explanation.
- Clear causality and a single teaching through-line are often virtues in instruction even though
  the study associates tidy causal structure with its AI fiction.
- The reported F1 scores measure performance inside the paper's constructed corpus. They do not
  establish a general detector for YouTube scripts, authorship, originality, or audience trust.
- The paper is a preprint under review. Its findings should be described as study results, not
  settled universal rules.
- The feature extraction and application pipeline itself relies on LLM annotation. Its
  interpretability does not make each feature assignment ground truth.

The paper states that the human stories came from Books3, are not released because of copyright,
and were used only for academic analysis. The authors explicitly do not endorse Books3 for model
training or commercial text generation. TraderCockpit should not download, ingest, or repurpose
those human stories. Nothing in the proposed design requires them.

## Why "undetectability" is the wrong metric

Optimizing for a detector produces detector-shaped prose:

- it can flatten the operator's real habits because a legitimate quirk resembles a listed tell;
- it rewards lexical evasion even when factual structure remains generic;
- it invites adversarial bypass tricks rather than better explanation;
- it encourages false certainty from scores that were not calibrated for this genre;
- it can obscure AI assistance instead of preserving an honest production record;
- it can damage accessibility and comprehension by adding mess merely to look statistically rare.

The current gate already has the right principle: `tools/ai_writing_gate.py:18-23` says its
0-100 detector score has no meaning against TraderCockpit copy without a baseline. It blocks only
specific categories measured silent on the known-good corpus and leaves broader rhythm signals as
warnings. Keep that boundary.

The priority order should be:

1. factual and claim integrity;
2. operator ownership and mouth-feel;
3. viewer comprehension and usable takeaways;
4. promise/title/script agreement;
5. exact artifact and disclosure consistency;
6. AI-pattern findings as lint, never a target score.

## Current integration gaps

1. `tools/episode_gate.py:63-89` runs `script_style_gate` and `ai_writing_gate`, but it does not
   run `teaching_claim_gate`.
2. Passing an artifact directory to `ai_writing_gate` reads only `vo.txt`
   (`tools/ai_writing_gate.py:223-233`). Titles, thumbnail copy, descriptions, chapter labels,
   end-screen text, and other audience-facing fields are outside that check.
3. `tools/teaching_claim_gate.py:61-101` already has the right core mechanics: the claim ontology
   is bound to the script SHA-256, every spoken paragraph has exactly one receipt ID, factual
   paragraphs require academic or run-receipt sources, and delivery-only paragraphs must explain
   why they are non-claims. The missing problem is chain placement, not a new claims system.
4. `tools/episode_gate.py:253-314` binds certification to the master hash and records selected
   source-file hashes, but no one writing receipt covers the complete public-surface set.
5. The series skill already requires the operator's spoken capture before drafting and says the
   skill supplies structure, never voice (`.claude/skills/series-script/SKILL.md:103-107`). Any
   refinement layer must preserve this ordering.

## Proposed deep module

One module, two public entry points:

```text
prepare(surface_manifest, claim_ontology, voice_pack) -> prose-contract.json
verify(prose-contract.json, candidate_surface_manifest) -> prose-receipt.json
```

The rewrite itself stays in the `human-facing-writing` skill. This keeps provider/model decisions
out of the deterministic module and preserves the repository's model-agnostic production rule.

### `prepare(...)`

The module reads an explicit manifest of every audience-facing surface. It refuses discovery by
glob because a missed file would look clean.

It writes a hash-bound contract containing:

- source path, surface type, preservation mode, and SHA-256;
- ordered claim IDs and their source/limitation bindings;
- protected literals: numbers, percentages, currency, dates, symbols, timeframes, parameter
  values, run IDs, commit hashes, artifact hashes, citations, locators, URLs, exact quotes,
  disclaimers, synthetic-media disclosures, and receipt IDs;
- protected non-prose regions: code, frontmatter, data blocks, link targets, table schemas, and
  stage markers;
- the exact operator capture and approved phrase-bank sample hashes used for voice calibration;
- whether a surface must preserve all claims (`script`, `description`) or may select a sourced
  subset without adding one (`title`, `thumbnail`, `chapter label`).

### Refinement step in the skill

The skill receives only the source prose, the protected contract, and the operator voice pack.
Its order is:

1. preserve the meaning and protected literals;
2. match the operator's recorded cadence and vocabulary;
3. remove generic AI-writing patterns using the already-installed skill;
4. read the result aloud;
5. run an independent critic against the contract;
6. return a candidate, never a silently approved replacement.

It may vary sentence length, merge paragraphs, move a limitation closer to its claim, and remove
empty ceremony. It may not invent first-person experience, rhetorical uncertainty, a citation,
or a colorful detail. First-person statements about the operator are factual claims unless they
appear in the operator capture or have a receipt.

### `verify(...)`

The verifier fails closed when:

- a source hash or voice-pack hash changed after contract preparation;
- a protected literal or protected non-prose region changed;
- a rewrite surface loses or adds a claim;
- a subset surface introduces a claim ID absent from the source ontology;
- a factual paragraph lacks a receipt or limitations field;
- an audience-facing path exists outside the manifest;
- the independent claim-diff critic reports a new, altered, or broadened proposition that is not
  mapped to a receipt;
- an existing `script_style_gate`, `ai_writing_gate`, or appropriate teaching-claim check blocks;
- the candidate's exact file hashes do not match the receipt.

The receipt records findings and hashes, not a "human probability." A model critic can find
semantic drift, but it cannot certify truth. Receipts and operator approval remain authoritative.

## Hooks

Use one project skill, `human-facing-writing`, as the orchestration hook:

1. **Series drafting:** after the fact pack and operator capture, before narration/TTS.
2. **Packaging:** after the title/thumbnail promise is chosen, before thumbnail rendering.
3. **Episode gate:** require `teaching_claim_gate` and the exact `prose-receipt.json`; missing,
   stale, or partial receipts block.
4. **Publish boundary:** verify the certified master plus the exact title, description, chapters,
   and disclosure text selected for upload.

Do not add another Humanizer detector, StoryScope runtime, XGBoost dependency, dataset, or
"human score." The existing drafting skill, detector, claims ontology, and episode receipt cover
the machinery once the two-entry-point contract connects them.

## Acceptance tests for an implementation wave

The smallest meaningful test set is adversarial:

- change `200` to `2,000`: block;
- change a parameter, ticker, timeframe, run ID, URL, citation locator, disclaimer, or hash: block;
- remove one factual sentence from a full-preservation script rewrite: block;
- add a plausible but unsourced explanatory sentence: block;
- change only sentence rhythm while all claims and protected content survive: allow the candidate
  to proceed to the existing style/voice gates;
- omit a declared public surface or add an undeclared one: block;
- rewrite from an operator capture, then mutate that capture after preparation: block;
- produce a clean detector score while the claim contract fails: block.

The positive fixture should be one operator-approved paragraph with a deliberately awkward first
draft, the same claims after refinement, and an exact receipt tied to both source and output
hashes.

## Provenance obligations

- If implementation copies substantial wording or code directly from `blader/humanizer`, retain
  its MIT copyright and permission notice in a third-party provenance file. A locally written
  contract that applies the general editing ideas should still cite the upstream source but does
  not require vendoring the full skill.
- If any StoryScope code is copied, retain its MIT notice. This design needs no StoryScope code.
- Cite the StoryScope paper as Russell et al., arXiv:2604.03136v4 when discussing its results. Do
  not imply the authors endorse TraderCockpit's workflow.
- Do not reuse the Books3 human-story corpus. The paper's CC0 status does not erase third-party
  rights in underlying stories, and the authors intentionally excluded the human text.
- Preserve internal AI-assistance, model, source, and output-hash provenance. Preserve any
  required public synthetic-media disclosure. A prose editor must never be used to remove or
  soften a disclosure.
