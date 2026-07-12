# 🎚️ MONTAGE-CRAFT — how we edit like a pro (adopted from OpenMontage, 2026-06-24)

Distilled, actionable editing craft for EVERY video the studio makes. These are **techniques + values** (not copied code — OpenMontage ships no license, so we adopt the methods/numbers, which aren't copyrightable, and re-implement in our own code). Apply these in `STUDIO.md`'s assemble + QA steps. Read this before cutting anything.

---

## 1. HOOK & RETENTION (short-form 9:16) — the make-or-break
- **Decision happens in ~1.7s.** Frame 1 MUST have: text on screen by **0.5s**, voice starting immediately, and motion. Never open on a static/silent beat.
- **Visual change every 1–3s.** A pattern-interrupt every **2–4s** (58% retention vs 41% static). No static hold > 3s.
- **Cuts per minute: 20–40** for short-form.
- 3s-retention → reach multiplier: `<60% = 1.0×` · `60–70% = 1.6×` · `70–85% = 2.2×` · `85%+ = 2.8×`. Targets: 3s→70%+, 15s→60%+, 30s→50%+.
- **End on CTA + LOOP** — the last beat connects back to the first so it replays seamlessly.

## 2. CUT RHYTHM (the breathing) — kills the "slideshow" feel
- **Never use the same shot length 3× in a row.** Vary it.
- Cinematic breathing pattern: `8s → 5s → 3s → 2s → 10s` (long, settle, quicken, hit, release).
- Hold length by tone (base): `urgent 1.2s · wry 2.0s · dreamlike 3.0s · reverent 3.5s · elegiac 4.0s`. **Hero shots get the longest hold; trim every other clip to its single best ~3s moment.**
- Total runtime must land within **±10%** of the target; compress non-hero holds first, never cut heroes short.
- Cut on **word boundaries**; trim dead air >1.5s down to ~0.5s; keep natural breaths 0.3–0.8s.

## 3. TRANSITIONS — restraint reads as "professional"
- **Cap the vocabulary at 4 distinct transition types** for the whole piece.
- **BANNED by default** (they read as cheap social edits): wipes, push/slide, zoom blur, RGB split, light leaks, glitch.
- Meaning: **hard cut** = wake up / disruption · **crossfade** = this continues · **slow dissolve** = drift with me.
- Durations: hard cut 0ms · crossfade 0.5–1.5s (fast <60s piece → **0.3–0.5s**) · fade-to-black 0.5–1.0s.
- Use **L-cuts / J-cuts** (carry audio 0.5–1.5s across the cut) on the 3–4 hardest transitions — documentary montages with L-cuts feel ~50% more coherent.
- Adjacent diversity: no two adjacent cuts share BOTH subject and scale; break the color pattern at least every 4 cuts.

## 4. CAPTIONS — word-by-word karaoke (biggest visible upgrade over flat text)
- 42px+ bold sans, **≤30 char/line, ≤2 lines**, ~15 char/s read speed, cue end **+200ms** past the last word.
- **Word-by-word highlight**: active word gets a highlight color + glow; past words dim; one caption group on screen at a time; **hard-kill each group at its end** (no lingering text — deterministic).
- Feed **Whisper word-level timestamps** into the caption renderer (Remotion `CaptionOverlay` pattern, or an ASS `force_style` block for the ffmpeg route). Default highlight `#22D3EE`.

## 5. AUDIO — the invisible 50% of "quality"
- **Voiceover processing chain** (apply after ElevenLabs/VoxCPM returns the wav): `highpass=f=80` → cut ~500Hz mud → boost 2–5kHz (+2–3dB presence) → de-ess 6–8kHz → `acompressor` ~3:1 (attack 1–5ms, release 10–20ms) → `alimiter` at **-1.5 dBTP** → **loudnorm to -14 LUFS**. Dramatic perceived-quality lift, ~free.
- **Music ducking**: bed sits **18–20 dB below** dialogue (`volume 0.08–0.15`, fadeIn 2s, fadeOut 3s); duck under VO via `sidechaincompress` (threshold ≈0.02, ratio ~9, attack 200ms, release 500ms).
- **Drop the music entirely for ~2–3s at the emotional peak / key reveal.** Use silence once, use it hard. Music tails out under the last 3–5s.

## 6. COLOR / LOOK — learn the palette, don't guess
- Grade order: normalize → color-temp → color-balance → curves → eq → (optional LUT). Intensity **0.6–0.85**, **±0.05 per adjustment**; never push saturation >1.2 on people; keep skin tone ~123° on the vectorscope.
- Cheap cinematic look (no LUT): CSS/shader `contrast(1.06) saturate(0.88) brightness(0.92)` + radial vignette (`transparent 52% → rgba(0,0,0,0.52)`) + faint scanline at `0.12×intensity`.
- Cinematic framing: 2.39:1 letterbox = **138px bars** top/bottom on 1080p.

## 7. SCENE-PLAN — the 5-Aspect Checklist (fixes flat comps; use for Unreal + Hyperframes prompts)
Every shot spec must state all five (write "N/A" — never silently omit): **Subject · Subject Motion · Scene · Spatial Framing · Camera.**
Draw from a controlled vocabulary: shot_size, `camera_movement` (push/pull/orbit/crane/handheld/static/…), `lens_mm [14,24,35,50,85,135,200]`, lighting_key, depth_of_field. Overlays (text/graphics) are a **separate layer** — never describe an overlay as "in the foreground" of the 3D scene.
Explainer rule: **verbatim on-screen text MUST be a real text layer, never AI-generated** (generators hallucinate text).

## 8. HYPERFRAMES MOTION GUARDRAILS (our Three.js engine = the "detail law", restated)
- **3 layers minimum per scene.** The background is NOT empty — radial glows, oversized faded type, depth dust. (= "many small SHARP glowing elements layered in DEPTH".)
- **Don't reuse the same easing on every tween.** The slowest scene should be ~3× slower than the fastest.
- Don't start motion at t=0 — offset 0.1–0.3s; keep total stagger under ~500ms.
- Subtle audio-reactivity only: caption `scale = 1 + peakBass*0.06`, glow from treble — 3–6% variation max.
- **"Instant AI-design tells" to avoid:** default fonts (Inter/Poppins/Syne for hero type), weight contrast 400-vs-700 (use **300 vs 900**), perfectly even spacing/timing.

## 9. REFERENCE REPLICATION (the `./references/` drop-zone)
- For each reference shot, classify **motion_type**: `motion_clip` (real video motion) vs `animated_still` (Ken-Burns/crossfade on stills). **Never guess** — decide it explicitly; it changes how we rebuild the shot.
- Emit a structured brief per shot: motion_type + palette (exact hexes) + the 5 aspects. Replicate from the brief.
- Prefer fewer-but-longer beats: a 60s video = ~6×10s, not 12×5s. Consolidate adjacent similar scenes.

---

## QA GATE (run before calling a video done)
- Frame 1: text by 0.5s + motion + voice? · Visual change every 1–3s? · Loop closes?
- No shot length repeated 3× in a row? · ≤4 transition types, zero banned effects?
- Captions word-synced, ≤2 lines, hard-killed at end?
- VO run through the processing chain + -14 LUFS? · Music ducked + a held silence at the peak?
- Total runtime within ±10% of target?
- Then: **TribeV2 score** → fix the dipped seconds → re-score (quantitative), and **Claude-watch** the flagged frames (qualitative why).

---

## 🎥 10. Camera & motion — nothing is ever truly static
- **Always-moving camera.** Even a "static" shot gets a slow push-in (2–5% over the shot) or a faint drift; held shots get a subtle **punch-in** to keep energy. Dead-static reads as a screenshot.
- **Ease everything; never linear.** Entrances `easeOutExpo`/`easeOutCubic`; moves `easeInOut`; UI/text pops get a slight **overshoot-and-settle** (back-ease 1.0→1.05→1.0). **Linear motion is the #1 "AI/template" tell.**
- **Splines, not constant velocity.** Animate position/rotation on Bézier curves — accelerate out of rest, **decelerate into the stop** (slow-in/slow-out). The camera arrives a few frames before the action, holds, then cut.
- **Motion blur on everything that moves** — camera, objects, AND graphics/text (pro AE editors always enable "Force Motion Blur"; in 3D use ~180° shutter). It's the line between "rendered" and "shot." Don't over-blur.
- **Real camera language:** lead/look room ahead of motion; **rack focus** to redirect the eye; a **dolly-zoom (Vertigo)** for a tension beat; **parallax** via a foreground element; **subtle handheld micro-shake** (±0.3°, low-freq) so it feels operated by a person — drive a touch off the music's low end on hits.
- **Speed ramps:** slow-mo into a beat, snap to real-time on the hit (motion-blurred through the ramp). The single most "expensive-looking" move.

## 👁️ 11. What every pro editor does (the implicit craft — do it by default)
- **Cut on action / on motion** — hide the cut inside a movement (turn, whip, hand cross). **Match cuts** carry shape/motion/color across the cut so it feels inevitable.
- **Eye-trace editing:** place the next shot's subject where the eye already is → cuts feel invisible. Frame cuts on a **blink/whip/flash**.
- **J-cuts & L-cuts everywhere** (audio leads or lags picture 0.3–1.5s) — the biggest "this was professionally edited" lever.
- **Screen direction / 180° + 30° rules** — keep left-right consistency; never cut to a near-identical angle (jump cut) unless intentional.
- **Room tone / ambient bed under everything** — never pure digital silence; a low air/hum bed makes cuts seamless. **Whoosh/transition SFX start 10–20ms BEFORE the visual.** **Sub-bass boom** on big reveals.
- **First & last frame are designed** (open hooks, close resolves + loops). Respect title/action-safe margins.
- **ONE grade across ALL sources** — Unreal, Hyperframes, stock, screen-rec matched to a single LUT so nothing looks pasted in. **Depth cueing:** distant elements get more haze + desaturation.
- **Texture pass:** film grain, gentle halation/bloom on highlights, vignette, a hair of chromatic aberration at the edges. **Master:** −14 LUFS, true-peak −1 dB, light bus "glue" compression.

## 🏆 12. What the top 1% do (mostly unspoken — implement automatically)
- **Snap cuts to the audio transient,** not just the beat — land on the exact kick/snare sample (subframe). Edit to the waveform, not the grid.
- **Silence as a weapon:** kill all audio ~0.5–1s before the payoff, then hit. **A "breath" pause before every reveal.**
- **Invisible transitions:** matched whip-pans between shots, masked/luma wipes hidden in a dark frame or a passing object, morph cuts.
- **Light wrap** in comp (bg light bleeds onto fg edges) so composited elements sit in the scene. **Anamorphic** flavor: 2.39, horizontal blue streak flares, oval bokeh.
- **Micro-life on everything:** slow drift, light flicker, dust motes, a 1-frame light leak at a key beat, faint exposure flicker — the "imperfections" that read as *captured*, not generated.
- **Color script (emotional arc):** the look shifts across the piece (cold/dim → warm/electric) — score the story in color, not just lighting.
- **Kinetic typography with physics:** text has weight, momentum, a settle; never just fades in; tracked to motion + motion-blurred.
- **Supersample:** render above target res, downscale for crispness; render 16-bit/log, grade down for clean highlights.
- **The signature moment:** one bespoke, clever beat (a visual pun, a perfect sound-to-visual sync) that's memorable + rewards a rewatch (feeds the LOOP).

## 🤚 13. The human-touch layer (so it reads as a human made it — the unasked edge)
- **Intentional imperfection:** timing isn't perfectly on-grid (a few ms of human jitter); a slightly off-center frame; a hand-feel to the shake.
- **Specific, tactile sound design** (a unique whoosh, a real UI click, a mechanical clunk) — generic stock SFX read as AI.
- **A CTA that doesn't feel like a CTA** — earned by the story, not bolted on. **An Easter-egg detail** rewarding the rewatch.
- **Restraint > effects:** the top 1% remove more than they add — every element earns its place; when in doubt, cut it. Taste beats plugins.

---

## 🎞️ 14. UNREAL CINEMATIC — render like film, not a game (Sequencer/MRQ/CineCam/post)
*Internet-scavenged from top-1% UE cinematic + virtual-production pros (Epic docs, hyperrender, 80.lv, magnopus, Faucher).*
- **Render via Sequencer + Movie Render Queue, never viewport grabs.** Temporal samples **9–16** (odd: 9/15 evaluate cleanly); **AA override = None** once you exceed 8 samples (TAA caps unique positions at 8). **Engine Warm Up + Render Warm Up frames ON** so Lumen/particles/cloth settle before frame 0 — and **extend Sequencer tracks 1 frame BEFORE** the render range or you get a pop. Output **EXR + Disable Tone Curve** (grade externally). Enable **Game Overrides → Cinematic Quality** instead of hand-listing cvars. Cameras/FX as **Spawnables**.
- **Cine Camera:** **35–50mm** normal, **85–100mm** compressed beauty (longer FL blurs bg without moving the rig). Aperture **f/1.4–2.8** hero DOF; **animate the aperture open as you push in** (real-lens breathing); **Smooth Focus Changes** on. **7–9 diaphragm blades** = round bokeh. **Manual focus distance rigged + tracked** to the subject (never auto). **Super 35** filmback. **Motion Blur Amount 0.5** = the 180° shutter.
- **Movement:** **Camera Rig Rail** (dolly; curve the tangent handles) + **Camera Rig Crane** (jib). Keyframe transforms with **Cubic/User tangents, flattened** for ease-in/out — **never Linear** (robotic). **Perlin-noise CameraShake on EVERY camera** (low-freq = handheld, ≈0 = tripod) — deterministic but organic, *the single biggest cinematic upgrade*; build 3 named shake assets (handheld>steadicam>tripod), tune by eye.
- **Lighting/post:** Lumen **Hit Lighting** reflections + **Virtual Shadow Maps**. **Exponential Height Fog + Volumetric Fog ON**; raise the directional light's **Volumetric Scattering Intensity** for god-rays. **Lock exposure (manual EV)** — no auto-drift between shots. **Filmic/ACES** tonemap; **`r.Tonemapper.Sharpen 2.0`**; restrained CA.
- **The "expensive look":** **FOUR fog levels** (height fog + volumetric `r.VolumetricFog.GridPixelSize 16` + translucent **fog cards** + VDB) = the depth that reads as film. **Emissive multiplied into base color** (props self-glow in shadow); **instance practicals at varied intensity+hue** (kills game-flatness); **edge point-lights** for specular kicks; **subsurface** on skin/wax/foliage.

## 📐 15. MOTION MATH — the AE 0.1% layer, re-implemented in code (Remotion/Three.js/ffmpeg)
*Scavenged from School of Motion, Motion Design School, motionscript, graymachine, Mt. Mograph — ported as MATH, not AE buttons.*
- **Never linear.** Entrances = **ease-OUT** (`1-(1-t)^3` cubic / `1-(1-t)^4` quart-snappier). A→B travel = **ease-in-out** (`t<.5 ? 4t³ : 1-(-2t+2)³/2`). **Asymmetric** (decel longer than accel) is the pro look — bezier `(0.16,1,0.3,1)`. Match the **velocity** being continuous (tune the speed graph), not just the value.
- **OVERSHOOT + SETTLE — the #1 separator.** Damped oscillation, **halving each swing**: for a 100 target → **120 → 90 → 105 → 97.5 → 101.25 → 100**, keys **2–4 frames** apart. Expression/math: **`out = target + v·amp·sin(2π·freq·t)·e^(−decay·t)`** (amp 0.05–0.15, freq ~2, decay ~2; sample velocity just *before* the key → amplitude ∝ arrival speed = physical).
- **Anticipation:** pull back the opposite way **3–6 frames** (~10–15% of travel) before the main move.
- **Follow-through / overlap:** offset related layers **2–4 frames**; trailing parts keep moving after the lead stops. **Frame-delayed clones** (`valueAtTime(time − N·frameDur)`) + falling opacity (50% × offset 2–3f) = a motion trail.
- **Squash & stretch:** preserve volume (X·Y≈const), **5–15%** tasteful (not cartoon).
- **Motion blur is non-negotiable.** 180° shutter → blur length **`velocity·(0.5/fps)`**; **directional** blur along the velocity vector (not Gaussian); 270–360° = dreamy.
- **Kinetic type:** every word's **settle** frame snaps to a beat; scale **0→100% with overshoot** (6–10f in); tracking **−10 → 0**; masked wipe reveal 4–8f, per-letter **1–2f cascade**; type has weight (overshoot + overlap + squash on landing).

## 🔊 16. VO-SYNC & B-ROLL-AS-MEANING — "everything corresponds to the voice" (the core mandate)
*Scavenged from editing/documentary/audio-reactive craft (bitcut, insidetheedit, adobe, premiumbeat, pixflow, soundonsound, BT.1359).*
- **Cut to the TRANSIENT, not the grid** — the acoustic onset (FFT ~46ms window), sample-accurate. **Anticipation cut 1–2 frames BEFORE the beat** (see shot, then hear it land = intentional). **Marker-strength → cut-weight:** kick/bass = whole-shot change; snare/chord = mid; hi-hat = flash. Never trust hand-tapped markers (they run 100–250ms late) — nudge to the waveform.
- **B-ROLL VISUALIZES THE NARRATION.** Mark a locator on **every evocative word in the VO FIRST**, then place the visual there. **"Say it → show it"** — the VO names a thing, that exact frame shows the thing (say "memory" → a memory-bank ignites; "24/7" → a clock/loop spins). The **visual lands a touch BEFORE the word** (perception tolerates audio-lead). **Vertical** (drop on the keyword) × **horizontal** (chain shots so action progresses). Let B-roll breathe a couple sentences before narration re-enters.
- **J/L cuts everywhere** — audio leads or lags picture **0.5–2s** (dialogue), **1–3s** (B-roll ambience). The biggest "professionally edited" lever; hide the seam with a short crossfade/room-tone J-cut.
- **Audio-reactive:** bake audio→keyframes; **bass band → big moves** (scale/camera push), **treble → shimmer/glow**; **EASE the mapping** (raw amplitude is gimmicky); **one band per property**; **3–6% variation** reads intentional.
- **Sound design for sync:** **whoosh LEADS the visual 10–20ms**, fills ~400–500ms peaking AT the cut; **impact/boom ON the hit frame**; **riser peak aligns exactly** with the reveal; **room tone under everything**; **drop music to silence ~1 beat before the key line**, then slam back (silence = the emphasis).
- **Sync budget:** audio may **lead ≤45ms** / **lag ≤125–185ms** and still read synced (20–40ms = noticeable threshold) — **bias hits to audio-leads-slightly.** Sidechain-duck music under VO; pause before the key word; keep the breaths.

## 🎨 17. COLOR & FILM-EMULATION FINISHING — "shot by a human on film" (one grade over ALL sources)
*Scavenged from colorist craft (Cullen Kelly node order, dehancer halation, AgX, EBU R128, schoolofmotion, bartwronski).*
- **Grade order:** prime (exposure+contrast, Luminosity) → **balance** (temp/tint, **linear gamma**) → **saturation** (HSV) → secondaries (windows/qualifiers) → **creative LUT at the TIMELINE level**. Park **skin on the ~123°/I vectorscope line** at **20–50% sat** (never >1.2 on people). **Teal-orange** = complementary split (subject pops). **COLOR SCRIPT** = the look shifts across the piece (**cold/desat → warm/electric**) — score the story in color.
- **Film emulation:** **AgX** (or ACES) tonemap, grade in **32-bit float**, transform last. **Halation:** isolate highlights (luma **0.6–0.8**), blur, tint **red→orange**, screen back — subtle, brightest sources only. **Grain:** per-frame animated, **3–8% opacity**, weighted in **mids** (smaller stock = bigger grain). **Gate weave:** **0.1–0.3px** low-freq positional drift. **Diffusion (Black Pro-Mist):** bloom only the top highlights.
- **Lens character:** **CA** radial R/B offset **1–3px** (0 at center → edges); **vignette ~0.5** radial; subtle barrel; **anamorphic** = horizontal blue streak flare + **2:1 oval bokeh**.
- **Human-imperfection (too clean = CGI):** **1-frame light leaks**, **exposure flicker** (±small luma), **subtle handheld drift**, **intentional off-center framing**, and **grain over the WHOLE comp** (unifies CG + plate). Know when to stop polishing.
- **Mastering:** **−14 LUFS** integrated, **true-peak −1 dBTP**; render **16-bit/log, grade down**; **supersample then downscale** (2×→1×) for crispness + cheap AA.

---

*Sources: §1–9 + QA adopted from OpenMontage craft/values (2026-06-24). §10–13 (camera/motion, pro + top-1% + human-touch) = the studio's own professional-editing knowledge layer, added 2026-06-24. §14–17 (Unreal cinematic, motion math, VO-sync/B-roll-as-meaning, color/film-emulation) = internet-scavenged 2026-06-24 from top-1%/0.1% Unreal + After-Effects + editing + colorist sources, ported as concrete math/values/cvars — the durable craft so EVERY video reads as a human master made it. Reference pieces/assets to preview: `ARSENAL-REFERENCES.md`.*
