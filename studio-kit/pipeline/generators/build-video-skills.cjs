#!/usr/bin/env node
'use strict';
// build-video-skills.cjs — DIGEST a video transcript and SEPARATE it into cinematic craft SKILLS.
// Separate everything — camera movement, angle, photo generation, characters, etc. — into skills, and go through those
// skills every time you make a video so output quality is cinematic. Each category SKILL file COMPOUNDS across every
// transcript you feed (the more references you digest, the sharper the whole library gets), and the master checklist is
// consulted every video.
//
// node build-video-skills.cjs <transcript.txt> [--title="..."]
// node build-video-skills.cjs --text="..." [--title="..."]
//
// Flow: LLM digest (separate the transcript into fixed craft categories) -> APPEND new rules to pipeline/skills/<cat>.md
// (compounds) -> regenerate the master 00-CINEMATIC-CHECKLIST.md. Bring your own LLM via llm.cjs, or run with no key to
// get a ready-to-paste digest prompt.

const fs = require('fs');
const path = require('path');
const { callLLM, llmConfigured, notConfiguredMessage } = require('./llm.cjs');

const SKILLS = path.join(__dirname, '..', 'skills');
const OUT = path.join(__dirname, 'output');
const SYSTEM = 'You are a world-class cinematic AI-video director and editor. Follow the instructions exactly and output ONLY the requested category blocks.';

// The fixed craft categories — "separate everything". Order = the checklist order the studio walks every video.
const CATS = [
 ['idea_concept', 'Idea & Concept', 'the core premise, scene-by-scene plan, why each shot earns its place'],
 ['characters', 'Characters', 'character sheets, consistency, outfits, aging, diversity (avoid clone armies)'],
 ['props', 'Props', 'prop sheets, depth/volume, controlling the exact action'],
 ['locations', 'Locations', 'the location image is ~most of the video quality; angle + engine choice'],
 ['image_generation', 'Image Generation', 'sheets, backgrounds, model-switching, quality checks before animating'],
 ['consistency_continuity', 'Consistency & Continuity', 'lock characters/props/geography across shots — sheets, schematic maps, wet/dry variants, single-face, anchors'],
 ['camera_angle', 'Camera Angle', 'framing that reads cinematic + gives the model depth'],
 ['camera_movement', 'Camera Movement', 'how the camera moves so it feels shot, not generated'],
 ['realism_detail', 'Realism & Detail', 'the texture/lighting cues that make it read as real, not AI'],
 ['prompting', 'Prompting', 'how to write the generation prompt so the model nails it'],
 ['transitions_vfx', 'Transitions & VFX', 'in-camera effects + scene-to-scene transitions with no editing cuts'],
 ['editing_iteration','Editing & Iteration', 'the ad is the best seconds of 100 tries — cut on action, match cuts, pull keeper phases from many takes'],
 ['voiceover_audio', 'Voiceover & Audio', 'narration/VO + sound that lifts the shot'],
 ['hook_structure', 'Hook & Structure', 'how the VIDEO itself hooks + holds a viewer (every shot a hook)'],
 ['local_generation', 'Local & Cloud Generation', 'two lanes to make every shot — cloud AI-gen for photoreal, local $0 engines (Hyperframes/Remotion) for MG + kinetic; pick per shot'],
];

function argVal(argv, name, dflt) { const a = argv.find((x) => x.startsWith(`--${name}=`)); return a ? a.slice(name.length + 3) : dflt; }
function nowIso() { return new Date().toISOString(); }
function slugify(s) { return String(s || 'video').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 50) || 'video'; }

function readTranscript(argv) {
 const t = argVal(argv, 'text', null);
 if (t) return t;
 const file = argv.find((a) => !a.startsWith('--'));
 if (file && fs.existsSync(file)) return fs.readFileSync(file, 'utf8');
 return '';
}

function digestPrompt(transcript) {
 const catList = CATS.map((c) => `### ${c[0]}\n(${c[1]} — ${c[2]})`).join('\n');
 return `You are a world-class cinematic AI-video director/editor. Study this video TRANSCRIPT and extract every REUSABLE TECHNIQUE, then SORT each technique under the exact category headers below. Output ONLY the category blocks, each header on its own line EXACTLY as \`### <key>\`, followed by 2-8 bullet rules. Each rule must be a crisp, imperative, reusable instruction (a checklist item we apply on the NEXT video) — concrete, not vague. If the transcript has nothing for a category, write \`- (none this source)\`. Do NOT copy the transcript's specific story; extract the transferable CRAFT + the exact tool/workflow tips (models, backgrounds, angles, asset habits).

CATEGORIES (use these keys verbatim):
${catList}

TRANSCRIPT:
"""
${String(transcript).slice(0, 16000)}
"""`;
}

// Parse "### key\n- rule\n- rule" blocks into { key: [rules] }
function parseCategories(digest) {
 const out = {};
 const re = /^###\s*([a-z_]+)\s*$/gim;
 const parts = digest.split(/^###\s*/gim).slice(1);
 for (const part of parts) {
 const nl = part.indexOf('\n');
 const key = part.slice(0, nl < 0 ? part.length : nl).trim().toLowerCase().replace(/[^a-z_]/g, '');
 const body = nl < 0 ? '' : part.slice(nl + 1);
 const rules = body.split('\n').map((l) => l.replace(/^[-*]\s?/, '').trim()).filter((l) => l && !/^\(none/i.test(l));
 if (CATS.some((c) => c[0] === key) && rules.length) out[key] = rules;
 }
 return out;
}

function appendSkill(key, label, blurb, rules, title) {
 fs.mkdirSync(SKILLS, { recursive: true });
 const p = path.join(SKILLS, `${key}.md`);
 if (!fs.existsSync(p)) {
 fs.writeFileSync(p, `# 🎬 SKILL — ${label}\n_${blurb}. Apply EVERY video. Rules compound as we study more references._\n`);
 }
 fs.appendFileSync(p, `\n## from: ${title} (${nowIso()})\n${rules.map((r) => `- ${r}`).join('\n')}\n`);
 return p;
}

function regenChecklist(source) {
 const p = path.join(SKILLS, '00-CINEMATIC-CHECKLIST.md');
 const rows = CATS.map((c, i) => {
 const f = path.join(SKILLS, `${c[0]}.md`);
 const has = fs.existsSync(f);
 return `${String(i + 1).padStart(2, '0')}. **[${c[1]}](${c[0]}.md)** — ${c[2]}${has ? '' : ' _(no rules yet)_'}`;
 }).join('\n');
 fs.writeFileSync(p, `# 🎬 CINEMATIC SKILLS CHECKLIST — walk EVERY skill before you generate\n: go through these every time we make a video so output is cinematic. Each file compounds as we digest more references (build-video-skills.cjs). Last updated from: ${source} · ${nowIso()}_\n\n**MANDATE:** before generating any shot, open each skill below and apply its rules; after rendering, re-check the ones that failed. This is the studio's per-video craft gate (pairs with MONTAGE-CRAFT.md + STACK.md).\n\n${rows}\n`);
 return p;
}

async function main() {
 const argv = process.argv.slice(2);
 const transcript = readTranscript(argv);
 if (!transcript || transcript.trim().length < 50) {
 console.error('Usage: node build-video-skills.cjs <transcript.txt> [--title="..."] (need >=50 chars)');
 process.exit(1);
 }
 const title = argVal(argv, 'title', (transcript.trim().split('\n').find((l) => l.replace(/\[[0-9:]+\]/g, '').trim()) || 'video').replace(/\[[0-9:]+\]/g, '').trim().slice(0, 60));

 const prompt = digestPrompt(transcript);

 // No LLM configured -> PASTE-MODE: save the digest prompt so it can be pasted into any LLM; then feed its output back.
 if (!llmConfigured()) {
 fs.mkdirSync(OUT, { recursive: true });
 const p = path.join(OUT, 'skills-digest-prompt-' + slugify(title) + '.md');
 fs.writeFileSync(p, `# Skills digest (READY-TO-RUN PROMPT) — ${title}\n_Assembled ${nowIso()}. Paste everything below into ChatGPT / Claude / any LLM; it returns the category blocks (\`### key\` + rules) that build-video-skills appends into pipeline/skills/._\n\n---\n\n${prompt}\n`);
 console.log(notConfiguredMessage(p));
 return;
 }

 console.log('⚙️ categorized DIGEST (your LLM)…');
 let digest = '';
 try { digest = await callLLM(SYSTEM, prompt, { temperature: 0.3, timeoutMs: 200000 }); }
 catch (e) { console.error('LLM call failed (' + (e && e.message ? e.message : e) + ').'); }
 digest = (digest || '').trim();
 if (!digest) { console.error('digest failed (LLM returned empty)'); process.exit(2); }

 const cats = parseCategories(digest);
 const written = [];
 for (const [key, label, blurb] of CATS) {
 if (cats[key] && cats[key].length) { appendSkill(key, label, blurb, cats[key], title); written.push(`${key} (+${cats[key].length})`); }
 }
 const checklist = regenChecklist(title);

 console.log(`\n✅ SKILLS UPDATED from "${title}":`);
 console.log(written.length ? ' ' + written.join('\n ') : ' (no categories parsed — check digest format)');
 console.log(`\n📋 checklist: ${path.relative(process.cwd(), checklist)}`);
 console.log(`📚 skills dir: ${path.relative(process.cwd(), SKILLS)} — the studio walks every skill before generating.`);
 if (!written.length) { console.log('\n--- raw digest (unparsed) ---\n' + digest.slice(0, 1500)); }
}

main().catch((e) => { console.error('ERR:', e && e.message ? e.message : e); process.exit(1); });
