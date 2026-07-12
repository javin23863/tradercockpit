# 🎬 Reference playbook — ULTRA-REALISM prompt structures (from reference clips)

Learned by reading frames of reference clips (including a bookmarked prompt).
Two proven realism strategies + the polish stack. These are gold — reuse the STRUCTURE, swap the content.

## Strategy A — "believable home video" ultra-realism (imperfection = realism)
The counterintuitive key: to make AI video read as REAL, **add camera FLAWS + negative constraints** (the opposite of "cinematic 4K"). Verbatim structure from the reference (Korean-neighborhood UGC):

- **Main subject** — exhaustive: age, exact clothing, hair, "realistic skin texture, minimal makeup", personality, and **"Maintain consistent identity, clothing, hairstyle, and appearance throughout the entire video."**
- **Location** — specific real-world detail (narrow alleys, laundry lines, utility poles, moving tree shadows) + **exclusions**: "No stores, advertisements, cafés, crowds, or commercial activity."
- **Visual Style** — "Ultra-realistic documentary realism. Genuine candid behavior. Natural body language. Unscripted slice-of-life feeling. Strong environmental authenticity."
- **Camera Style (the realism engine)** — "Early-2000s consumer DV camcorder aesthetic. Heavy handheld shake, imperfect framing, frequent autofocus hunting, lens breathing, exposure pumping when moving between sun and shade, occasional motion blur, subtle rolling shutter, mild digital compression artifacts, faded colors, soft contrast, slight sensor noise. **No stabilization. No cinematic camera moves. No modern color grading.**"
- **Timestamped beat breakdown** — 00:00–00:02, 00:02–00:04 … each a specific micro-action ("she sits on a low wall adjusting her ponytail, a light breeze moves loose strands, she smiles naturally while the camera struggles to hold focus").
- **Audio** — "Natural ambient sound only — morning birds, distant motorcycles, light wind, leaves rustling… **No music. No sound design. No narration.**"
- **Goal** — one line north star: "Authentic Korean neighborhood life captured like a forgotten home video from the early 2000s — candid, imperfect, realistic, warm, deeply believable."

**Rule:** imperfection sells realism. List the specific artifacts you WANT (shake, autofocus hunting, lens breathing, exposure pumping, rolling shutter, compression, sensor noise) and the polish you DON'T (no stabilization, no cinematic moves, no color grading, no music). A timestamped beat list + a one-line goal frame the whole thing.

## Strategy B — start-frame + end-frame image-to-video (the "impossible shot")
From the G-Wagon-falls-from-sky POV (Seedance 2.0 image-to-video): generate a **START FRAME** and an **END FRAME** image, then the video prompt describes the **motion BETWEEN them**. Verbatim video prompt:
> "UGC iPhone POV video. The man is filming the sky with his phone — arms stretched up, the phone screen showing a small dark car-shaped dot high above against the cloudy sky, palm trees framing the edges. The car is falling from the sky toward the ground, growing larger and larger in real space as it falls, and at the same time growing larger and larger inside the phone screen as the camera tracks it. The man's arms gradually lower as he follows the falling car down, the phone tilting from pointing straight up to pointing forward, until the dark olive-green Mercedes G-Wagon lands firmly in the parking lot, parking exactly in the final position of the end frame."

- The image prompt (to make the start frame): "Recreate this image with the following changes: POV view; instead of looking ahead, make it appear as if he is filming the sky, with the small car above him. His arm raised higher, filming a black dot in the sky (the car)."
- **Rules:** (1) lock the shot with a start + end frame, describe only the motion between; (2) "dual growth" / layered detail (the car grows in real space AND inside the phone screen); (3) end the prompt with "lands exactly in the final position of the end frame" so it converges. Workflow: generate new first frames, chain them into the shot, dial the look until it clicks (Supercomputer + Canvas).

## Polish stack (the editing frame)
RESULT vs BEFORE showed motion-tracking points, a **SPEED RAMPS** curve (slow → sharp spike → slow), and an **After Effects timeline**. Polish = speed ramping on the impact/peak beat + motion tracking + AE timeline assembly. The believable shot is 50% prompt, 50% edit.

## When to use which
- **Strategy A (imperfection)** → UGC, testimonial, "caught on camera", relatable/authentic, product-in-real-life. Reads as REAL because it looks unproduced.
- **Strategy B (start/end frame)** → a specific impossible/hero motion you can pin with two frames.
- Both pair with the per-category skills in `pipeline/skills/` and the MONTAGE-CRAFT edit rules.
