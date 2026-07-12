# 🎬 SKILL — Local & Cloud Generation
_two lanes to make every shot: cloud AI-gen for photoreal, local $0 engines for motion-graphics + kinetic video. Pick per shot. Apply EVERY video._

## The two lanes (decide per shot, not per project)
- **Cloud AI-gen** — when the shot needs photoreal footage, a real-looking person/product, or a look you can't hand-code (skin, fabric, weather, a set). Costs credits, runs on a service.
- **Local $0 generation** — when the shot is abstract motion-graphics, kinetic text/captions, a data-driven overlay, or a stylized 3D backdrop. Runs on your machine, no API, no per-clip fee, total control.
- Most finished videos MIX both: photoreal hero shots from the cloud, titles/captions/MG backdrops/transitions from the local engines, assembled with ffmpeg.

## Lane 1 — Cloud AI-gen (images, cinematic frames, video)
- Driver: `pipeline/generators/generate-shot-pack.cjs` — takes a minimal brief and fills every craft gap (lens, 60/30/10 light, practical-light-only, character consistency, engine-specific fixes) into ready-to-paste prompts for Higgsfield / Seedance / Kling.
- Text-to-video shot list (default mode):
  `node generate-shot-pack.cjs --concept="..." --shots=6 --aspect=9:16 --realism=hero`
- First-frame / last-frame image-to-video (most controllable motion): add `--frames`.
- Standalone pictures (product shots, character/reference sheets): add `--pic`.
- Reusable character you keep consistent across a whole video: add `--character` to build a character bible first, then reference it in every shot.
- Solve variants and state changes in image-land (cheap), not video-land (expensive) — build the extra sheet instead of burning video generations.

## Lane 2 — Local $0 generation (no API, runs on your machine)
### Hyperframes — cinematic motion-graphics (Three.js)
- Use for: glowing abstract "AI-looking" backdrops (neural nets, particles, energy cores), animated MG loops, and still cinematic frames — all rendered locally.
- Lives at `pipeline/generators/html3d-render.cjs`; the scenes are `pipeline/generators/compositions/*.html`.
- Render a 6s vertical clip: `node html3d-render.cjs --html compositions/itm-3-ignite.html --out out.mp4 --fps 30 --dur 6 --w 1080 --h 1920` (run from `pipeline/generators/`).
- **Eyeball a still first**: `node html3d-render.cjs --html compositions/itm-3-ignite.html --still 90 --stillout f.png` → open `f.png`, confirm the look, THEN commit to the full render.
- Character animation: the scenes can load a rigged GLB with BVH / FBX / Lottie motion (see `compositions/models/`), so a character can walk/gesture in-scene with zero cloud cost.

### Remotion — kinetic-typography, captions, data-driven video (React)
- Use for: headlines that snap/slide on the beat, voiceover-synced captions, counters/charts/stats that animate from real numbers — the pixel-perfect "words and numbers" half of video.
- Lives at `pipeline/generators/remotion/`. Once per machine: `cd pipeline/generators/remotion && npm install`.
- Preview + scrub live: `npx remotion studio`.
- Render a composition (the `id` comes from `src/Root.tsx`): `npx remotion render CostReel out.mp4`, or feed data: `npx remotion render ProductReel out.mp4 --props='{"productName":"Your Product","price":"$XX"}'`.
- Every `src/*Reel.tsx` and `src/scenes/*` is a fill-in-the-blanks template; the reusable blocks are in `src/components/` (KineticCaptions, FitText, AuroraShader).

## Assembly
- Stitch the lanes together with **ffmpeg**: lay cloud footage as B-roll under a Remotion caption pass, drop a Hyperframes MG backdrop behind a title, cut between beats, and mux the voiceover. One timeline, two sources of pixels.

## Pick-fast rules
- Photoreal human/product/place → **Cloud (Lane 1)**.
- Abstract/energy/tech backdrop or animated logo moment → **Hyperframes**.
- Text, captions, counters, or a hundred data-swapped variations → **Remotion**.
- In-scene rigged character motion for $0 → **Hyperframes (GLB + BVH/FBX/Lottie)**.
- Always render ONE still/preview before a full render — a flaw in the frame compounds across every frame of the clip.
