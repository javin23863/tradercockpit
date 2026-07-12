#!/usr/bin/env node
'use strict';
// generate-shot-pack.cjs — THE generation entry point that CONSUMES the compounded craft skills.
// Go through these skills every time you make a video, so output quality is cinematic.
// The skills (pipeline/skills/*.md) + the reference playbooks are the LEARNED craft; this turns a CONCEPT into a
// production-ready CONNECTED shot pack (a STYLE-PREFIX block glued to N named shot prompts) that walks every skill —
// character consistency, frame-coordinate placement, practical-light-only, 60/30/10, angle/movement, realism cues,
// transitions, VO — ready to paste into Seedance / Kling / Higgsfield.
//
// node generate-shot-pack.cjs --concept="..." [--shots=6] [--aspect=9:16] [--style="..."] [--realism=ugc|hero]
//
// Flow: LOAD all skills + reference playbooks (the learned craft) -> your LLM (or paste-mode) generates the connected
// shot pack applying the master checklist -> write output/<slug>.md. The craft the studio learned is now what every
// generation is built from. Bring your own LLM via llm.cjs, or run with no key to get a ready-to-paste prompt.

const fs = require('fs');
const path = require('path');
const { callLLM, llmConfigured, notConfiguredMessage } = require('./llm.cjs');

const SKILLS = path.join(__dirname, '..', 'skills');
const PLAYBOOKS = path.join(__dirname, '..', 'playbooks');
const OUT = path.join(__dirname, 'output');

const SYSTEM = 'You are a world-class cinematic AI-video director. Follow the instructions exactly and output ONLY the requested markdown — no preamble, no commentary.';

function argVal(argv, name, dflt) { const a = argv.find((x) => x.startsWith(`--${name}=`)); return a ? a.slice(name.length + 3) : dflt; }
function nowIso() { return new Date().toISOString(); }
function slugify(s) { return String(s || 'concept').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 50) || 'concept'; }

// Load every compounded skill file (the learned craft), compactly. 00-CINEMATIC-CHECKLIST is the index — load it first,
// then each skill file (its rules), budget-capped so the whole craft base fits one prompt.
function loadCraft() {
 const parts = [];
 const checklist = path.join(SKILLS, '00-CINEMATIC-CHECKLIST.md');
 if (fs.existsSync(checklist)) parts.push('=== MASTER CHECKLIST (walk EVERY skill) ===\n' + fs.readFileSync(checklist, 'utf8').trim());
 const files = fs.existsSync(SKILLS) ? fs.readdirSync(SKILLS).filter((f) => f.endsWith('.md') && !f.startsWith('00-')).sort() : [];
 for (const f of files) {
 const body = fs.readFileSync(path.join(SKILLS, f), 'utf8').trim();
 // keep each skill's rules but cap runaway compounding (rules repeat across sources; the model needs the gist, not
 // 4 near-duplicate passes) — the tighter cap keeps all categories represented while cutting latency.
 parts.push(`=== SKILL: ${f.replace('.md', '')} ===\n${body.slice(0, 1400)}`);
 }
 return parts.join('\n\n');
}

// The reference playbooks are the proven prompt STRUCTURES (ultra-realism imperfection + start/end-frame).
function loadReferences() {
 const parts = [];
 for (const f of ['reference-prompts-ultrareal.md']) {
 const p = path.join(PLAYBOOKS, f);
 if (fs.existsSync(p)) parts.push(fs.readFileSync(p, 'utf8').trim().slice(0, 4000));
 }
 return parts.join('\n\n');
}

// ENGINE ADAPTER — per-engine rules that auto-remove that engine's known failure modes (data in engine-adapters.json).
function loadEngineAdapter(engine) {
 try {
 if (!engine) return '';
 const adapters = JSON.parse(fs.readFileSync(path.join(__dirname, 'engine-adapters.json'), 'utf8'));
 const adapter = adapters[engine];
 if (!adapter) return '';
 const rules = Array.isArray(adapter.rules) ? adapter.rules.filter(Boolean) : [];
 if (!rules.length) return '';
 return `=== ENGINE ADAPTER: ${adapter.label || engine} (obey these — they remove this engine's failure modes) ===\n${rules.map((r) => `- ${r}`).join('\n')}`;
 } catch (_) { return ''; }
}

// PROJECT STYLE LOCK — if a project-style.md sits next to this script, its look is glued VERBATIM to every shot (team consistency).
function loadStyleLock() {
 try { const p = path.join(__dirname, 'project-style.md'); if (!fs.existsSync(p)) return ''; return fs.readFileSync(p, 'utf8').trim().slice(0, 2000); }
 catch (_) { return ''; }
}

// Section 4 differs by MODE: 'shots' (text-to-video shot list) · 'frames' (first-frame/last-frame image-to-video) ·
// 'pic' (standalone image / picture generation — the "pics" surface, same craft applied to a still).
function section4(mode, shots) {
 if (mode === 'frames') {
 return `4. **FRAME PACKS 1..${shots}** — FIRST-FRAME / LAST-FRAME image-to-video (Seedance CS 2.0 / Kling / Higgsfield image-to-video). For EACH named shot output THREE blocks, applying Strategy B:
 - **START FRAME (image-gen prompt)** — a photographer-grade prompt (lens, aperture, film stock/grain, halation, exact 60/30/10 lighting, the character locked to the schematic X/Y, practical light only) describing the EXACT first frame. If a character sheet is involved, note which sheet/state to reference. Feeds an image model (GPT-image / Soul Cinema / Higgsfield generate_image).
 - **END FRAME (image-gen prompt)** — the same photographer-grade prompt for the RESOLVED final frame (the position/state the motion lands in). Same character/lighting/lens; only what MOVED changes.
 - **MOTION PROMPT (image-to-video)** — describes ONLY the motion BETWEEN the two frames (camera + subject), with the realism cues, ending with "…lands/settles exactly in the final position of the end frame" so it converges. Engine mode = image-to-video, first+last frame attached.
 Each frame pack = 3 blocks. Keep the character identity/clothing/hair IDENTICAL between start and end frame.`;
 }
 if (mode === 'character') {
 return `4. **CHARACTER BIBLE** — from the brief, FILL EVERY GAP into a complete, reusable character the studio can generate + keep consistent across a whole video. Output these blocks:
 - **IDENTITY** — age, build/height, face (bone structure, eyes, skin texture "realistic pores, no makeup", hair, distinguishing marks), demeanor/energy. Be exhaustive and specific — this is what locks consistency.
 - **WARDROBE** — the default outfit head-to-toe + 1-2 alternates if the story needs them; exact fabrics/colors (tie to a palette).
 - **CHARACTER SHEET PROMPTS** — the photographer-grade image-gen prompts to BUILD the sheet: (a) gray-bg (#7A7A7A) closeup face, (b) gray-bg full-body front, (c) gray-bg full-body back. Single-face rule: "erase any duplicate face." Note: batch on gray for higher win-rate; test candidates in motion before locking.
 - **EXPRESSION / STATE SHEET** — key expressions (neutral, the story's core emotion) with anatomical specifics (jaw, eyes, brow) so reactions aren't robotic; + any STATE variants the outcome needs (wet/dry, injured, aged, transformed) each as its own locked asset.
 - **PROP LOCKS** — any signature prop the character carries, each as a clean prop-sheet reference (outside + inside if hands interact with it).
 - **CONSISTENCY LOCK** — the verbatim line to paste into every shot: "Maintain consistent identity, clothing, hairstyle, and appearance throughout the entire video."
 Fill gaps intelligently from the brief — the user gives the seed, YOU complete the high-end spec.`;
 }
 if (mode === 'pic') {
 return `4. **IMAGE PROMPTS 1..${shots}** — standalone PICTURES (product shots / character sheets / scene stills for GPT-image / Soul Cinema / Higgsfield generate_image). For EACH named image output:
 - **IMAGE PROMPT** — a PHOTOGRAPHER-grade prompt: specific lens + aperture + film stock/grain/halation + camera, the exact 60/30/10 lighting (PRACTICAL LIGHT ONLY), subject placed at the schematic X/Y, 3/4 or CCTV angle (never head-on), realistic skin/material texture, and the exact composition. For a character/product SHEET use gray background + single-face + closeup+full-body panels (higher win-rate). No vague adjectives.
 - **NEGATIVE / EXCLUSIONS** — what to keep OUT (extra light sources, plastic/AI-slop look, duplicate faces, wrong props, head-on framing).
 - **CONSISTENCY NOTE** — which locked sheet/asset to reference so this still matches the rest of the set.
 Each image = those 3 lines. Images are cheap — say when to batch + pick the winner on gray.`;
 }
 return `4. **SHOTS 1..${shots}** — each a NAMED shot (e.g. \`1A\`, \`1B\`) with: the ANGLE (3/4 or specific, why it reads cinematic), CAMERA MOVEMENT, the beat/action spelled out move-by-move (choreography, not "he dances"), the REALISM strategy for this shot (A = imperfection/UGC cues: handheld shake, autofocus hunting, lens breathing, exposure pumping, rolling shutter, sensor noise, "No stabilization/cinematic-moves/color-grading" — OR B = start-frame + end-frame with only the motion between described, ending "lands exactly in the final position of the end frame"), the TRANSITION into the next shot (match-cut / in-camera), and AUDIO (ambient-only or VO line). Pick A or B per shot based on whether it's UGC-real or a hero/impossible shot.`;
}

function genPrompt({ concept, shots, aspect, style, realism, craft, refs, mode, engine }) {
 // Project style-lock (glue one look across a whole film) + engine adapter (strip the target engine's failure modes).
 // Both resolve to '' when their source file is missing, so they add no noise.
 const styleLockRaw = loadStyleLock();
 const styleLockSection = styleLockRaw ? `\n=== LOCKED PROJECT STYLE PREFIX (use this VERBATIM as the style prefix for every shot — do not invent a new one) ===\n${styleLockRaw}\n` : '';
 const engineBlock = loadEngineAdapter(engine);
 const engineSection = engineBlock ? `\n${engineBlock}\n` : '';
 // CHARACTER mode is a focused bible, not the 6-section video structure — the user gives a seed, we fill every gap.
 if (mode === 'character') {
 return `You are the cinematic STUDIO director + character designer. Turn the CHARACTER BRIEF below into a complete, production-ready CHARACTER BIBLE the studio can generate and keep perfectly consistent across an entire video. The user gives a SEED — you FILL EVERY GAP to a high-end spec using the learned craft below. This is not generic — apply the specific character/consistency/image-generation/realism skills.
${styleLockSection}
${section4('character')}${engineSection}

RULES: be exhaustive and CONCRETE (a generator must be able to build this character from your spec alone). Realistic skin texture, no plastic/AI-slop look. Photographer-grade image prompts (lens, light, gray-bg). No vague adjectives. Fill gaps intelligently from the brief.

CHARACTER BRIEF: "${concept}"${style ? `\nStyle/world: "${style}".` : ''}

=== LEARNED CRAFT SKILLS (apply the character/consistency/image/realism skills) ===
${craft}

=== PROVEN REFERENCE PROMPT STRUCTURES (reuse the STRUCTURE) ===
${refs}`;
 }
 const kindLine = mode === 'frames'
 ? 'Turn the CONCEPT below into a PRODUCTION-READY FIRST-FRAME / LAST-FRAME (image-to-video) pack that Seedance CS 2.0 / Kling / Higgsfield can execute per shot.'
 : mode === 'pic'
 ? 'Turn the CONCEPT below into a PRODUCTION-READY set of standalone IMAGE (picture) prompts that GPT-image / Soul Cinema / Higgsfield generate_image can execute.'
 : 'Turn the CONCEPT below into a PRODUCTION-READY shot pack that a generator (Seedance / Kling / Higgsfield) can execute shot-by-shot.';
 const unit = mode === 'frames' ? 'frame packs (first+last frame each)' : mode === 'pic' ? 'images' : 'shots';
 const editOrPick = mode === 'pic'
 ? '6. **PICK PASS** — how to batch + choose the winners (gray-bg win-rate, test a couple candidates in motion/context, lock the winner), and the quality-preservation mask trick if any asset gets edited downstream.'
 : '6. **EDIT PASS** — the montage/edit notes: cut-on-action, speed-ramp the peak beat, keeper-phase harvesting (best 1-2s of many takes), frame-by-frame FPS check.';
 return `You are the cinematic STUDIO director. ${kindLine} You MUST apply the studio's LEARNED CRAFT SKILLS and the proven REFERENCE STRUCTURES — this is not generic prompting, it is the specific craft below.
${styleLockSection}
OUTPUT (clean markdown, in this exact order):
1. **STYLE PREFIX** — one connected block glued to every ${unit === 'images' ? 'image' : 'shot'}: film-emulation look, lighting rule (PRACTICAL LIGHT ONLY unless the concept needs otherwise), camera/lens language, and the 60/30/10 color split (name the 3 colors). Changing this once changes everything.
2. **CHARACTER / ASSET LOCKS** — for each recurring character/product: the sheet spec (gray-bg closeup+full-body, single-face, wet/dry variants if state changes) + one line on maintaining consistent identity/clothing/hair.
3. **LOCATION ANCHOR + SCHEMATIC** — the anchor object + a frame-coordinate map (X/Y placement, e.g. "hero at 20%X/30%Y, anchor at 70%X"); never generate the location head-on (use 3/4 or CCTV).
${section4(mode, shots)}
5. **SKILL TICKS** — after each ${mode === 'pic' ? 'image' : 'shot/frame pack'}, a one-line check confirming which skill categories it satisfies (characters ✓ consistency ✓ camera-angle ✓ realism ✓ …).
${editOrPick}

RULES: be CONCRETE and reusable — no vague adjectives ("cinematic", "high quality", "4K" do nothing per the craft). Every ${mode === 'pic' ? 'image' : 'shot'} earns its place. Match the realism strategy to the job. Density control: ONE main idea + ONE main action + ONE camera strategy per ${mode === 'pic' ? 'image' : 'shot'}.

CONCEPT: "${concept}"
FORMAT: ${aspect} aspect. ${shots} ${unit}. Default realism lean: ${realism}.${style ? ` Style direction: "${style}".` : ''}

=== LEARNED CRAFT SKILLS (apply all — this is the studio's compounded knowledge) ===
${craft}

=== PROVEN REFERENCE PROMPT STRUCTURES (reuse the STRUCTURE, swap the content) ===
${refs}${engineSection}`;
}

async function main() {
 const argv = process.argv.slice(2);
 const concept = argVal(argv, 'concept', null) || argv.find((a) => !a.startsWith('--'));
 if (!concept || concept.trim().length < 8) {
 console.error('Usage: node generate-shot-pack.cjs --concept="..." [--shots=6] [--aspect=9:16] [--style="..."] [--realism=ugc|hero] [--frames|--pic]');
 console.error(' default = video shot pack (text-to-video)');
 console.error(' --frames = FIRST-FRAME / LAST-FRAME image-to-video packs (start image + end image + motion prompt)');
 console.error(' --pic = standalone IMAGE / picture prompts (product shots, character sheets, scene stills)');
 process.exit(1);
 }
 // MODE: default 'shots' (video) · --frames (first/last frame) · --pic (images) · --character (character bible) · --mode=X
 const mode = argVal(argv, 'mode',
 argv.includes('--frames') ? 'frames'
 : argv.includes('--pic') ? 'pic'
 : argv.includes('--character') || argv.includes('--char') ? 'character'
 : 'shots');
 const shots = Math.max(1, Math.min(20, parseInt(argVal(argv, 'shots', '6'), 10) || 6));
 const aspect = argVal(argv, 'aspect', '9:16');
 const style = argVal(argv, 'style', '');
 const realism = argVal(argv, 'realism', 'ugc');
 const engine = argVal(argv, 'engine', 'seedance'); // target engine — auto-applies its adapter rules (engine-adapters.json)

 const craft = loadCraft();
 const refs = loadReferences();
 if (!craft || craft.length < 200) { console.error('no skills found in ' + SKILLS + ' — the kit ships them in pipeline/skills/, or run build-video-skills.cjs on a transcript.'); process.exit(2); }

 const assembled = genPrompt({ concept, shots, aspect, style, realism, craft, refs, mode, engine });
 if (argv.includes('--print-prompt')) { // dry-run: inspect the assembled prompt (with style-lock + engine adapter)
 process.stdout.write(assembled);
 return;
 }
 const unitLabel = mode === 'frames' ? 'frame-pack' : mode === 'pic' ? 'image' : mode === 'character' ? 'character' : 'shot';
 const skillCount = fs.existsSync(SKILLS) ? fs.readdirSync(SKILLS).filter((f) => f.endsWith('.md') && !f.startsWith('00-')).length : 0;
 fs.mkdirSync(OUT, { recursive: true });
 const slug = slugify(concept) + (mode === 'frames' ? '-frames' : mode === 'pic' ? '-pics' : mode === 'character' ? '-character' : '');
 const p = path.join(OUT, `${slug}.md`);
 const title = mode === 'frames' ? 'FIRST/LAST-FRAME PACK' : mode === 'pic' ? 'IMAGE PACK' : mode === 'character' ? 'CHARACTER BIBLE' : 'SHOT PACK';

 // If an LLM is configured, generate the pack directly. Otherwise PASTE-MODE: save the fully-assembled pro prompt
 // so it can be pasted into any LLM. Either way the tool always produces value.
 if (llmConfigured()) {
 console.log(`⚙️ generating ${shots}-${unitLabel} pack (${mode}) from ${craft.length} chars of learned craft + reference structures (your LLM)…`);
 let pack = '';
 try { pack = await callLLM(SYSTEM, assembled, { temperature: 0.6, timeoutMs: 200000 }); }
 catch (e) { console.error('LLM call failed (' + (e && e.message ? e.message : e) + ') — falling back to paste-mode.'); }
 if (pack && pack.trim()) {
 const header = `# 🎬 ${title} — ${concept}\n_Generated ${nowIso()} · ${shots} ${unitLabel}s · ${aspect} · built from the compounded studio skills (pipeline/skills/) + reference playbooks. Walk the checklist before generating._\n\n`;
 fs.writeFileSync(p, header + pack.trim() + '\n');
 console.log(`\n✅ ${title}: ${p}`);
 console.log(` ${shots} ${unitLabel}s · applies all ${skillCount} skill categories + reference structures.`);
 return;
 }
 }

 // PASTE-MODE — save the ready-to-run prompt.
 const header = `# 🎬 ${title} (READY-TO-RUN PROMPT) — ${concept}\n_Assembled ${nowIso()} · ${shots} ${unitLabel}s · ${aspect} · built from the compounded studio skills (pipeline/skills/) + reference playbooks. Paste everything below into ChatGPT / Claude / any LLM to generate._\n\n---\n\n`;
 fs.writeFileSync(p, header + assembled + '\n');
 console.log(notConfiguredMessage(p));
}

main().catch((e) => { console.error('ERR:', e && e.message ? e.message : e); process.exit(1); });
