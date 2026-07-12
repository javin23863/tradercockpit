#!/usr/bin/env node
/**
 * html3d-render.cjs — Hyperframes-style seek-capture renderer.
 *
 * The technique Hyperframes proves: author in HTML/JS (Three.js / GSAP — the medium LLMs are
 * trained deepest on → far wider creative range than Remotion-React), then SEEK the animation to
 * frame/fps before capturing each frame so it renders deterministically. This runs that path with
 * puppeteer (already installed) + ffmpeg — no bun monorepo build needed.
 *
 * The composition HTML must expose: window.__seek(tSeconds) + window.__ready === true
 * (Three.js: render synchronously inside __seek; everything derived from t → frame-accurate.)
 *
 * Usage:
 * node html3d-render.cjs --html <comp.html> --out <out.mp4> [--fps 30 --dur 6 --w 1080 --h 1920]
 * node html3d-render.cjs --html <comp.html> --still 90 --stillout frame.png # one frame, to LOOK at
 * add --nopost to skip the bloom/grain/vignette ffmpeg pass.
 */
const puppeteer = require('puppeteer');
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const http = require('http');

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.json': 'application/json', '.css': 'text/css',
 // 3D-asset compositions (GLTF characters, HDRI lighting, PBR textures) served from the comp dir
 '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml',
 '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.bin': 'application/octet-stream', '.hdr': 'application/octet-stream' };

const A = {};
for (let i = 2; i < process.argv.length; i++) {
 const k = process.argv[i];
 if (k.startsWith('--')) {
 const key = k.slice(2);
 const next = process.argv[i + 1];
 if (key === 'nopost' || key === 'bloom') { A[key] = true; }
 else { A[key] = next; i++; }
 }
}

const htmlPath = path.resolve(A.html);
if (!fs.existsSync(htmlPath)) { console.error('html not found:', htmlPath); process.exit(1); }
const W = +(A.w || 1080), H = +(A.h || 1920), FPS = +(A.fps || 30), DUR = +(A.dur || 6);
const still = A.still != null ? +A.still : null;

// The compositions self-vendor three.js (three.module.js / three.core.js) and their jsm/ + fonts/ assets next to each
// comp, so nothing needs copying here — just resolve the directory we serve from.
const buildDir = path.dirname(htmlPath);

// serve buildDir over http so ES-module imports (three) resolve — file:// blocks module CORS in Chrome
const server = http.createServer((req, res) => {
 const rel = decodeURIComponent((req.url || '/').split('?')[0]).replace(/^\/+/, '');
 const fp = path.join(buildDir, rel);
 if (!fp.startsWith(buildDir) || !fs.existsSync(fp) || fs.statSync(fp).isDirectory()) { res.writeHead(404); res.end('nf'); return; }
 res.writeHead(200, { 'Content-Type': MIME[path.extname(fp).toLowerCase()] || 'application/octet-stream' });
 fs.createReadStream(fp).pipe(res);
});
server.on('error', (e) => { console.error('[html3d-render] server error:', e.message); }); // no-error-listener = uncaught-exception crash risk

(async () => {
 await new Promise(r => server.listen(0, '127.0.0.1', r));
 const port = server.address().port;
 const fileUrl = `http://127.0.0.1:${port}/${encodeURIComponent(path.basename(htmlPath))}`;
 const browser = await puppeteer.launch({
 headless: true,
 args: [
 '--no-sandbox', '--disable-setuid-sandbox',
 '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
 '--ignore-gpu-blocklist', '--enable-webgl', `--window-size=${W},${H}`,
 '--hide-scrollbars', '--force-color-profile=srgb',
 ],
 });
 try {
 const page = await browser.newPage();
 page.on('console', m => { const t = m.text(); if (/error|Error|undefined|fail/i.test(t)) console.log(' [page]', t); });
 page.on('pageerror', e => console.log(' [pageerror]', e.message));
 await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
 await page.goto(fileUrl, { waitUntil: 'load', timeout: 30000 });
 await page.waitForFunction('window.__ready === true', { timeout: 30000 });

 const seekShot = async (tSec, out) => {
 await page.evaluate(t => window.__seek(t), tSec);
 // two rAFs so Chrome composites the freshly-rendered WebGL buffer into the screenshot
 await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
 await page.screenshot({ path: out, type: 'png' });
 };

 if (still != null) {
 const out = path.resolve(A.stillout || 'still.png');
 await seekShot(still / FPS, out);
 console.log('still ->', out);
 return;
 }

 const framesDir = fs.mkdtempSync(path.join(os.tmpdir(), 'mg3d-'));
 const N = Math.round(DUR * FPS);
 process.stdout.write(`rendering ${N} frames @ ${W}x${H} ${FPS}fps `);
 for (let n = 0; n < N; n++) {
 await seekShot(n / FPS, path.join(framesDir, `f${String(n).padStart(5, '0')}.png`));
 if (n % 30 === 0) process.stdout.write('.');
 }
 process.stdout.write(' done\n');

 const out = path.resolve(A.out || 'out.mp4');
 // post pass options (lesson: a LOW-threshold full-frame gblur+screen WASHES to flat purple — additive
 // sprites glow everywhere. REAL bloom = HIGH threshold (only the brightest cores survive) → blur → screen-add,
 // so blacks stay black and only hot pixels bloom). --bloom enables it; default = subtle vignette+grain only.
 const THR = A.bloomthr || 190;
 const bloomVf = `split[a][b];[b]lutrgb=r='if(gt(val,${THR}),val,0)':g='if(gt(val,${THR}),val,0)':b='if(gt(val,${THR}),val,0)',gblur=sigma=${A.bloomsigma || 10}[bl];[a][bl]blend=all_mode=screen:all_opacity=0.9,vignette=PI/5,noise=alls=4:allf=t,format=yuv420p`;
 const vf = A.nopost ? 'format=yuv420p' : (A.bloom ? bloomVf : 'vignette=PI/5,noise=alls=4:allf=t,format=yuv420p');
 const r = spawnSync('ffmpeg', ['-y', '-framerate', String(FPS), '-i', path.join(framesDir, 'f%05d.png'),
 '-vf', vf, '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', out], { stdio: 'inherit' });
 fs.rmSync(framesDir, { recursive: true, force: true });
 if (r.status !== 0) { console.error('ffmpeg failed'); process.exit(1); }
 console.log('out ->', out, '(' + (fs.statSync(out).size / 1048576).toFixed(1) + ' MB)');
 } finally {
 await browser.close();
 server.close();
 }
})().catch(e => { console.error(e); process.exit(1); });
