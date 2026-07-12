#!/usr/bin/env node
'use strict';

/**
 * check-deps.js — verify the three required binaries are installed
 * and tell the user exactly how to install whatever's missing.
 */

const { spawnSync } = require('child_process');

function which(bin) {
  const r = spawnSync(process.platform === 'win32' ? 'where' : 'which', [bin]);
  return { found: r.status === 0, path: r.stdout.toString().trim().split(/\r?\n/)[0] };
}

function version(bin, arg = '--version') {
  const r = spawnSync(bin, [arg], { shell: false });
  if (r.status !== 0) return null;
  return r.stdout.toString().split('\n')[0].trim();
}

const platform = process.platform === 'win32' ? 'windows'
  : process.platform === 'darwin' ? 'mac'
  : 'linux';

const installCmd = {
  'yt-dlp': {
    windows: 'pip install yt-dlp     (or:  scoop install yt-dlp)',
    mac:     'brew install yt-dlp    (or:  pip3 install yt-dlp)',
    linux:   'pip install yt-dlp     (or:  sudo apt install yt-dlp)',
  },
  'ffmpeg': {
    windows: 'choco install ffmpeg   (or download from ffmpeg.org and add bin/ to PATH)',
    mac:     'brew install ffmpeg',
    linux:   'sudo apt install ffmpeg',
  },
  'whisper': {
    windows: 'pip install openai-whisper',
    mac:     'pip3 install openai-whisper',
    linux:   'pip install openai-whisper',
  },
};

const deps = ['yt-dlp', 'ffmpeg', 'ffprobe', 'whisper'];

console.log('\n  Dependency check\n');
let missing = 0;
for (const bin of deps) {
  const r = which(bin);
  if (r.found) {
    const v = version(bin, '--version') || version(bin, '-version') || '?';
    console.log(`  ✓ ${bin.padEnd(10)} — ${v.slice(0, 70)}`);
  } else {
    missing++;
    const hint = installCmd[bin]?.[platform] || installCmd[bin]?.linux || 'see project README';
    console.log(`  ✗ ${bin.padEnd(10)} — NOT FOUND`);
    if (bin !== 'ffprobe') {  // ffprobe comes with ffmpeg
      console.log(`     install: ${hint}`);
    }
  }
}

console.log();
if (missing === 0) {
  console.log('  All dependencies present. You can run:  node clip.js\n');
  process.exit(0);
} else {
  console.log(`  ${missing} missing — install above, restart your terminal, re-run this script.\n`);
  process.exit(1);
}
