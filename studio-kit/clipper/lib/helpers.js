'use strict';

const fs = require('fs');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

function which(bin) {
  const r = spawnSync(process.platform === 'win32' ? 'where' : 'which', [bin]);
  return r.status === 0;
}

function run(cmd, args, opts = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, { stdio: opts.silent ? 'pipe' : 'inherit', ...opts });
    let stdout = '', stderr = '';
    if (opts.silent) {
      child.stdout.on('data', d => stdout += d);
      child.stderr.on('data', d => stderr += d);
    }
    child.on('exit', code => code === 0
      ? resolve({ stdout, stderr })
      : reject(new Error(`${cmd} exit ${code}: ${stderr.slice(-500)}`)));
    child.on('error', reject);
  });
}

function ask(question) {
  return new Promise((resolve) => {
    const rl = require('readline').createInterface({ input: process.stdin, output: process.stdout });
    rl.question(question, (answer) => { rl.close(); resolve(answer.trim()); });
  });
}

function loadEnv() {
  const envPath = path.join(__dirname, '..', '.env');
  if (!fs.existsSync(envPath)) return;
  for (const line of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2];
  }
}

function saveJSON(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

function parseSrt(srtText) {
  const blocks = srtText.replace(/\r/g, '').split(/\n\n+/);
  const cues = [];
  for (const b of blocks) {
    const lines = b.split('\n').filter(Boolean);
    if (lines.length < 2) continue;
    const tsLine = lines.find(l => /-->/.test(l));
    if (!tsLine) continue;
    const m = tsLine.match(/(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})/);
    if (!m) continue;
    const start = +m[1] * 3600 + +m[2] * 60 + +m[3] + +m[4] / 1000;
    const end = +m[5] * 3600 + +m[6] * 60 + +m[7] + +m[8] / 1000;
    const text = lines.slice(lines.indexOf(tsLine) + 1).join(' ').trim();
    cues.push({ start, end, text });
  }
  return cues;
}

function srtTime(s) {
  const hh = String(Math.floor(s / 3600)).padStart(2, '0');
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, '0');
  const ss = String(Math.floor(s % 60)).padStart(2, '0');
  const ms = String(Math.floor((s - Math.floor(s)) * 1000)).padStart(3, '0');
  return `${hh}:${mm}:${ss},${ms}`;
}

function sliceSrt(cues, segStart, segDuration) {
  const segEnd = segStart + segDuration;
  const subset = cues
    .filter(c => c.end > segStart && c.start < segEnd)
    .map((c, i) => {
      const start = Math.max(0, c.start - segStart);
      const end = Math.min(segDuration, c.end - segStart);
      return `${i + 1}\n${srtTime(start)} --> ${srtTime(end)}\n${c.text}\n`;
    });
  return subset.join('\n');
}

function getVideoDuration(videoPath) {
  const r = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', videoPath]);
  return parseFloat(r.stdout.toString().trim());
}

const log = {
  info: (...a) => console.log('[•]', ...a),
  warn: (...a) => console.warn('[!]', ...a),
  error: (...a) => console.error('[X]', ...a),
  step: (n, total, msg) => console.log(`\n[${n}/${total}] ${msg}`),
};

module.exports = {
  which, run, ask, loadEnv, saveJSON,
  parseSrt, srtTime, sliceSrt, getVideoDuration, log,
};
