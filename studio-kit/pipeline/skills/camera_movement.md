# 🎬 SKILL — Camera Movement
_how the camera moves so it feels shot, not generated. Apply EVERY video. Rules compound as we study more references._

## from: Seedance 4K hyperreal AI short film breakdown (Adil) (2026-07-05T17:43:42.644Z)
- Write the camera move into every video prompt — never leave movement to the model's discretion.
- Specify follow-behind tracking for chase and flight subjects instead of front-on coverage.
- Call slow-motion at the peak-action beat (flying past small elements, an impact) so viewers absorb the detail.
- Drop the camera to ground level to reveal surface texture (grass, terrain) that sells the shot as real.
- Verify crowds and scene geometry stay locked while the perspective shifts — any smearing means regenerate.

## from: AI commercial/ad workflow (Adil) (2026-07-05T17:53:13.983Z)
- Tie the camera to the subject's action and forbid static frames in the prompt: "open behind him and ease around to profile as he walks — no static."
- Get rig-grade movement by describing the rig: a snorricam locked to the body keeps the subject fixed while the world blurs past — moves that normally need a camera op and a day on location come free from description.
- When the camera will move through a space, make sure the location image was generated with depth (3/4 angle) for the model to hold onto.

## from: Hell Grind AI feature film — 28 pro tips (Higgsfield) (2026-07-05T17:56:56.910Z)
- Use a SINGLE continuous shot for maximum control — define the camera move and character action second by second within one generation.
- Commit to ONE camera strategy per shot (rule it in the system prompt) so the model doesn't blend conflicting moves.
- For action/dialogue, let one MULTI-SHOT generation hold several cuts — camera, lighting, and positions stay consistent across the internal cuts.

## from: Reference clips — ultra-realism prompt structures (2026-07-05T18:02:10.691Z)
- List the specific camera flaws you WANT in the prompt: heavy handheld shake, frequent autofocus hunting, lens breathing, exposure pumping when moving between sun and shade, occasional motion blur, subtle rolling shutter.
- Name a specific era/format aesthetic to govern the motion: "Early-2000s consumer DV camcorder aesthetic" (or whichever format matches your realism target).
- For POV tracking, describe the operator's body arc across the whole shot ("arms gradually lower as he follows the object down") so camera movement is motivated by the subject, not floating.
- Apply negative camera constraints (no stabilization, no cinematic camera moves, no modern color grading) — see the master negative-constraint rule in `prompting`.

## from: Hell Grind Ep2 — full unedited AI-film process (Adil): style-prefix, 44-iteration locations, diagnosis loop, team collab (2026-07-05T19:07:32.447Z)
- Write the camera move into the prompt per beat ("push the camera in from a medium to a closeup; door closed, he opens it, closeup on him") — never leave movement to the model.
- When a beat doesn't land (an action reads too quick), lengthen the shot and give the character a real action to complete — have him actually start walking.
- Judge movement against the slop test: intentional, motivated camera reads as cinema; a character standing oddly mid-room while the camera drifts reads as generated.
