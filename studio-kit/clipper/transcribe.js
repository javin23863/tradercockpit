#!/usr/bin/env node
'use strict';

/**
 * transcribe.js — just transcribe, no clipping.
 *
 * Usage:
 *   node transcribe.js                            (interactive)
 *   node transcribe.js https://youtube.com/...    (URL)
 *   node transcribe.js ./input/video.mp4          (local file)
 *
 * Output: output/transcript.srt + transcript.txt + transcript.json
 */

const fs = require('fs');
const path = require('path');
const { which, run, ask, loadEnv, parseSrt, log } = require('./lib/helpers.js');
loadEnv();

const ROOT = __dirname;
const arg = (n, d) => { const i = process.argv.indexOf(n); return i === -1 ? d : process.argv[i + 1]; };

const OUTPUT = path.resolve(arg('--output', path.join(ROOT, 'output')));
const WHISPER_MODEL = arg('--model', 'small');

function isUrl(s) { return /^https?:\/\//i.test(s); }
function isFile(s) { return s && fs.existsSync(s); }

async function getInput() {
  let target = process.argv[2];
  if (target && !target.startsWith('--')) return target;
  console.log('\n  Transcribe a video\n');
  console.log('  Paste a YouTube URL, or a path to a local video file\n');
  const answer = await ask('  > ');
  if (answer) return answer;
  const inputDir = path.join(ROOT, 'input');
  if (fs.existsSync(inputDir)) {
    const videos = fs.readdirSync(inputDir).filter(f => /\.(mp4|mov|mkv|webm|avi|m4v)$/i.test(f));
    if (videos.length === 1) return path.join(inputDir, videos[0]);
  }
  throw new Error('No URL or file provided.');
}

async function main() {
  const target = await getInput();
  fs.mkdirSync(OUTPUT, { recursive: true });

  let videoPath;
  if (isUrl(target)) {
    if (!which('yt-dlp')) throw new Error('yt-dlp not installed. Run: pip install yt-dlp');
    log.step(1, 3, `Downloading: ${target}`);
    await run('yt-dlp', [
      '-f', 'bestaudio',
      '-o', path.join(OUTPUT, 'source.%(ext)s'),
      target,
    ]);
    const files = fs.readdirSync(OUTPUT).filter(f => f.startsWith('source.'));
    videoPath = path.join(OUTPUT, files[0]);
  } else if (isFile(target)) {
    videoPath = path.resolve(target);
    log.step(1, 3, `Using local file: ${videoPath}`);
  } else {
    throw new Error(`Not a URL or existing file: ${target}`);
  }

  log.step(2, 3, 'Extracting audio');
  const audioPath = path.join(OUTPUT, 'audio.wav');
  await run('ffmpeg', ['-y', '-i', videoPath, '-vn', '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', audioPath, '-loglevel', 'error']);

  log.step(3, 3, `Transcribing (model=${WHISPER_MODEL})`);
  const useApi = process.env.USE_OPENAI_WHISPER === '1' && process.env.OPENAI_API_KEY;
  let srtPath;
  if (useApi) {
    if (!which('curl')) throw new Error('curl needed for OpenAI API path');
    srtPath = path.join(OUTPUT, 'transcript.srt');
    await run('curl', [
      '-s', '-o', srtPath,
      'https://api.openai.com/v1/audio/transcriptions',
      '-H', `Authorization: Bearer ${process.env.OPENAI_API_KEY}`,
      '-F', `file=@${audioPath}`,
      '-F', 'model=whisper-1',
      '-F', 'response_format=srt',
    ]);
  } else {
    if (!which('whisper')) throw new Error('whisper not installed. Run: pip install openai-whisper');
    await run('whisper', [audioPath,
      '--model', WHISPER_MODEL,
      '--output_format', 'srt',
      '--output_dir', OUTPUT,
      '--language', 'en',
      '--verbose', 'False',
    ]);
    srtPath = path.join(OUTPUT, 'audio.srt');
    if (fs.existsSync(srtPath)) {
      const renamed = path.join(OUTPUT, 'transcript.srt');
      fs.renameSync(srtPath, renamed);
      srtPath = renamed;
    }
  }

  const srtText = fs.readFileSync(srtPath, 'utf8');
  const cues = parseSrt(srtText);
  const plainText = cues.map(c => c.text).join(' ');
  fs.writeFileSync(path.join(OUTPUT, 'transcript.txt'), plainText);
  fs.writeFileSync(path.join(OUTPUT, 'transcript.json'), JSON.stringify({ source: target, cues, created_at: Date.now() }, null, 2));

  // Clean intermediate
  try { fs.unlinkSync(audioPath); } catch (_) {}

  console.log('\nDone.');
  console.log(`  SRT:  ${srtPath}`);
  console.log(`  TXT:  ${path.join(OUTPUT, 'transcript.txt')}`);
  console.log(`  JSON: ${path.join(OUTPUT, 'transcript.json')}`);
  console.log(`  ${cues.length} cues, ~${plainText.split(/\s+/).length} words`);
}

if (require.main === module) {
  main().catch(e => { log.error(e.message); process.exit(1); });
}
