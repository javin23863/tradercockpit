# 🎬 SKILL — Image Generation
_sheets, backgrounds, model-switching, quality checks before animating. Apply EVERY video. Rules compound as we study more references._

## from: Seedance 4K hyperreal AI short film breakdown (Adil) (2026-07-05T17:43:42.642Z)
- Create a new folder per project from day one — asset management is a habit, so finding anything three months later is easy.
- Generate reference images at maximum quality (4K) — the better the input image, the sharper the final video.
- Run several generation batches and cherry-pick; never settle for the first acceptable result.
- There is no one best model — route by strength: GPT Image 2.0 at 4K for reference sheets, Soul Cinema for cinematic locations and from-scratch characters (cheapest at ~1 credit per 8 images), Nano Banana Pro when depth/realism falls flat — switch models before fighting the prompt.
- Save every finished asset (character, location, prop) as a named element the moment it's approved.
- Quality-check every image BEFORE animating — depth, shadows, natural detail — because flaws in the still compound in the video.

## from: AI commercial/ad workflow (Adil) (2026-07-05T17:53:13.982Z)
- Route each job to the right model: Soul Cinema for photoreal character sheets (skin texture), GPT image 2.0 for product/location/sheet editing, AI Cast for fast side characters.
- One product image isn't enough — build a product sheet (front + 3/4 perspective) so the model sees it from every angle and can't hallucinate it mid-scene.
- Work on a canvas: drag every candidate side by side, compare, and drag the winner to the top to lock it — nothing gets lost.
- Solve variants and state changes in image-land, not video-land: images are cheap, videos aren't — build the second sheet instead of burning video generations.
- Preserve quality across edits with masking: every GPT-image edit softens the asset toward flat plastic AI-slop, so stack the crisp original on top of the edited version and mask out only the changed region (the outfit) — face, skin, and background stay from the original.

## from: Hell Grind AI feature film — 28 pro tips (Higgsfield) (2026-07-05T17:56:56.910Z)
- Prompt like a photographer: name the lens, camera, aperture (e.g. "stopped down two stops from wide open"), film stock, grain, halation, bokeh, and the light sources — words like "photorealistic, cinematic, high quality" do NOTHING.
- Don't know gear? Ask Claude — or screenshot a frame from a movie you love, ask Claude what camera/lens shot it, and put those specs in your prompt.
- Apply the 60/30/10 color rule: 60% dominant color, 30% secondary, 10% accent — the split cinematography uses constantly.
- Specify "PRACTICAL LIGHT ONLY" (sun, windows, lamps that are IN the frame) — an artificial extra light behind characters makes them look plopped-in and plasticky.
- If you love one moment of a generation, screenshot that frame, upload it to Claude, and use it as the REFERENCE for positioning/lighting in the next generations.
- Quality-check the still before animating: plasticky skin, too much light on faces, or a cheap-looking element (like a bad portal) means regenerate that element now, not after animation.

## from: Reference clips — ultra-realism prompt structures (2026-07-05T18:02:10.690Z)
- For start/end-frame I2V shots: generate the START FRAME image first, then the END FRAME image, then write the video prompt to describe ONLY the motion between them.
- Generate new start frames from an existing reference using the "Recreate this image with the following changes: …" pattern — list each change explicitly (e.g., "POV view; instead of looking ahead, make it appear as if he is filming the sky, with the small car above him. His arm raised higher, filming a black dot in the sky").
- Iterate by generating new first frames and chaining them into the same shot until the look clicks (workflow: Supercomputer + Canvas).
- Quality-check every anchor frame before animating — the start and end frames are the two locks that determine whether the motion converges.

## from: Hell Grind Ep2 — full unedited AI-film process (Adil): style-prefix, 44-iteration locations, diagnosis loop, team collab (2026-07-05T19:07:32.445Z)
- Batch 4 images per prompt; with a detailed prompt the model is consistent, so repeated errors mean the PROMPT is wrong — fix the prompt, don't re-roll.
- Don't read the long prompts — skim the 4 outputs and tell the assistant only what to change ("front wall red, couch blue, colder tones, add light atmospheric haze"); iterate through the assistant, never hand-edit.
- Fight the plasticky default look with lighting keywords: "light atmospheric haze," "film grain," "crush the blacks to add shadow depth."
- Every edit pass loses detail — re-edit from the earlier clean source image ("edit the PREVIOUS image again"), never from the latest output, so artifacts don't compound.
- When the layout is right but edits keep drifting the spatial layout, stop editing and regenerate from scratch with the full detailed prompt and NO reference image to lock a clean version.
- Quality-check the still before animating: plastic textures, wrong geography, or drifting faces disqualify it.
