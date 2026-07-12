# 🎬 SKILL — Consistency & Continuity
_lock characters/props/geography across shots — sheets, schematic maps, wet/dry variants, single-face, anchors. Apply EVERY video. Rules compound as we study more references._

## from: AI commercial/ad workflow (Adil) (2026-07-05T17:53:13.982Z)
- Lock every winning asset to the top of the canvas and save it as a named ELEMENT — use the exact same names in Claude, so pasting a prompt auto-attaches all required images.
- Change ONE variable at a time when testing (same prompt, swap only the hero OR the location) so you can actually see what's making the difference.
- Give the model one face per character: erase duplicates from every sheet so there's a single anchor to lock onto.
- Build deliberate variant sheets for any transformation (hero dry / hero_wet) and tell Claude exactly which cuts use which.
- Use the map/schematic hack for geography — text can't pin a location: build a schematic in GPT image 2.0 marking where things sit and how big, then have Claude rewrite the prompt around it; it holds take after take and skips the 20-generation lottery.
- Anchor the hero to a fixed object in frame (a tree on the left) so spatial geography stays consistent across generations.
- Match cut boundaries explicitly: the opening action of a scene should replicate the closing action of the previous one — same hand, same motion.

## from: Hell Grind AI feature film — 28 pro tips (Higgsfield) (2026-07-05T17:56:56.910Z)
- Use a FRAME COORDINATE SYSTEM: split the location into X/Y axes and give the model exact placements ("20% on X, 30% on Y, place the character here") — it obeys.
- Draw the scene before you prompt it: ask Claude for a top-down MAP, iterate it ("move him here, her there"), and paste the resulting positioning prefix into your prompt.
- Anchor every location with a fixed object so positional references land identically across every cut.
- Open dialogue scenes with an establishing wide/medium shot so the model sees all characters and the location; every later cut then keeps positions and eyelines correct.
- Generate related cuts (e.g. four reactions in the same location) inside ONE multi-shot generation to lock lighting and positioning across them, then cut out the keeper phases.
- Lock each character/prop state as its own named asset and pull only from the canvas — long-film continuity (injuries, clothing, transformations) holds only if the right state is grabbed every time.
- When characters teleport between shots (positioning drift), re-anchor with coordinates/anchors, verify the correct canvas asset was attached, then diff before/after to confirm the fix landed.

## from: Reference clips — ultra-realism prompt structures (2026-07-05T18:02:10.690Z)
- Lock identity by repeating the character description + the "Maintain consistent identity…" line in every shot prompt that features the same person.
- For I2V continuity, force convergence: end the prompt with "lands exactly in the final position of the end frame" so the generated motion snaps to your anchor.
- Place environmental anchors (palm trees at frame edges, parking-lot position, wall the subject sits on) that appear identically in both the start and end frames so geography is locked across the motion.

## from: Hell Grind Ep2 — full unedited AI-film process (Adil): style-prefix, 44-iteration locations, diagnosis loop, team collab (2026-07-05T19:07:32.446Z)
- Define ONE style prefix block — STYLE, LIGHTING, COLOR, COMPOSITION, AUDIO — and glue it to every shot; it's the single most important consistency tool when many people generate the same film.
- Paste the style prefix into the assistant with the script so every generated prompt inherits the look automatically.
- Upload assets once and keep the reference sequence fixed across the whole shot list (image1 = character, image2 = location) so nothing is re-uploaded or re-tagged.
- Feed the video model a combined two-view location reference so geography holds when the camera moves through the scene.
- Organize collaboration as one project per scene-group and SHARE THE FOLDER (with permissions) instead of sending files — sharing passes all assets, inputs, prompts, and which tool made each image, so anyone can trace and tweak.
- Use adult/teen character sheet variants deliberately so time jumps stay on-model instead of drifting.
