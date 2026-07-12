#!/usr/bin/env node
'use strict';
/**
 * slideshow-risk.cjs — a $0, deterministic PRE-RENDER scorer.
 *
 * Catch the "slideshow feel" BEFORE you spend a single render. It scores a shot list / plan across 6 dimensions that
 * reliably predict whether the output will read as directed video or as animated slides — no model, no cost, instant.
 * It's the $0 companion to the TribeV2 attention gate (which scores a FINISHED cut): run this on the plan first, fix
 * what it flags, then render and let TribeV2 grade the result.
 *
 *   node slideshow-risk.cjs <plan.json | shot-pack.md>
 *
 * Input:
 *   - a plan .json: { "scenes": [ {type, description, shot_language:{shot_size,camera_movement,lighting_key},
 *                                  shot_intent, information_role, narrative_role, hero_moment}, ... ],
 *                     "renderer_family": "cinematic-3d" }  (a bare top-level array of scenes also works)
 *   - a shot-pack .md (as produced by generate-shot-pack.cjs / any LLM): the named shots are parsed into scenes
 *     heuristically (camera movement, shot size, lighting, stated intent are read from each shot's text).
 *
 * Each dimension scores 0-5 (LOWER is better). Verdict from the average:
 *   < 2.0 strong · < 3.0 acceptable · < 4.0 revise · >= 4.0 fail (don't render yet).
 * Exit code: 0 = strong/acceptable, 1 = revise/fail (so it can gate a pipeline).
 *
 * (A clean-room re-implementation of the OpenMontage slideshow-risk method + thresholds.)
 */

const fs = require('fs');
const path = require('path');

// ---- verdict from average ------------------------------------------------
function verdictFor(avg) {
  if (avg < 2.0) return 'strong';
  if (avg < 3.0) return 'acceptable';
  if (avg < 4.0) return 'revise';
  return 'fail';
}

function pct(x) { return Math.round(x * 100) + '%'; }
function round1(x) { return Math.round(x * 10) / 10; }

// ---- the 6 dimensions ----------------------------------------------------

// 1. repetition — same scene types / descriptions / shot sizes recurring.
function scoreRepetition(scenes) {
  if (scenes.length < 3) return { score: 0.0, reason: 'Too few scenes to assess repetition' };

  const typeCounts = {};
  for (const s of scenes) { const t = s.type || 'unknown'; typeCounts[t] = (typeCounts[t] || 0) + 1; }
  let topType = 'unknown', topCount = 0;
  for (const t of Object.keys(typeCounts)) if (typeCounts[t] > topCount) { topCount = typeCounts[t]; topType = t; }
  const typeRatio = topCount / scenes.length;

  const descriptions = scenes.map((s) => String(s.description || '').toLowerCase().slice(0, 50));
  const uniqueDescRatio = new Set(descriptions).size / descriptions.length;

  const sizeCounts = {};
  for (const s of scenes) { const sz = (s.shot_language && s.shot_language.shot_size) || 'none'; sizeCounts[sz] = (sizeCounts[sz] || 0) + 1; }
  let topSize = 0;
  for (const sz of Object.keys(sizeCounts)) if (sizeCounts[sz] > topSize) topSize = sizeCounts[sz];
  const sizeRatio = topSize / scenes.length;

  let score = 0.0; const reasons = [];
  if (typeRatio > 0.7) { score += 2.0; reasons.push(`Scene type '${topType}' dominates at ${pct(typeRatio)}`); }
  if (uniqueDescRatio < 0.6) { score += 1.5; reasons.push(`Only ${pct(uniqueDescRatio)} unique descriptions`); }
  if (sizeRatio > 0.6) { score += 1.5; reasons.push(`Same shot size in ${pct(sizeRatio)} of scenes`); }

  return { score: Math.min(5.0, score), reason: reasons.join('; ') || 'Good variety' };
}

// 2. decorative_visuals — scenes that decorate instead of communicate (no stated role/intent).
function scoreDecorative(scenes) {
  let decorative = 0;
  for (const s of scenes) {
    const hasInfo = !!s.information_role, hasNarr = !!s.narrative_role, hasIntent = !!s.shot_intent;
    if (!hasInfo && !hasNarr && !hasIntent) decorative += 1;
  }
  const ratio = decorative / scenes.length;
  const score = Math.min(5.0, ratio * 5.0);
  let reason;
  if (ratio > 0.5) reason = `${decorative}/${scenes.length} scenes have no stated purpose (no information_role, narrative_role, or shot_intent)`;
  else if (ratio > 0.2) reason = `${decorative}/${scenes.length} scenes lack stated purpose`;
  else reason = 'Most scenes have clear communicative purpose';
  return { score: round1(score), reason };
}

// 3. weak_motion — motion that exists but has no narrative purpose.
function scoreWeakMotion(scenes) {
  let totalMoving = 0, purposeless = 0;
  for (const s of scenes) {
    const mv = (s.shot_language && s.shot_language.camera_movement) || 'static';
    if (mv !== 'static' && mv !== 'unspecified' && mv != null) {
      totalMoving += 1;
      if (!s.shot_intent) purposeless += 1;
    }
  }
  if (totalMoving === 0) return { score: 1.5, reason: 'No camera movement defined (may be intentional for static style)' };
  const ratio = purposeless / totalMoving;
  const score = Math.min(5.0, ratio * 4.0);
  const reason = ratio > 0.5 ? `${purposeless}/${totalMoving} moving shots lack shot_intent` : 'Camera movement appears purposeful';
  return { score: round1(score), reason };
}

// 4. weak_shot_intent — no explicit reason for framing / reveal rhythm.
function scoreWeakIntent(scenes) {
  const withIntent = scenes.filter((s) => !!s.shot_intent).length;
  const ratio = withIntent / scenes.length;
  const score = Math.min(5.0, (1.0 - ratio) * 5.0);
  let reason;
  if (ratio < 0.3) reason = `Only ${withIntent}/${scenes.length} scenes have shot_intent — most shots lack purpose`;
  else if (ratio < 0.6) reason = `${withIntent}/${scenes.length} scenes have shot_intent`;
  else reason = 'Strong shot intent coverage';
  return { score: round1(score), reason };
}

// 5. typography_overreliance — too much of the video is text-first.
function scoreTypography(scenes) {
  const textTypes = new Set(['text_card', 'stat_card', 'kpi_grid']);
  const textScenes = scenes.filter((s) => textTypes.has(s.type)).length;
  const ratio = textScenes / scenes.length;
  let score, reason;
  if (ratio > 0.6) { score = 4.0; reason = `${textScenes}/${scenes.length} scenes are text/stat cards — video feels like animated slides`; }
  else if (ratio > 0.4) { score = 2.5; reason = `${textScenes}/${scenes.length} scenes are text-based — consider balancing with visual scenes`; }
  else if (ratio > 0.2) { score = 1.0; reason = 'Balanced text and visual content'; }
  else { score = 0.0; reason = 'Visual-first approach'; }
  return { score, reason };
}

// 6. unsupported_cinematic_claims — a "cinematic" label without cinematic structure.
function scoreCinematicClaims(scenes, rendererFamily) {
  const isCinematic = rendererFamily && String(rendererFamily).toLowerCase().includes('cinematic');
  if (!isCinematic) return { score: 0.0, reason: 'Not claiming cinematic treatment' };

  const issues = [];
  const heroCount = scenes.filter((s) => !!s.hero_moment).length;
  if (heroCount === 0) issues.push('Claims cinematic but has no hero_moment defined');

  const withMovement = scenes.filter((s) => ((s.shot_language && s.shot_language.camera_movement) || 'static') !== 'static').length;
  if (withMovement < scenes.length * 0.3) issues.push(`Claims cinematic but only ${withMovement}/${scenes.length} scenes have camera movement`);

  const withLighting = scenes.filter((s) => !!(s.shot_language && s.shot_language.lighting_key)).length;
  if (withLighting < scenes.length * 0.3) issues.push(`Claims cinematic but only ${withLighting}/${scenes.length} scenes define lighting`);

  const score = Math.min(5.0, issues.length * 1.8);
  return { score: round1(score), reason: issues.join('; ') || 'Cinematic claims supported by structure' };
}

// ---- top-level scorer ----------------------------------------------------
function scoreSlideshowRisk(scenes, rendererFamily, renderRuntime) {
  if (!scenes || !scenes.length) {
    return { average: 5.0, verdict: 'fail', dimensions: {}, render_runtime: renderRuntime || null };
  }
  const dimensions = {
    repetition: scoreRepetition(scenes),
    decorative_visuals: scoreDecorative(scenes),
    weak_motion: scoreWeakMotion(scenes),
    weak_shot_intent: scoreWeakIntent(scenes),
    typography_overreliance: scoreTypography(scenes),
    unsupported_cinematic_claims: scoreCinematicClaims(scenes, rendererFamily),
  };
  const scores = Object.values(dimensions).map((d) => d.score);
  const average = scores.reduce((a, b) => a + b, 0) / scores.length;
  return {
    average: Math.round(average * 100) / 100,
    verdict: verdictFor(average),
    dimensions,
    render_runtime: renderRuntime || null,
  };
}

// ---- shot-pack .md -> scenes (heuristic parse) ---------------------------
const MOVE_RE = /\b(push[- ]?in|pull[- ]?out|dolly|track(?:ing)?|pan|tilt|zoom|crane|orbit|handheld|parallax|whip|arc|boom|truck|steadicam|drone|fly[- ]?through)\b/i;
const SIZE_RE = /\b(extreme close[- ]?up|close[- ]?up|closeup|medium close|medium shot|medium|wide shot|wide|establishing|full[- ]?body|two[- ]?shot|over[- ]the[- ]shoulder|cctv|low[- ]?angle|high[- ]?angle|macro|aerial)\b/i;
const LIGHT_RE = /\b(practical light|lighting|60\/30\/10|key light|rim light|backlight|golden hour|neon|haze|bloom|volumetric|hard light|soft light|chiaroscuro|silhouette)\b/i;
const INTENT_RE = /\b(reads cinematic|why|because|so that|to (?:reveal|show|convey|land|sell|emphasi[sz]e)|hook|payoff|beat|reveal|reason|intent|conveys?|communicates?)\b/i;
const HERO_RE = /\b(hero|impossible shot|money shot|reveal|climax|centerpiece|the reveal)\b/i;
const TEXT_RE = /\b(text card|title card|kinetic (?:type|text)|caption|lower third|stat card|end[- ]?card|headline|on[- ]screen text)\b/i;

// A shot header looks like `**1A**`, `### Shot 2`, `1A.`, `- Shot 3:`, `Shot 4 —`, `1)`.
const SHOT_HEADER_RE = /^\s*(?:#{1,6}\s*)?(?:[-*]\s*)?(?:\*\*)?\s*(?:shot\s*)?(\d{1,2}[A-Za-z]?)\b[\).:\-–]/i;

function parseShotPackMarkdown(md) {
  const lines = md.split(/\r?\n/);
  // Focus on the shots section if present (SHOTS / FRAME PACKS / IMAGE PROMPTS), else scan the whole doc.
  let start = 0;
  for (let i = 0; i < lines.length; i++) {
    if (/^\s*#{0,6}\s*\**\s*\d?\s*\.?\s*(SHOTS|FRAME PACKS|IMAGE PROMPTS)\b/i.test(lines[i])) { start = i; break; }
  }
  const blocks = [];
  let cur = null;
  for (let i = start; i < lines.length; i++) {
    const line = lines[i];
    if (SHOT_HEADER_RE.test(line)) {
      if (cur) blocks.push(cur);
      cur = { label: (line.match(SHOT_HEADER_RE)[1] || '').toUpperCase(), text: line + '\n' };
    } else if (cur) {
      // stop the shots section if we clearly hit a later top-level section (SKILL TICKS / EDIT PASS / PICK PASS)
      if (/^\s*#{0,6}\s*\**\s*\d?\s*\.?\s*(SKILL TICKS|EDIT PASS|PICK PASS)\b/i.test(line)) { blocks.push(cur); cur = null; break; }
      cur.text += line + '\n';
    }
  }
  if (cur) blocks.push(cur);

  // Fallback: no shot headers found — treat markdown headings / numbered items as scenes.
  if (!blocks.length) {
    let c = null;
    for (const line of lines) {
      if (/^\s*(#{1,6}\s+|\d{1,2}[\).]\s+|[-*]\s+)/.test(line) && line.trim().length > 3) {
        if (c) blocks.push(c);
        c = { label: String(blocks.length + 1), text: line + '\n' };
      } else if (c) c.text += line + '\n';
    }
    if (c) blocks.push(c);
  }

  return blocks.map((b) => {
    const t = b.text;
    const isText = TEXT_RE.test(t);
    return {
      type: isText ? 'text_card' : 'shot',
      description: t.replace(/\s+/g, ' ').trim().slice(0, 200),
      shot_language: {
        shot_size: SIZE_RE.test(t) ? (t.match(SIZE_RE)[0].toLowerCase()) : 'none',
        camera_movement: MOVE_RE.test(t) ? (t.match(MOVE_RE)[0].toLowerCase()) : 'static',
        lighting_key: LIGHT_RE.test(t) ? (t.match(LIGHT_RE)[0].toLowerCase()) : null,
      },
      shot_intent: INTENT_RE.test(t) || null,
      hero_moment: HERO_RE.test(t) || null,
      information_role: null,
      narrative_role: null,
    };
  });
}

// ---- input loading -------------------------------------------------------
function loadScenes(file) {
  const raw = fs.readFileSync(file, 'utf8');
  const ext = path.extname(file).toLowerCase();
  if (ext === '.json' || (ext !== '.md' && /^\s*[[{]/.test(raw))) {
    const data = JSON.parse(raw);
    let scenes = [];
    if (Array.isArray(data)) scenes = data;
    else if (Array.isArray(data.scenes)) scenes = data.scenes;
    else if (data.scene_plan && Array.isArray(data.scene_plan.scenes)) scenes = data.scene_plan.scenes;
    return { scenes, rendererFamily: data.renderer_family || null, renderRuntime: data.render_runtime || null, kind: 'json' };
  }
  return { scenes: parseShotPackMarkdown(raw), rendererFamily: null, renderRuntime: null, kind: 'markdown' };
}

// ---- CLI -----------------------------------------------------------------
function main() {
  const file = process.argv.slice(2).find((a) => !a.startsWith('--'));
  if (!file) {
    console.error('Usage: node slideshow-risk.cjs <plan.json | shot-pack.md>');
    console.error('  Scores a shot list / plan for "slideshow feel" BEFORE you render (0-5 per dimension, lower = better).');
    process.exit(1);
  }
  if (!fs.existsSync(file)) { console.error('not found: ' + file); process.exit(1); }

  let loaded;
  try { loaded = loadScenes(file); }
  catch (e) { console.error('could not parse ' + file + ': ' + (e && e.message ? e.message : e)); process.exit(1); }

  const result = scoreSlideshowRisk(loaded.scenes, loaded.rendererFamily, loaded.renderRuntime);

  const bar = { strong: '🟢', acceptable: '🟡', revise: '🟠', fail: '🔴' }[result.verdict] || '⚪';
  console.log(`\n${bar} SLIDESHOW-RISK: ${result.verdict.toUpperCase()}  (avg ${result.average} / 5 · lower is better · parsed ${loaded.scenes.length} scenes from ${loaded.kind})\n`);
  const names = ['repetition', 'decorative_visuals', 'weak_motion', 'weak_shot_intent', 'typography_overreliance', 'unsupported_cinematic_claims'];
  for (const n of names) {
    const d = result.dimensions[n];
    if (!d) continue;
    console.log(`  ${n.padEnd(30)} ${String(d.score).padStart(4)}  — ${d.reason}`);
  }
  console.log('\n  Verdict scale: <2 strong · <3 acceptable · <4 revise · >=4 fail (fix the plan before rendering).');
  console.log('  Companion: score the FINISHED cut with qa-attention-gate.cjs (TribeV2 attention).');

  // Gate exit code: 0 = ship-worthy plan, 1 = needs work.
  process.exit(result.verdict === 'strong' || result.verdict === 'acceptable' ? 0 : 1);
}

if (require.main === module) main();
module.exports = { scoreSlideshowRisk, parseShotPackMarkdown };
