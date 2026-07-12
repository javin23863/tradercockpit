# 🎚️ Pro Editing Craft — make every video look professionally cut

The difference between "AI slop" and "this looks edited by a pro" is a handful of concrete rules. Apply these on every video. They're battle-tested values, not vibes.

---

## 1. Hook & retention (short-form 9:16)
- The viewer decides in **~1.7 seconds.** Frame 1 must have **text on screen by 0.5s**, voice starting immediately, and motion. Never open on a static/silent beat.
- **Visual change every 1–3s;** a pattern-interrupt every **2–4s** (≈58% retention vs 41% for static).
- **Cuts per minute: 20–40.** No static hold longer than 3s.
- **End on a CTA + LOOP** — the last beat connects back to the first so it replays seamlessly.

## 2. Cut rhythm (kills the "slideshow" feel)
- **Never use the same shot length 3× in a row.** Vary it.
- Cinematic breathing: `8s → 5s → 3s → 2s → 10s` (long, settle, quicken, hit, release).
- Hold by tone (base): `urgent 1.2s · wry 2.0s · dreamlike 3.0s · reverent 3.5s · elegiac 4.0s`. **Hero shots hold longest; trim every other clip to its single best ~3s moment.**
- Keep total runtime within **±10%** of target. Cut on **word boundaries**; trim dead air >1.5s to ~0.5s.

## 3. Transitions (restraint reads as professional)
- **Cap the vocabulary at 4 transition types** for the whole piece.
- **Banned by default** (they read cheap): wipes, push/slide, zoom blur, RGB split, light leaks, glitch.
- Meaning: hard cut = disruption · crossfade = this continues · slow dissolve = drift with me.
- Durations: hard cut 0ms · crossfade 0.5–1.5s (fast <60s piece → 0.3–0.5s) · fade-to-black 0.5–1.0s.
- Use **J-cuts / L-cuts** (carry audio 0.5–1.5s across a cut) on the 3–4 hardest transitions — montages with L-cuts feel ~50% more coherent.

## 4. Captions — word-by-word (the biggest visible upgrade)
- 42px+ bold sans, **≤30 char/line, ≤2 lines,** cue ends **+200ms** past the last word.
- **Word-by-word highlight:** active word gets a color + glow; past words dim; one group on screen at a time; hard-kill each group at its end (no lingering text).
- Time captions to **word-level speech timestamps** (any speech-to-text with word timing).

## 5. Audio — the invisible 50% of quality
- **Voiceover processing chain:** high-pass at 80Hz → cut ~500Hz mud → boost 2–5kHz (+2–3dB presence) → de-ess 6–8kHz → compress ~3:1 → limit at −1.5 dBTP → normalize to **−14 LUFS.** Dramatic perceived-quality lift.
- **Music ducking:** bed sits **18–20 dB below** the voice; duck under the VO automatically (sidechain).
- **Drop the music entirely for ~2–3s at the emotional peak.** Use silence once, use it hard. Tail music out under the last 3–5s.

## 6. Color & look
- Grade order: normalize → temp → balance → curves → eq → (optional LUT). Intensity **0.6–0.85,** ±0.05 per adjustment; never push saturation >1.2 on people.
- Cheap cinematic look (no LUT): `contrast 1.06, saturate 0.88, brightness 0.92` + a soft radial vignette + faint scanlines.
- Cinematic framing: 2.39:1 letterbox = ~138px bars top/bottom on 1080p.

## 7. Scene planning — the 5-aspect checklist (fixes flat shots)
Every shot spec states all five (write "N/A," never silently omit): **Subject · Subject Motion · Scene · Spatial Framing · Camera.** Pull from a fixed vocabulary (shot size, camera move, lens mm `[14,24,35,50,85,135,200]`, lighting key, depth of field). On-screen verbatim text is always a real text layer — never AI-generated (generators hallucinate letters).

## 8. Motion-graphics depth (why most AI MG looks flat)
- **3 layers minimum per scene.** The background is never empty — radial glows, oversized faded type, depth dust. Detail = **many small, sharp, glowing elements layered in depth,** not a few big soft blobs.
- **Don't reuse the same easing on every move.** The slowest scene should be ~3× slower than the fastest. Offset motion 0.1–0.3s off the start.
- "Instant AI-design tells" to avoid: default fonts for hero type, 400-vs-700 weight contrast (use **300 vs 900**), perfectly even spacing/timing.

---

## ✅ The QA gate (run before calling a video done)
- Frame 1 has text by 0.5s + motion + voice? Visual change every 1–3s? Loop closes?
- No shot length repeated 3× in a row? ≤4 transition types, zero banned effects?
- Captions word-synced, ≤2 lines, hard-killed at end?
- Voice run through the chain + −14 LUFS? Music ducked + a held silence at the peak?
- Total runtime within ±10% of target?
- Score it (attention model) → fix the dipped seconds → watch the flagged frames → re-score.

*These are universal editing principles — use them with any toolset.*
