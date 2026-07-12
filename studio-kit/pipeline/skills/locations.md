# 🎬 SKILL — Locations
_the location image is ~most of the video quality; angle + engine choice. Apply EVERY video. Rules compound as we study more references._

## from: Seedance 4K hyperreal AI short film breakdown (Adil) (2026-07-05T17:43:42.641Z)
- Treat the location image as the single biggest determinant of final video quality — examine it hard and regenerate if anything looks off.
- Hunt for AI artifacts before approving: levitating objects, items attached to nothing, misplaced props, lighting that's too bright.
- Request 3/4 angles so more of the room is visible and the video model gets real depth perception — it renders without breaking.
- Use the engine built for cinematic stills (Soul Cinema) for locations — it puts out the highest-quality images.
- Match the location's atmosphere to the story beat (e.g., "messy teenager's room vibe") — atmosphere carries as much as geometry.
- Skip building a location asset for one-off shots — current 4K video models build convincing single-use environments on their own.
- Reuse a saved location element across scenes — a location built for one scene serves later scenes for free.

## from: AI commercial/ad workflow (Adil) (2026-07-05T17:53:13.982Z)
- Treat the location as the make-or-break quality lever: if it reads fake or plasticky, no prompting will save the video.
- Aim the default look at bright, clean, high-budget commercial; use a simple prompt and lots of batches, keeping multiple options.
- Generate locations at a 3/4 angle, not flat head-on — it gives the room depth for the video model to hold onto when the camera moves, and the win rate jumps.
- A/B test heroes-in-locations side by side before locking: it becomes obvious which location keeps the face lit and which sinks it into shadow.
- Edit the locked location surgically in GPT image 2.0 — "clear the island, add a stove on the left, replace the TV with a door, keep everything else the same."

## from: Hell Grind AI feature film — 28 pro tips (Higgsfield) (2026-07-05T17:56:56.909Z)
- NEVER generate a location head-on/front — the model struggles with depth. Use a 3/4 angle (camera tilted, wider view) or a corner-of-the-ceiling CCTV angle; both work.
- Put an ANCHOR object in every location (a tree, a stack of books) so you can place characters and camera precisely relative to it ("place Roco to the left of the tree," "camera hovering next to the books").
- If the model keeps grabbing the wrong side of a location, split it into separate VIEWS: generate front and back images, attach both, and assign per cut ("cut 1 uses this view, cut 2 uses this view").
- Store every location, in every needed state, on the shared canvas.

## from: Reference clips — ultra-realism prompt structures (2026-07-05T18:02:10.690Z)
- Pack location prompts with specific real-world texture — narrow alleys, laundry lines, utility poles, moving tree shadows, palm trees framing the edges — because the location image carries most of the perceived video quality.
- Add an explicit exclusion list to every location prompt: "No stores, advertisements, cafés, crowds, or commercial activity" (adapt the list to kill whatever doesn't belong in your scene).
- Choose the location strategy to match content: residential/neighborhood grain for UGC authenticity; open environmental framing (parking lot, sky) for hero impossible shots.

## from: Hell Grind Ep2 — full unedited AI-film process (Adil): style-prefix, 44-iteration locations, diagnosis loop, team collab (2026-07-05T19:07:32.445Z)
- Treat the location image as most of the final video quality — budget serious iteration (44 tries for one apartment, ~20 more for its reverse angle).
- Describe the location in TEXT via the assistant; do NOT feed location photos into the image generator — poor spatial awareness makes it cram references together (a room ends up outdoors).
- Write an oddly-detailed spatial layout in words: windows left, hallway right with 2 doors left / 3 doors right, kitchen along the right wall, L-shaped couch facing the TV.
- Age the space with concrete cues — revealed ceiling pipes, darker outside, grungier surfaces — plus lore props that imply the inhabitants (skaters → a skateboard against the wall).
- After locking the front wide angle, generate a reverse angle, then combine both views into ONE 16:9 reference image so the video model gets maximum spatial context when the camera moves.
- For a daytime version, upload the locked room image and just say "it's daytime" — don't rebuild.
