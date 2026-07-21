# AI-sounding script research

Date: 2026-07-16  
Scope: English market-news narration for TraderCockpit. Existing uploads are out of scope and must remain unchanged.

## Bottom line

The failure is not simply “AI vocabulary.” The recurring problem is a voice that is statistically average, structurally predictable, abstract where a market commentator should be concrete, and polished enough to erase the speaker’s point of view. A word blacklist alone will produce bland copy. The safer fix is to draft from a specific TraderCockpit thesis and a small corpus of preferred prior scripts, then run a narrow style audit without allowing that audit to rewrite facts.

For the next iteration, borrow the useful checks from open-source projects but do not add a generic humanizer dependency. TraderCockpit already has an editorial gate; a short local rule set plus a read-aloud review is the smallest reliable solution.

## What people react against

These patterns recur across research, practitioner guidance, and direct audience complaints:

1. **Genre mismatch.** Instruction-tuned LLMs retain an informationally dense, noun-heavy style even when asked for informal language. In a peer-reviewed comparison, they used present-participial clauses two to five times as often as human text and nominalizations 1.5 to two times as often. That is a poor default for spoken market commentary. [Reinhart et al., PNAS 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11874169/)
2. **Low specificity and low variation.** A 2026 multilingual study found that the largest gaps between human and machine text were concreteness, cultural nuance, and diversity. Explicitly prompting for those distinctions improved results in more than half of the tested cases. [Wang et al., ACL 2026](https://aclanthology.org/2026.acl-long.639/)
3. **Averaged, repeatable construction choices.** A pairwise study of human and LLM news text found human text had the greatest grammatical-construction diversity, while LLM outputs were more similar to one another. [Weissweiler et al., ACL 2025](https://aclanthology.org/2025.acl-long.443/)
4. **Voice normalization during rewriting.** Even prompts asking an LLM to preserve voice did not remove the directional pull toward a more polished, less situated register; first-person markers and contractions fell while abstraction and punctuation elaboration rose. This is a 2026 preprint, so treat it as suggestive rather than settled. [van Nuenen, 2026](https://arxiv.org/abs/2604.22142)
5. **Post-editing is not enough by itself.** In a preregistered study of 81 participants, post-editing moved LLM drafts toward each writer’s style, but the results remained closer to LLM text and less diverse than unassisted writing. [Baumler et al., 2026](https://arxiv.org/abs/2604.24444)
6. **Performative depth.** Wikipedia’s community-maintained field guide repeatedly flags negative parallelisms (“not X, but Y”), ornamental groups of three, superficial `-ing` analysis, inflated significance, vague attribution, canned conclusions, and formulaic em-dash emphasis. Its key caveat matters: these are possible indicators, not proof of AI authorship. [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
7. **The same tells are audible in video scripts.** A recent YouTube discussion specifically complained about constant triplets, repeated corrective contrasts, and stock LLM vocabulary. The thread also contains the necessary counterpoint: some listeners care more about entertainment and accuracy, and any one phrase is prone to false positives. This is direct anecdotal evidence, not a population study. [r/youtube discussion](https://www.reddit.com/r/youtube/comments/1ug9gjb/ai_scripts_on_youtube/)

## TraderCockpit script rules

Use these as editorial checks, not as a detector score.

1. **Lead with the take.** The first two sentences must state what changed and why it matters to a portfolio. Delete “here’s what you need to know,” “let’s break it down,” and other announcements.
2. **Name the actor and the mechanism.** Prefer “Brent rose after…” to abstract sentences about “uncertainty,” “pressure,” or “the evolving landscape.” Every paragraph needs at least one concrete noun: person, institution, route, security, price, date, or threshold.
3. **Make one defensible judgment per beat.** Facts stay sourced; the host’s interpretation should sound like a real market participant with a view. Use “My read is…” or “What I care about here is…” only when a genuine judgment follows.
4. **Stop narrating the verification process.** Do not say a chart is “verified in TradingView” or that a claim was “confirmed” merely to reassure the viewer. Show the source; speak the market implication.
5. **Zero decorative contrast templates by default.** “Not just X, but Y,” “This isn’t X; it’s Y,” and close variants are allowed only when correcting a real misconception and never more than once in a 10-minute script.
6. **Use the natural number of items.** Three items are fine when the evidence has three components. Do not manufacture triplets for cadence.
7. **Cut unearned profundity.** Remove aphorisms, inflated metaphors, generic “turning point” language, and dramatic fragments that do not add a fact or a take.
8. **Vary spoken rhythm deliberately.** Mix short and long sentences, contractions and plain statements. Read the script aloud; punctuation should serve breath and emphasis, not page aesthetics.
9. **No vague authorities.** Replace “analysts say,” “experts believe,” and “markets are watching” with a named source or with TraderCockpit’s clearly labeled interpretation.
10. **No automatic summary ending.** Finish on the decision variable, invalidation level, or next event that can change the thesis. Add the call to action after the editorial ending, not instead of it.
11. **Protect the preferred voice corpus.** Extract measurable habits from the operator-approved Fable-era scripts: sentence-length range, contraction rate, first-person frequency, humor/edge, transition style, and how conclusions land. Use those scripts as few-shot references at draft time. Do not ask a later “humanizer” pass to invent personality.
12. **Separate fact and voice passes.** Lock claims and source mapping first. The voice pass may change phrasing and rhythm but cannot add, remove, intensify, or generalize a factual claim.

## Open-source options

| Project | What it offers | License / maintenance signal as of 2026-07-16 | Fit for TraderCockpit |
|---|---|---|---|
| [blader/humanizer](https://github.com/blader/humanizer) | A portable prompt/skill derived from Wikipedia’s field guide; includes voice calibration from user samples and a 33-pattern checklist. | MIT; README reports v2.8.2, 39 commits, 29.3k stars, and ongoing version history. | Best reference catalog. Reuse a small attributed subset of rules; do not run its unrestricted rewrite loop over sourced market copy. |
| [yzhao062/agent-style](https://github.com/yzhao062/agent-style) | Generation-time rules plus an optional review pass. Its canonical rules cite established writing guides. | Rules/content are CC BY 4.0; enforcement code is MIT; latest listed release v0.3.5 on 2026-04-29. | Useful architecture, but the project explicitly puts marketing copy and long-form narrative outside scope. Reference only. |
| [stephenturner/skill-deslop](https://github.com/stephenturner/skill-deslop) | Directness, rhythm, trust, authenticity, and density rubric; catalogs formulaic AI patterns. | MIT; only one commit shown, and the README says it synthesizes other projects. | Useful vocabulary for a review rubric, not a dependency or authority. |
| [vale-cli/vale](https://github.com/vale-cli/vale) | Mature, customizable, markup-aware deterministic prose linter. | MIT; 1,908 commits; latest listed release v3.15.1 on 2026-06-12. | Good fallback if the local rule set grows. Do not install now: the existing TraderCockpit editorial gate can cover the small required rule set more cheaply. |

## Warning on “humanizers” and detectors

- Do not optimize for “bypassing AI detection.” Wikipedia warns that detectors have non-trivial error rates and can fail under paraphrasing, formatting changes, or unseen models. The target is audience trust and a recognizable voice, not an evasion score. [Wikipedia caveat](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing#AI_detection_tools)
- Do not send unpublished scripts or source material to unsourced hosted humanizer services. Many publish no method, evaluation set, license, privacy boundary, or factuality test.
- Do not accept a tool’s “human” score as an editorial gate. A script can avoid common tells and still be generic, inaccurate, or lifeless.
- Do not let a style rewriter touch numbers, named entities, quotations, attributions, probabilities, chart levels, or the causal direction of a claim.

## Recommended implementation decision

Keep this local and small:

1. Build the voice baseline from the approved Fable-era TraderCockpit scripts.
2. Add a warning-only check to the existing editorial gate for repeated corrective contrasts, ornamental triplets, vague authority, stock signposting, generic endings, and repeated sentence lengths.
3. Draft with the voice baseline present from the first prompt; do not bolt personality on after narration and visuals are produced.
4. Require one read-aloud pass and one operator script approval before TTS and visual assembly.
5. Measure success with revision count, operator acceptance on first review, and audience retention—not an AI-detector score.

