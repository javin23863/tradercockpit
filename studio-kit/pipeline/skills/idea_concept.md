# 🎬 SKILL — Idea & Concept
_the core premise, scene-by-scene plan, why each shot earns its place. Apply EVERY video. Rules compound as we study more references._

## from: Seedance 4K hyperreal AI short film breakdown (Adil) (2026-07-05T17:43:42.639Z)
- Break every scene into three ingredients — characters, location, props — and list exactly which assets you need before generating anything.
- Make every shot a hook: if the shot wouldn't stop you from scrolling ("nobody would watch that, even myself"), redesign it before rendering.
- Anchor disparate visual styles (fantasy, wildlife, action) to one simple narrative spine — e.g., a character glued to a screen while a recurring real-world interruption escalates — so the montage reads as one film.
- When you have a specific vision, build dedicated assets first instead of winging a single prompt — assets are what lock control over the result.
- Deliberately design shots that stress the model (wide vistas, crowds, tiny far-away details) — those are the shots that prove 4K over 1080p.

## from: AI commercial/ad workflow (Adil) (2026-07-05T17:53:13.980Z)
- Plan in three fixed stages before generating a single clip: (1) build, test, and lock assets (product, characters, locations, props), (2) turn the script into a connected shot list via a Claude skill, (3) generate scenes in the video model.
- Write the full script before touching a generator — one beat per scene, and every shot must earn its place.
- Get organized before generating anything: you're about to make a ton of files, and a scattered library costs half a day of digging mid-edit — name and file assets from the start.
- Treat the workflow as product-agnostic: swap any product into the same system; the real power is in how you describe each shot, not what's in it.
- Budget for iteration up front — the finished ad is the best few seconds out of ~100 tries cut together; iteration IS the skill, not a fallback.

## from: Hell Grind AI feature film — 28 pro tips (Higgsfield) (2026-07-05T17:56:56.909Z)
- Script action scenes beat by beat before generating: each cut defines who is in it, where they stand, which weapon/prop they hold, and the choreography — ask Claude to choreograph if stuck.
- Give every shot ONE main idea, ONE main action, and ONE camera strategy — enforce this density limit in your system prompt so no generation tries to do two things.
- Prefer a single continuous shot when you need maximum control: one camera move + character action can define what happens each second.
- Cut ruthlessly, even usable material: the team trimmed 110 min to 90 by deleting generations that worked but didn't earn their place — keep only shots with a reason to exist.
- Don't grind a stuck scene in order: drop a placeholder on the timeline, generate the next scenes, and return with fresh eyes — production order doesn't have to match scene order.

## from: Reference clips — ultra-realism prompt structures (2026-07-05T18:02:10.689Z)
- Write a one-line north-star goal before any prompt (e.g., "Authentic [X] life captured like a forgotten home video — candid, imperfect, realistic, warm, deeply believable") and use it to filter every shot decision.
- Choose your realism strategy up front: Strategy A (imperfect UGC) for relatable/testimonial/"caught-on-camera"; Strategy B (start+end-frame I2V) for a single impossible hero motion you can pin with two images.
- Build a timestamped beat breakdown (00:00–00:02, 00:02–00:04 …) where each beat is one specific micro-action ("subject sits on a low wall adjusting ponytail, breeze moves loose strands, smiles naturally").
- Earn each shot's place: every beat must advance the slice-of-life feeling OR deliver the one impossible feat — cut anything that is merely "nice footage."

## from: Hell Grind Ep2 — full unedited AI-film process (Adil): style-prefix, 44-iteration locations, diagnosis loop, team collab (2026-07-05T19:07:32.443Z)
- Start from a finished written script and work only a couple of scenes at a time — a little text turns into a lot of production time.
- Codify all accumulated craft knowledge into a reusable custom Claude skill (.zip), invoke it once per session, and let it run three phases: split scenes into ~15-second shots with prompts tailored to the target video model, request the assets it needs, then map prompts onto scenes.
- Rely on the assistant's persistent chat context — invoke the skill once at the start instead of re-explaining per shot.
- Plan two passes: week 1 generate the whole runtime, week 2 refine the key moments.
- Gate every clip on explicit director's approval — no approval, no place in the film.
