# 🎬 SKILL — Characters
_character sheets, consistency, outfits, aging, diversity (avoid clone armies). Apply EVERY video. Rules compound as we study more references._

## from: Seedance 4K hyperreal AI short film breakdown (Adil) (2026-07-05T17:43:42.640Z)
- Generate character sheets on a gray background — tested to outperform white or black backgrounds for downstream consistency.
- Include one view with the face clearly visible plus one full-body view for the outfit (or a full three-view sheet) so the video model never has to guess.
- To change an outfit, upload the existing character sheet to your prompt assistant and ask for an outfit-swap prompt — never re-describe the character from scratch.
- Specify age explicitly (e.g., "woman aged 40–45") and pick the take whose wrinkles and aging look most natural.
- Save every approved character as a named element immediately so the prompt tool can auto-reference it in every later scene.
- For armies and crowds, build ONE sheet containing several distinct character variants and reference that image — a single-character reference produces an army of clones.

## from: AI commercial/ad workflow (Adil) (2026-07-05T17:53:13.981Z)
- Build the hero as a character sheet: two panels, close-up + full body, front and back, on a gray background — the close-up gives the model the exact face to lock onto, the full body gives height and build.
- Use gray backgrounds deliberately: zero clutter competing with the character means a much higher win rate of usable generations.
- Generate photoreal character sheets in Soul Cinema (best for photorealistic looks); run many cheap batches (8 images = 1 credit) and scroll until a face stops you.
- Never lock from stills alone — grab several candidates and test them with actual footage, because a face that looks great as a still can fall apart the moment it moves.
- Use AI Cast for side characters: one prompt returns an instant sheet with multiple styling options; spend less care here and pick the one that fits the story role.
- Kill the multi-face problem: erase every extra face from the sheet in GPT image 2.0 so the video model has exactly one face to grab — do this for every character, or it drifts.
- Generate outfits systematically: ask Claude for 10 outfit prompts from the character image, run all 10 in GPT image 2.0, then combine the best pieces into one prompt ("shirt from look 2, make it pink, jeans from look 1").
- For mid-scene state changes (dry → soaked), build a second sheet on purpose (e.g., hero_wet) instead of asking words to transform him — the face drips off and the model improvises.

## from: Hell Grind AI feature film — 28 pro tips (Higgsfield) (2026-07-05T17:56:56.909Z)
- Cut the face OUT of the wide/full-body shot in every character sheet — the wide-shot face is plasticky and mismatched; removing it forces the model to lock onto the good close-up face.
- Lock every character STATE as its own separate asset (e.g. initial with skateboard → after-fight injuries → partially transformed → fully transformed) so nobody ever grabs the wrong version.
- Script-supervise like live action: track each character's injuries, clothing, props, and what they're holding or missing across the whole film.
- Store all character-state assets on a shared canvas so any team member can pull the correct one instantly.

## from: Reference clips — ultra-realism prompt structures (2026-07-05T18:02:10.689Z)
- Describe the main subject exhaustively in every prompt: exact age, full clothing breakdown, hairstyle, and "realistic skin texture, minimal makeup."
- Include "personality" in the subject description specifically to drive candid body-language generation — it tells the model how the person should move and behave, not just flavor text.
- Append a verbatim identity-lock line to every character prompt: "Maintain consistent identity, clothing, hairstyle, and appearance throughout the entire video."
- For UGC realism, dress characters in everyday, relatable clothing — avoid glam, styled, or editorial looks that break the unproduced feel.

## from: Hell Grind Ep2 — full unedited AI-film process (Adil): style-prefix, 44-iteration locations, diagnosis loop, team collab (2026-07-05T19:07:32.444Z)
- Build character sheets for faces and upload them to the prompt-writer; if a prompt describes appearance too fully, the model invents new characters even with sheets attached.
- For small in-world images of characters (e.g. a Polaroid), have the assistant describe ONLY clothing, never facial appearance — the sheets carry the face.
- Tag characters explicitly (@Lulu, @Roco) when the shot needs them anchored.
- Prepare age variants of each character (adult vs teenage sheets) and pick the version the story beat requires.
