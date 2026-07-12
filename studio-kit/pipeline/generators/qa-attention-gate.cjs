'use strict';

// QA attention-gate: find WHERE attention dips in a rendered cut, extract those
// exact frames, Claude-watch + diagnose WHY, and emit the edit/regeneration fix.
//
// Honest scope: TribeV2's front door is a web app (viral-analyser) so the SCORING
// step is documented/handed-off; everything else here is automated and $0.

const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { callLLM, llmConfigured, notConfiguredMessage } = require('./llm.cjs');

const KITROOT = path.join(__dirname, '..', '..');
const SKILLS = path.join(__dirname, '..', 'skills');
const OUT = path.join(__dirname, 'output');
const SYSTEM = 'You are a senior video editor and creative director doing QA on a rendered cut. Follow the instructions exactly and output ONLY the requested analysis — terse and actionable.';

// --- house-style helpers ---

function argVal(name, fallback) {
  const flag = '--' + name + '=';
  for (const a of process.argv.slice(2)) {
    if (a.indexOf(flag) === 0) return a.slice(flag.length);
  }
  return fallback;
}

function nowIso() { return new Date().toISOString(); }

// --- local helpers ---

function slugify(name) {
  const s = String(name)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80);
  return s || 'video';
}

// Load studio skills the same way generate-shot-pack.cjs loadCraft does:
// read pipeline/skills/*.md EXCEPT files starting with "00-", cap each at 1400 chars.
function loadCraft() {
  const dir = SKILLS;
  let files;
  try {
    files = fs.readdirSync(dir);
  } catch (e) {
    return [];
  }
  const out = [];
  for (const f of files.sort()) {
    if (!f.endsWith('.md')) continue;
    if (/^00-/.test(f)) continue;
    try {
      const txt = fs.readFileSync(path.join(dir, f), 'utf8');
      out.push({ name: f, body: txt.slice(0, 1400) });
    } catch (e) {
      // skip unreadable skill file
    }
  }
  return out;
}

function ffmpegAvailable() {
  try {
    const r = spawnSync('ffmpeg', ['-version'], { stdio: 'ignore', timeout: 10000 });
    return !r.error && !r.signal && r.status === 0;
  } catch (e) {
    return false;
  }
}

function usage() {
  console.error('Usage: node qa-attention-gate.cjs --video=<path.mp4> [--dips="14,23,41"] [--engine=seedance]');
}

async function main() {
  const video = argVal('video', null);
  const dipsArg = argVal('dips', null);
  const engine = argVal('engine', 'seedance');

  // 1. Validate --video (required, must exist on disk).
  if (!video) {
    usage();
    process.exit(1);
  }
  const videoPath = path.isAbsolute(video) ? video : path.resolve(process.cwd(), video);
  if (!fs.existsSync(videoPath)) {
    console.error('ERROR: --video not found on disk: ' + videoPath);
    usage();
    process.exit(1);
  }

  const videoBasename = path.basename(videoPath, path.extname(videoPath));
  const slug = slugify(videoBasename);
  const framesDir = path.join(OUT, 'qa-frames', slug);
  const tribeV2Path = path.join(KITROOT, 'tribev2', 'viral-analyser');
  const tribeV2Found = fs.existsSync(tribeV2Path);
  if (!tribeV2Found) {
    console.error('WARNING: TribeV2 viral-analyser not found at ' + tribeV2Path + ' — install TribeV2 there (see pipeline/tool-guides/tribev2.md).');
  }

  // 2. If no --dips: hand off to TribeV2 web app, do NOT fabricate scores.
  if (!dipsArg) {
    console.log('TribeV2 viral-analyser app: ' + tribeV2Path + (tribeV2Found ? '' : ' (NOT FOUND on disk — see pipeline/tool-guides/tribev2.md)'));
    console.log('');
    console.log('Honest scope: the SCORING step is manual (TribeV2 front door is a web app).');
    console.log('Score this cut in the TribeV2 viral-analyser app (open tribev2/viral-analyser,');
    console.log('drop in the video -> it returns the engagement curve + dip timestamps),');
    console.log('then re-run with --dips=<comma seconds>.');
    console.log('');
    console.log('Example: node qa-attention-gate.cjs --video=' + video + ' --dips="14,23,41" --engine=' + engine);
    process.exit(0);
  }

  // 3. Parse dips into normalized (ms precision), deduped, sorted second-marks.
  const seen = new Set();
  const dips = [];
  for (const part of String(dipsArg).split(',')) {
    const t = part.trim();
    if (!t) continue;
    const raw = Number(t);
    if (!Number.isFinite(raw) || raw < 0) {
      console.error('WARNING: skipping invalid dip second: ' + JSON.stringify(t));
      continue;
    }
    const n = Math.round(raw * 1000) / 1000;
    if (seen.has(n)) continue;
    seen.add(n);
    dips.push(n);
  }
  dips.sort((a, b) => a - b);
  if (dips.length === 0) {
    console.error('ERROR: no valid dip seconds parsed from --dips=' + JSON.stringify(dipsArg));
    process.exit(1);
  }

  // Prepare frames dir; if this fails, mark all frames instead of spawning doomed ffmpeg calls.
  let framesDirOk = true;
  try {
    fs.mkdirSync(framesDir, { recursive: true });
  } catch (e) {
    framesDirOk = false;
    console.error('WARNING: could not create frames dir ' + framesDir + ': ' + e.message);
  }

  // 3a. Extract one frame per dip second via ffmpeg; degrade gracefully if missing.
  const haveFfmpeg = ffmpegAvailable();
  if (!haveFfmpeg) {
    console.error('WARNING: ffmpeg unavailable — frames will need to be extracted manually.');
  }

  const frames = [];
  for (const sec of dips) {
    const framePath = path.join(framesDir, 'dip-' + String(sec) + 's.png');
    if (!haveFfmpeg) {
      frames.push({ sec, framePath, ok: false, reason: 'ffmpeg unavailable — extract manually' });
      continue;
    }
    if (!framesDirOk) {
      frames.push({ sec, framePath, ok: false, reason: 'frames dir unavailable — extract manually' });
      continue;
    }
    try {
      // -y precedes the output: ffmpeg ignores trailing options, which would
      // make re-runs die at the overwrite prompt (stdin is ignored).
      const r = spawnSync(
        'ffmpeg',
        ['-y', '-ss', String(sec), '-i', videoPath, '-frames:v', '1', '-q:v', '2', framePath],
        { stdio: 'ignore', timeout: 60000 }
      );
      if (r.error) {
        frames.push({ sec, framePath, ok: false, reason: 'ffmpeg spawn failed: ' + r.error.message });
        continue;
      }
      if (r.signal) {
        frames.push({ sec, framePath, ok: false, reason: 'ffmpeg timed out / killed (' + r.signal + ')' });
        continue;
      }
      if (r.status !== 0) {
        frames.push({ sec, framePath, ok: false, reason: 'ffmpeg exited with status ' + r.status });
        continue;
      }
      let size = 0;
      try { size = fs.statSync(framePath).size; } catch (e) { size = 0; }
      if (size === 0) {
        frames.push({ sec, framePath, ok: false, reason: 'ffmpeg produced no output (dip beyond video end?)' });
        continue;
      }
      frames.push({ sec, framePath, ok: true });
    } catch (e) {
      frames.push({ sec, framePath, ok: false, reason: 'ffmpeg error: ' + e.message });
    }
  }

  // 4. CLAUDE-WATCH + DIAGNOSE: one fusion prompt grounded in the studio skills.
  const craft = loadCraft();
  if (craft.length === 0) {
    console.error('WARNING: no studio skills loaded from pipeline/skills — diagnosis will be ungrounded.');
  }
  const craftText = craft.length
    ? craft.map(c => '### SKILL: ' + c.name + '\n' + c.body).join('\n\n')
    : '(studio skills unavailable — pipeline/skills/*.md missing or unreadable)';

  const dipLines = frames.map(f => {
    const status = f.ok ? ('extracted -> ' + f.framePath) : ('NOT extracted (' + f.reason + ')');
    return '- t=' + f.sec + 's — ' + status;
  }).join('\n');

  const prompt = [
    'You are the QA-attention-gate: a senior video editor + creative director reviewing a RENDERED cut.',
    'TribeV2 returned an engagement curve; below are the dip timestamps (where attention dips).',
    'You also receive the studio skills (craft) — ground every diagnosis in them.',
    '',
    'VIDEO: ' + videoPath,
    'ENGINE (for any regeneration recommendation): ' + engine,
    '',
    'DIP TIMESTAMPS + FRAME STATUS:',
    dipLines,
    '',
    'STUDIO SKILLS (grounded):',
    craftText,
    '',
    'For EACH dip second above, output:',
    '1. The LIKELY reason attention drops there — pacing / slop / composition / audio / hook (or name a specific other).',
    '2. The EXACT edit fix — e.g. cut tighter, move payoff earlier, re-generate the shot with <prompt change>, speed-ramp, add audio sting, reframe, replace B-roll. Be concrete.',
    '3. Which shot to regenerate (if any) — by timestamp / scene reference — and the specific new prompt tweak to use with ' + engine + '.',
    '4. One-line confidence (low / med / high).',
    '',
    'Be terse and actionable. No filler.'
  ].join('\n');

  // If an LLM is configured, diagnose directly. Otherwise PASTE-MODE: embed the ready-to-run prompt in the report.
  let diagnosis = '(no diagnosis produced)';
  const pasteMode = !llmConfigured();
  if (pasteMode) {
    diagnosis = 'No LLM configured — paste the prompt below into ChatGPT / Claude / any LLM to get the diagnosis + fixes.\n\n---\n\n' + prompt;
  } else {
    try {
      const out = await callLLM(SYSTEM, prompt, { temperature: 0.4, timeoutMs: 200000 });
      diagnosis = (out && String(out).trim()) || '(the LLM returned empty output)';
    } catch (e) {
      diagnosis = '(LLM unavailable: ' + (e && e.message ? e.message : String(e)) + ')';
      console.error('WARNING: LLM failed: ' + (e && e.message ? e.message : e));
    }
  }

  // 5. Write the report.
  const reportsDir = OUT;
  const reportPath = path.join(reportsDir, 'qa-' + slug + '.md');
  const extractedCount = frames.filter(f => f.ok).length;

  const lines = [];
  lines.push('# QA Attention Gate — ' + slug);
  lines.push('');
  lines.push('Generated: ' + nowIso());
  lines.push('');
  lines.push('**Video:** `' + videoPath + '`');
  lines.push('**Engine:** ' + engine);
  lines.push('**TribeV2 app:** `' + tribeV2Path + '`' + (tribeV2Found ? '' : ' — NOT FOUND on disk (see pipeline/tool-guides/tribev2.md)'));
  lines.push('');
  lines.push('## Dip timestamps + extracted frames (' + extractedCount + '/' + frames.length + ' extracted)');
  lines.push('');
  for (const f of frames) {
    lines.push('- **t=' + f.sec + 's** — ' + (f.ok ? ('`' + f.framePath + '`') : ('NOT extracted: ' + f.reason)));
  }
  lines.push('');
  lines.push('## Frames directory');
  lines.push('');
  lines.push('`' + framesDir + '`');
  lines.push('');
  lines.push('## Diagnosis + fixes');
  lines.push('');
  lines.push(diagnosis);
  lines.push('');
  lines.push('## Human next step');
  lines.push('');
  lines.push('1. Open the extracted frames above + the TribeV2 engagement curve.');
  lines.push('2. Apply the fixes from the diagnosis (cut / re-generate / speed-ramp / reframe).');
  lines.push('3. Re-render the cut.');
  lines.push('4. Re-score in TribeV2 to confirm the dip lifted.');
  lines.push('');
  const report = lines.join('\n');

  let reportWritten = false;
  try {
    fs.mkdirSync(reportsDir, { recursive: true });
    fs.writeFileSync(reportPath, report, 'utf8');
    reportWritten = true;
  } catch (e) {
    // Don't lose the diagnosis: dump the report to stdout instead.
    console.error('ERROR: cannot write report ' + reportPath + ': ' + e.message);
    console.error('Dumping report to stdout:');
    console.log('');
    console.log(report);
  }

  if (reportWritten) console.log('Report:  ' + reportPath);
  console.log('Frames:  ' + framesDir);
  if (pasteMode && reportWritten) console.log('\n' + notConfiguredMessage(reportPath));

  if (!reportWritten) process.exit(1);
}

main().catch(err => {
  console.error('qa-attention-gate: fatal: ' + (err && err.stack ? err.stack : err));
  process.exit(1);
});
