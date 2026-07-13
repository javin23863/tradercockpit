#!/usr/bin/env node
'use strict';

/**
 * clip.js — YouTube auto-clipper + subtitler.
 *
 * Dead-simple usage:
 *   node clip.js                                  # interactive prompt
 *   node clip.js https://youtube.com/watch?v=...  # YouTube URL
 *   node clip.js ./input/video.mp4                # local video file
 *
 * Optional flags (all have sensible defaults):
 *   --clips 6           number of clips to produce
 *   --duration 30       seconds per clip
 *   --mode hooks        ai | hooks | even | script — 'ai' LLM-scores the clip-worthy moments over the transcript
 *   --reframe           also emit a vertical 9:16 (auto-reframe.py) cut of each clip
 *   --output ./output   where the clips land
 *   --model small       whisper model: tiny | base | small | medium | large-v3
 *   --keep-source       keep the raw download + full SRT for debugging
 *
 * 'ai' mode uses an OpenAI-compatible LLM when configured (env LLM_BASE_URL, LLM_API_KEY, LLM_MODEL —
 * DeepSeek/Ollama/OpenAI); with none set it falls back to the same keyword scorer as 'hooks'. --reframe needs python.
 */

const fs = require('fs');
const path = require('path');
const { which, run, ask, loadEnv, saveJSON, parseSrt, sliceSrt, getVideoDuration, log } = require('./lib/helpers.js');
loadEnv();

const ROOT = __dirname;
const arg = (n, d) => { const i = process.argv.indexOf(n); return i === -1 ? d : process.argv[i + 1]; };
const flag = (n) => process.argv.includes(n);

const CLIPS = parseInt(arg('--clips', '6'), 10);
const DURATION = parseInt(arg('--duration', '30'), 10);
const MODE = arg('--mode', 'hooks');
const OUTPUT = path.resolve(arg('--output', path.join(ROOT, 'output')));
const WHISPER_MODEL = arg('--model', 'small');
const SCRIPT_FILE = arg('--script');
const SRT_IN = arg('--srt'); // pre-made transcript — skips whisper entirely
const KEEP_SOURCE = flag('--keep-source');
const REFRAME = flag('--reframe');

const HOOK_PATTERNS = [
  /\?$/,
  /\b(here'?s why|the secret|nobody tells you|stop doing|let me show you|wait until|watch this|the truth about)\b/i,
  /\b(I (?:wish|never|just|literally|swear|promise|hate|love))\b/i,
  /\b(this changed|this killed|this saved|this destroyed|this works)\b/i,
  /^(so|but|because|listen|imagine|picture this|what if)\b/i,
];

async function checkDeps() {
  const missing = [];
  if (!which('ffmpeg')) missing.push('ffmpeg');
  if (!which('ffprobe')) missing.push('ffprobe (comes with ffmpeg)');
  const useApi = process.env.USE_OPENAI_WHISPER === '1' && process.env.OPENAI_API_KEY;
  if (!SRT_IN && !useApi && !which('whisper')) missing.push('whisper');
  // yt-dlp is only required for URL mode — we'll check later if URL is given
  return missing;
}

function isUrl(s) { return /^https?:\/\//i.test(s); }
function isFile(s) { return s && fs.existsSync(s); }

async function getInput() {
  let target = process.argv[2];
  if (target && !target.startsWith('--')) return target;
  // Interactive
  console.log('\n  YouTube auto-clipper\n');
  console.log('  Paste a YouTube URL, or a path to a local video file');
  console.log('  (or drop a video into the input/ folder and just press enter)\n');
  const answer = await ask('  > ');
  if (answer) return answer;
  // Look in input/ for a video
  const inputDir = path.join(ROOT, 'input');
  if (fs.existsSync(inputDir)) {
    const videos = fs.readdirSync(inputDir).filter(f => /\.(mp4|mov|mkv|webm|avi|m4v)$/i.test(f));
    if (videos.length === 1) return path.join(inputDir, videos[0]);
    if (videos.length > 1) {
      console.log('\n  Multiple videos in input/. Pick one:');
      videos.forEach((v, i) => console.log(`    ${i + 1}) ${v}`));
      const choice = await ask('  > ');
      const idx = parseInt(choice, 10) - 1;
      if (videos[idx]) return path.join(inputDir, videos[idx]);
    }
  }
  throw new Error('No URL or file provided.');
}

async function downloadVideo(url, outDir) {
  if (!which('yt-dlp')) throw new Error('yt-dlp not installed. Run: pip install yt-dlp');
  fs.mkdirSync(outDir, { recursive: true });
  const outTpl = path.join(outDir, 'source.%(ext)s');
  log.step(1, 4, `Downloading: ${url}`);
  await run('yt-dlp', [
    '-f', 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
    '--merge-output-format', 'mp4',
    '-o', outTpl,
    url,
  ]);
  const files = fs.readdirSync(outDir).filter(f => f.startsWith('source.'));
  if (!files.length) throw new Error('yt-dlp produced no output');
  return path.join(outDir, files[0]);
}

async function extractAudio(videoPath, outDir) {
  fs.mkdirSync(outDir, { recursive: true });
  const audioPath = path.join(outDir, 'audio.wav');
  await run('ffmpeg', ['-y', '-i', videoPath, '-vn', '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', audioPath, '-loglevel', 'error']);
  return audioPath;
}

async function transcribeLocal(audioPath, outDir, model = 'small') {
  log.step(2, 4, `Transcribing with Whisper (model=${model})`);
  await run('whisper', [audioPath,
    '--model', model,
    '--output_format', 'srt',
    '--output_dir', outDir,
    '--language', 'en',
    '--verbose', 'False',
  ]);
  const srtPath = path.join(outDir, path.basename(audioPath, path.extname(audioPath)) + '.srt');
  if (!fs.existsSync(srtPath)) throw new Error('Whisper did not produce SRT');
  return srtPath;
}

async function transcribeOpenAI(audioPath, outDir) {
  log.step(2, 4, 'Transcribing via OpenAI Whisper API');
  if (!which('curl')) throw new Error('OpenAI Whisper fallback needs curl in PATH');
  const srtPath = path.join(outDir, 'audio.srt');
  await run('curl', [
    '-s', '-o', srtPath,
    'https://api.openai.com/v1/audio/transcriptions',
    '-H', `Authorization: Bearer ${process.env.OPENAI_API_KEY}`,
    '-F', `file=@${audioPath}`,
    '-F', 'model=whisper-1',
    '-F', 'response_format=srt',
  ]);
  if (!fs.existsSync(srtPath) || fs.statSync(srtPath).size < 50) {
    throw new Error('OpenAI Whisper API returned empty/invalid SRT');
  }
  return srtPath;
}

function pickSegments(cues, duration, n, mode, videoDuration, scriptFile) {
  if (mode === 'script' && scriptFile) {
    const data = JSON.parse(fs.readFileSync(scriptFile, 'utf8'));
    return data.segments || data;
  }
  if (mode === 'even' || !cues.length) {
    const step = Math.max((videoDuration - duration) / Math.max(n - 1, 1), 1);
    return Array.from({ length: n }, (_, i) => ({
      start: Math.round(i * step),
      duration,
      label: `segment-${i + 1}`,
    }));
  }
  const scored = cues.map(c => {
    let score = 0;
    for (const re of HOOK_PATTERNS) if (re.test(c.text)) score += 1;
    return { ...c, score };
  }).filter(c => c.score > 0);
  scored.sort((a, b) => b.score - a.score);
  const picks = [];
  for (const c of scored) {
    if (picks.length >= n) break;
    if (picks.every(p => Math.abs(p.start - c.start) > duration * 1.5)) {
      picks.push({
        start: Math.max(0, c.start - 2),
        duration,
        label: `hook-${picks.length + 1}-${c.text.slice(0, 40).replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`,
      });
    }
  }
  if (picks.length < n) {
    const filler = pickSegments([], duration, n - picks.length, 'even', videoDuration);
    picks.push(...filler);
  }
  return picks.slice(0, n);
}

// AI highlight mode — score clip-worthy moments via an LLM over the transcript, reusing highlight-select.cjs.
// Maps its {start,end,title} to clip.js's {start,duration,label}. Falls back to the keyword scorer inside
// selectHighlights when no LLM is configured, so --mode ai is a strict upgrade over hooks and makes "AI picks
// the moments" real when a key is set.
async function pickSegmentsAI(cues, duration, n) {
  const { selectHighlights } = require('./highlight-select.cjs');
  const clips = await selectHighlights({ cues, clips: n, duration });
  return clips.map((c, i) => ({
    start: Math.max(0, Math.round(c.start)),
    duration: Math.max(5, Math.min(duration, Math.round((c.end - c.start) || duration))),
    label: `ai-${i + 1}-${String(c.title || c.reason || 'clip').slice(0, 40).replace(/[^a-z0-9]+/gi, '-').toLowerCase()}`,
  }));
}

// Vertical 9:16: cut the RAW source, center-crop, THEN burn subs sized for the vertical frame.
// (Burning on 16:9 first cropped the text off both edges.) Best-effort: failure never fails the clip.
// ponytail: center-crop only; wire auto-reframe.py subject-tracking if talking heads drift off-center.
async function reframeVertical(videoPath, seg, srtSlicePath, outFile) {
  const out = outFile.replace(/\.mp4$/i, '.vertical.mp4');
  const subPath = srtSlicePath.replace(/\\/g, '/').replace(/^([A-Z]):/i, '$1\\:');
  const style = "FontName=Arial Bold,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=120";
  try {
    await run('ffmpeg', [
      '-y', '-ss', String(seg.start), '-t', String(seg.duration), '-i', videoPath,
      '-vf', `crop=ih*9/16:ih,scale=1080:1920,subtitles='${subPath}':force_style='${style}'`,
      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
      '-c:a', 'aac', '-b:a', '128k', out, '-loglevel', 'error',
    ]);
    return out;
  } catch (e) { log.warn(`  ↳ reframe failed: ${e.message}`); return null; }
}

async function clipAndBurn(videoPath, srtSlicePath, seg, outFile) {
  const subPath = srtSlicePath.replace(/\\/g, '/').replace(/^([A-Z]):/i, '$1\\:');
  const style = "FontName=Arial Bold,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=60";
  await run('ffmpeg', [
    '-y',
    '-ss', String(seg.start),
    '-t', String(seg.duration),
    '-i', videoPath,
    '-vf', `subtitles='${subPath}':force_style='${style}'`,
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
    '-c:a', 'aac', '-b:a', '128k',
    outFile,
    '-loglevel', 'error',
  ]);
}

async function main() {
  // Check core deps (ffmpeg + whisper unless using API)
  const missing = await checkDeps();
  if (missing.length) {
    log.error('Missing dependencies:');
    missing.forEach(m => log.error('   - ' + m));
    log.error('\nRun check-deps to see install instructions: node check-deps.js');
    process.exit(2);
  }

  const target = await getInput();
  fs.mkdirSync(OUTPUT, { recursive: true });
  const TEMP = path.join(OUTPUT, '.tmp');
  fs.mkdirSync(TEMP, { recursive: true });

  // Resolve: URL or local file
  let videoPath;
  if (isUrl(target)) {
    videoPath = await downloadVideo(target, TEMP);
  } else if (isFile(target)) {
    videoPath = path.resolve(target);
    log.step(1, 4, `Using local file: ${videoPath}`);
  } else {
    throw new Error(`Not a URL or existing file: ${target}`);
  }

  // Transcribe (or reuse a supplied SRT)
  let srtPath;
  if (SRT_IN) {
    srtPath = path.resolve(SRT_IN);
    log.step(2, 4, `Using supplied transcript: ${srtPath}`);
  } else {
    const audioPath = await extractAudio(videoPath, TEMP);
    const useApi = process.env.USE_OPENAI_WHISPER === '1' && process.env.OPENAI_API_KEY;
    srtPath = useApi
      ? await transcribeOpenAI(audioPath, TEMP)
      : await transcribeLocal(audioPath, TEMP, WHISPER_MODEL);
  }

  // Pick segments
  const srtText = fs.readFileSync(srtPath, 'utf8');
  const cues = parseSrt(srtText);
  const videoDuration = getVideoDuration(videoPath);
  log.step(3, 4, `Picking ${CLIPS} segments (mode=${MODE}, video duration=${Math.round(videoDuration)}s)`);
  let segments;
  if (MODE === 'ai') {
    segments = await pickSegmentsAI(cues, DURATION, CLIPS);
    if (!segments.length) { log.warn('ai mode produced nothing — falling back to hooks'); segments = pickSegments(cues, DURATION, CLIPS, 'hooks', videoDuration, SCRIPT_FILE); }
  } else {
    segments = pickSegments(cues, DURATION, CLIPS, MODE, videoDuration, SCRIPT_FILE);
  }

  // Save full-video transcript at top level so client has the whole SRT + TXT
  fs.copyFileSync(srtPath, path.join(OUTPUT, 'transcript.srt'));
  fs.writeFileSync(path.join(OUTPUT, 'transcript.txt'), cues.map(c => c.text).join(' '));

  saveJSON(path.join(OUTPUT, 'manifest.json'), {
    source: target,
    video_duration_s: videoDuration,
    mode: MODE,
    clips_count: segments.length,
    segments,
    created_at: Date.now(),
  });

  // Clip + burn (and persist the matching .srt next to each .mp4)
  log.step(4, 4, `Cutting + burning ${segments.length} clips (saving .srt next to each .mp4)`);
  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    const base = `clip-${String(i + 1).padStart(3, '0')}-${seg.label || 'segment'}`;
    // Write the slice SRT directly to the OUTPUT folder so it's kept
    const sliceOutSrt = path.join(OUTPUT, `${base}.srt`);
    fs.writeFileSync(sliceOutSrt, sliceSrt(cues, seg.start, seg.duration));
    const outFile = path.join(OUTPUT, `${base}.mp4`);
    try {
      // ffmpeg's subtitles filter can read straight from the output-folder SRT
      await clipAndBurn(videoPath, sliceOutSrt, seg, outFile);
      log.info(`✓ ${base}.mp4  +  ${base}.srt  (start=${seg.start}s, ${seg.duration}s)`);
      if (REFRAME) { const v = await reframeVertical(videoPath, seg, sliceOutSrt, outFile); if (v) log.info(`  ↳ vertical 9:16 → ${path.basename(v)}`); }
    } catch (e) {
      log.warn(`✗ ${base}.mp4: ${e.message}`);
    }
  }

  if (!KEEP_SOURCE) {
    try { fs.rmSync(TEMP, { recursive: true, force: true }); } catch (_) {}
  }
  console.log(`\nDone. ${segments.length} clips + matching .srt + transcript.srt/txt in: ${OUTPUT}\n`);
}

if (require.main === module) {
  main().catch(e => { log.error(e.message); process.exit(1); });
}

module.exports = { main };
