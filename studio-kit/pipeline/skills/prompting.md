# 🎬 SKILL — Prompting
_how to write the generation prompt so the model nails it. Apply EVERY video. Rules compound as we study more references._

## from: Seedance 4K hyperreal AI short film breakdown (Adil) (2026-07-05T17:43:42.646Z)
- Route every generation prompt through a prompt assistant (Claude with a dedicated prompt skill) loaded with all your asset images — it writes pro-level prompts with the assets locked in.
- Over-specify: camera movement, character actions, room layout, what's playing on screens — the more detail you give, the better the output.
- Never give the model open freedom on in-frame text or screen content — spell out exactly what plays, or the text turns into slop.
- When using a video reference, set the generation to the reference's exact duration — a mismatch makes the model start inventing.
- Iterate with surgical edits (change the angle, add slow-mo, rewrite how a creature enters) rather than rewriting the prompt wholesale.
- Specify motion mechanics precisely ("the bird glides, doesn't flap its wings") to kill unwanted movement.

## from: AI commercial/ad workflow (Adil) (2026-07-05T17:53:13.984Z)
- Never write video prompts by hand — load a Claude SKILL that encodes exactly how the video model wants shots described, what holds consistency and what breaks it, so Claude stops guessing.
- Give Claude three things: the full script (one beat per scene), every locked asset UPLOADED (not described — the more it sees, the better it writes), and a NAME for each asset.
- Demand one CONNECTED shot-list document: a STYLE PREFIX block (lighting, camera, color) glued to every prompt — change it once, it changes everywhere.
- Name every prompt (1A, 1B…) so you can edit like an editor — "edit prompt 1A, do this" — and only that prompt changes while everything else stays locked.
- Override the prefix per scene when the location demands it ("for scene 2 only, override the prefix lighting…").
- Never write "he dances" — it means nothing to the model. Spell choreography out move by move: "two head nods, shoulder rolls one at a time, a knee dip, a finger snap, a quarter spin at the door."
- Write cut-by-cut choreography with named cuts, each with a style and specific moves, including the trigger that starts the action ("on a tap of the ear cup").

## from: Hell Grind AI feature film — 28 pro tips (Higgsfield) (2026-07-05T17:56:56.911Z)
- Build a SYSTEM PROMPT and keep polishing it (the team spent a full week on one): CN-safe language rules, on-screen text rules, density control (ONE idea/action/camera strategy), reference-image discipline, mode-selection rules (text-to-video / image-to-video / reference-to-video / video-to-video → correct output settings), and the X/Y frame coordinate system.
- For emotional scenes, give BOTH situational context (what the character feels — pure terror, watching a loved one disappear) AND anatomical behavior (arm fully extended, fingers spread, jaw dropped, lands on hands and knees).
- More detail beats less: specify when to cut, to which angle, and to whom — every unspecified choice is room for the model to hallucinate the wrong motion.
- Expect the first patch to fail: compare what landed vs. didn't, adjust the prompt, run again — iteration is the workflow, not the fallback.
- Salvage partial wins in-prompt: if the first 5s of a 15s clip work, instruct the model to change only the last 10s.
- On shot lists, tell Claude to "optimize the shot list and update ONLY what changed" — it rewrites just the active prompt and cuts tokens ~80%.
- When iterations bloat a prompt with conflicting instructions, tell Claude to "optimize, study the context, and sanitize the prompt" — stripping the cruft measurably improves results.
- Spell dialogue PHONETICALLY (write what it SOUNDS like, not the real spelling) for complex or invented words.

## from: Reference clips — ultra-realism prompt structures (2026-07-05T18:02:10.691Z)
- Use the full Strategy-A prompt stack in order: Subject (exhaustive + identity lock) → Location (detail + exclusions) → Visual Style → Camera Style → timestamped beat breakdown → Audio → one-line Goal.
- For the Visual Style field, use this transferable phrasing verbatim (swap content, keep structure): "Ultra-realistic documentary realism. Genuine candid behavior. Natural body language. Unscripted slice-of-life feeling. Strong environmental authenticity."
- For I2V, prompt ONLY the motion between the start and end frames, then close with the convergence command: "lands exactly in the final position of the end frame."
- Use "dual growth" / layered-detail phrasing for complex shots: describe an action happening in real space AND simultaneously on a screen within the frame, both growing/charging together.
- Keep one master list of negative constraints and reference it across categories rather than restating: "No stabilization. No cinematic camera moves. No modern color grading. No music. No sound design. No narration." — telling the model what NOT to do is as important as what to do.

## from: Hell Grind Ep2 — full unedited AI-film process (Adil): style-prefix, 44-iteration locations, diagnosis loop, team collab (2026-07-05T19:07:32.448Z)
- Iterate prompts exclusively through the assistant with change-notes; never hand-edit a long generated prompt.
- Order references to match the prompt: the reference described first goes first (character before location), and attach only the assets that shot actually needs.
- Embed failure-mode handles INSIDE the prompt ("do not drift the Polaroid") — prompt-embedded guards outperform side-notes.
- Address prompts by ID ("for prompt 21A, [change]") so the assistant updates them in the tracked shot list and every revision stays findable.
- For engines with hard character caps (Seedance 2.0 launched with a 3,000-character limit and worked better in Chinese), prompt in the denser language — Chinese packs ~1-2 chars/word vs English 5-10, so far more direction fits the budget; verify current caps per engine.
- Describe spatial layouts with odd specificity — counted doors, wall-by-wall contents — because vague geography is what the model gets wrong.
