# 🎬 COOKBOOK — AI FILM / NARRATIVE VIDEO: the full pipeline (script → locked film)

_The end-to-end, repeatable workflow for any narrative / multi-shot AI video, distilled from the pros' unedited process
(Hell Grind Ep2, Adil/Higgsfield — 15-person team, 10M credits; 44 iterations for ONE location; ~1 of 100 generations
makes the final cut). The `pipeline/skills/` files are the ATOMIZED craft; THIS is the ORDER you walk them in. Our
`generate-shot-pack.cjs` automates the prompt-authoring steps (2–3); the rest is the discipline that turns slop into cinema._

**North star:** quality comes from the ITERATION LOOP, not the first prompt. Expect to fail a lot; the frameworks below
turn failures into cinematic shots. Every shot must earn director-level approval or it doesn't make the film.

---

## PHASE 0 — LOCK THE FOUNDATION (do this ONCE per project, reuse everywhere)

1. **SCRIPT** — write the whole thing first, one beat per scene. Work 1–3 scenes at a time.
2. **STYLE PREFIX** (the #1 team-consistency tool — one block glued to EVERY shot): style · lighting · color · composition · audio.
   - **Lighting rule:** be specific — e.g. "natural light only, key light from sky and windows only." (Practical-light-only kills the plopped-in/plasticky look.)
   - **Audio rule (load-bearing):** environmental SFX ONLY — **NO music, NO subtitles.** WHY: Seedance gives ONE audio track and adds music in emotional moments, which you CANNOT separate in post. Add your own music when editing the full film.
   - **Color:** the 60/30/10 split (name the 3 colors) + the project's tone (warm/cold).
   - Store it on the shared canvas; paste it into every prompt-authoring session so every shot inherits the look.
3. **CHARACTER SHEETS** — gray-bg (#7A7A7A) closeup + full-body (front/back), single-face (erase duplicates). Lock every STATE the story needs as its own asset (teenage/adult, dry/wet, injured/transformed). → `generate-shot-pack.cjs --character "<brief>"`.

---

## PHASE 1 — SHOT LIST (automated) → `generate-shot-pack.cjs`

4. Feed the **concept + outcome** → the generator loads all 14 skills + reference structures and produces the connected
   pack (STYLE PREFIX + character/asset locks + location schematic + named shots + edit pass), via your own LLM (or paste-mode).
   The pros' "shot list builder" skill does the same job (split scenes into ~15s shots, tailored to the target video model,
   then map prompts onto scenes). Keep the shot list as a **living 2-column doc** (left = scene description, right = prompt)
   so every prompt is tracked + re-findable when you refine key moments in week 2.

---

## PHASE 2 — BUILD THE ASSETS (this is ~most of the final quality)

5. **LOCATIONS** (nail these or the video is sloppy — the lighting/style of every shot comes from the location reference):
   - Describe the layout in **words in Claude**, do NOT upload a location image into the image generator (Nano Banana Pro has
     weak spatial awareness → it crams uploaded rooms in, e.g. a room outdoors). Be oddly specific (windows left, hallway
     right w/ 2 doors left / 3 right, L-couch facing TV, small kitchen right wall…).
   - **Batch 4 images.** With a detailed prompt the model is consistent, so if something's off the PROMPT is the bug — fix it,
     don't just re-roll. Don't read the long prompts; look at the 4 and tell Claude the parts to change.
   - **Fight plasticky (Nano Banana Pro's default):** add "light atmospheric haze" + "film grain" + "crush the blacks to add
     shadow depth" + specific lighting keywords. Age it: revealed ceiling pipes, darker outside, grungier, lore props.
   - **Editing loses detail each pass** → prefer "edit the PREVIOUS image again" (re-edit from the clean source). When edits
     keep drifting the layout, **STOP editing and REGENERATE FROM SCRATCH** with the full detailed prompt + NO reference — locks a clean version.
   - **Two views:** after the front wide angle, generate the REVERSE angle (view from the hallway in), then COMBINE both into
     ONE 16:9 reference image → maximum spatial context so the video model holds geography as the camera moves. Daytime = upload the locked room, say "it's daytime."
6. **PROPS** get clean reference sheets. Photo-wall / multi-image props: generate each element INDIVIDUALLY and STITCH in
   Photoshop — a whole wall in one gen DRIFTS faces (unacceptable for a real film). For a Polaroid, give Claude the face
   sheets but have it describe only the CLOTHING (over-describing appearance makes it invent new characters even with sheets attached).

---

## PHASE 3 — TEAM / ORGANIZATION (for multi-person or multi-scene work)

7. One **project per scene-group**. Share the **FOLDER** (not downloaded images) so everyone gets all assets + inputs +
   prompts + which tool made each — anyone can go back and tweak. Comment on individual generations. Keep the canonical
   style prefix + asset canvas shared so N people stay consistent.

---

## PHASE 4 — GENERATE THE VIDEO (Seedance 2.0 / Kling / Higgsfield)

8. Upload assets ONCE; the shot list tags them in the SAME sequence every shot (image1 = hero, image2 = location) — never
   re-upload. **Reference ORDER matters:** the reference described first in the prompt goes first.
9. Aspect: **21:9** for a big-screen/cinema film (else 16:9 / 9:16 for social).
10. **Batch 8 videos → SKIM, don't watch each fully.** Judge composition first; only watch fully if the composition is right.
    If several share the SAME mistake, STOP and fix the prompt (don't keep batching). Reality: ~1/64 usable, ~1/100 makes the cut.
11. **Spatial-awareness fixes (Seedance's weakness):** don't have a character ENTER from outside into a room (it invents
    doors / teleports him) — put the CAMERA INSIDE facing inward; push the camera FURTHER IN to kill the "too many doors" artifact.
12. **Spell out camera + shot size per beat** ("push in from medium → closeup; door opens; then super-low-angle closeup on his
    boots as he steps in"). Beats that don't land → make the shot LONGER + have the action actually complete.
13. **Failure-mode handles go INSIDE the prompt** ("do not drift the Polaroid"), not as side-notes.
14. **Engine adapter — Seedance:** it historically preferred **Chinese** prompts AND had a hard **3,000-char cap**; Chinese
    packs ~1–2 chars/word vs 5–10 in English → more information within the budget. (Verify current caps before relying on this.)

---

## PHASE 5 — EDIT + QA (assembly is 50% of the shot)

15. **Edit as you go** — new timeline + reference music from the start, so you know what's missing + how shots cut + the final feel.
16. **Edit pass** (from the skills): cut-on-action, speed-ramp the peak beat, keeper-phase harvest (best 1–2s of many takes),
    match/J cuts, frame-by-frame FPS check.
17. **QA gate:** run the render through the attention score (TribeV2 — see pipeline/tool-guides/tribev2.md) → fix the dipped seconds →
    Claude-watch the flagged frames. Verify from the viewer's seat (render a frame, LOOK) before "done."

---

## THE MINDSET (slop vs cinema)
- **Slop:** plasticky texture, wrong/extra doors, characters standing weirdly mid-room, faces drifting, plopped-in lighting.
- **Cinema:** real texture, moody CONTROLLED practical light, correct geography, intentional camera, one job per shot.
- **Scrapping is normal** (they burned ~100k credits on a 2.5-min scene then scrapped it on a script change — "that's how you get cinema").
- **Every shot needs director-level approval.** ~1/100 generations makes the final film. Iteration IS the skill.

---
_Automation map: PHASE 0.3 + PHASE 1 → `generate-shot-pack.cjs` (`--character` / default / `--frames` / `--pic`), all via your own LLM
or paste-mode. PHASES 2/4/5 are the human iteration + QA discipline the generator can't do for you. Compounds with
`pipeline/skills/` (atomized craft) + `MONTAGE-CRAFT.md` (edit rules) + `playbooks/` (prompt structures)._
