/**
 * gen-vo.cjs — clean ElevenLabs voiceover from a TEXT FILE (no shell-escaping risk).
 * Studio arsenal. Reads a .txt narration, renders MP3 (and optional WAV) for the assembler.
 *
 *   node gen-vo.cjs --in <narration.txt> --out <abs.mp3> [--voice <id>] [--wav]
 *
 * Voice default = <YOUR_VOICE_ID> (the studio narrator). Needs ELEVENLABS_API_KEY in .env.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..', '..');
function parseEnv(p) { const o = {}; try { for (const l of fs.readFileSync(p, 'utf8').split(/\r?\n/)) { const t = l.trim(); if (!t || t.startsWith('#')) continue; const i = t.indexOf('='); if (i < 0) continue; o[t.slice(0, i).trim()] = t.slice(i + 1).trim().replace(/^["']|["']$/g, ''); } } catch {} return o; }
Object.assign(process.env, parseEnv(path.join(ROOT, '.env')), process.env);

const A = require('minimist')(process.argv.slice(2));
const inFile = A.in || A._[0];
const out = A.out || path.join(process.env.USERPROFILE || '', 'videos/vo.mp3');
const voice = A.voice || process.env.ELEVEN_VOICE_ID || '<YOUR_VOICE_ID>';
const model = process.env.ELEVEN_MODEL_ID || 'eleven_turbo_v2_5';

(async () => {
  if (!inFile || !fs.existsSync(inFile)) { console.error('need --in <narration.txt>'); process.exit(1); }
  const key = process.env.ELEVENLABS_API_KEY;
  if (!key) { console.error('ELEVENLABS_API_KEY missing in .env'); process.exit(1); }
  const text = fs.readFileSync(inFile, 'utf8').replace(/\s+\n/g, '\n').trim();
  fs.mkdirSync(path.dirname(out), { recursive: true });
  console.log(`[gen-vo] voice=${voice} model=${model} chars=${text.length}\n→ ${out}`);
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice}?output_format=mp3_44100_128`, {
    method: 'POST',
    headers: { 'xi-api-key': key, 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, model_id: model, voice_settings: { stability: 0.45, similarity_boost: 0.8, style: 0.3, use_speaker_boost: true } }),
    signal: AbortSignal.timeout(60000),
  });
  if (!res.ok) { console.error('elevenlabs', res.status, (await res.text().catch(() => '')).slice(0, 300)); process.exit(1); }
  fs.writeFileSync(out, Buffer.from(await res.arrayBuffer()));
  const kb = (fs.statSync(out).size / 1024).toFixed(0);
  console.log(`[gen-vo] wrote ${kb}KB`);
  // optional 24k mono wav for Whisper/VoxCPM-style consumers
  if (A.wav) {
    const wav = out.replace(/\.mp3$/i, '.wav');
    try { execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', out, '-ar', '24000', '-ac', '1', wav]); console.log(`[gen-vo] wav → ${wav}`); }
    catch (e) { console.error('wav convert failed:', e.message); }
  }
})();
