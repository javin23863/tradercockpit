// Deterministically re-cut the 5 posted shorts from the FIXED master-clean.mp4,
// reusing manifest ranges + existing per-clip SRTs. Replicates clip.js reframeVertical.
//
// Dual-treatment: article (white-page) windows are luma-detected per clip and get a
// blurred-background "fit" treatment instead of the hard right-anchor crop, so on-page
// text never gets clipped. Chart/globe segments keep the original crop.
const { spawnSync } = require("child_process");
const path = require("path");
const PROD = "C:\\Users\\MSI\\Desktop\\OpenMontage-Skill\\productions\\video-02-hormuz-v4";
const MASTER = path.join(PROD, "build", "master-clean.mp4");
const SHORTS = path.join(PROD, "shorts");

// label base (matches existing shorts/<base>.srt and .vertical.mp4) -> manifest start
const SEGS = [
  { start: 0.0,     base: "clip-006-segment-1" },
  { start: 129.96,  base: "clip-001-hook-1-is-the-straight-actually-closed-" },
  { start: 271.339, base: "clip-002-hook-2-because-83-crude-flows-straight" },
  { start: 429.699, base: "clip-003-hook-3-so-how-high-can-crude" },
  { start: 542.299, base: "clip-004-hook-4-but-the-headline-number-matters" },
];
const DUR = 30;
const style = "FontName=Arial Bold,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=120";
const cw = "trunc(ih*9/16/2)*2";
const cropX = `iw-${cw}`; // CLIP_ANCHOR=right (chart-dominant)

// News-article pages are white-dominant (~200-227 YAVG under this crop); charts/globe/video
// b-roll run dark-to-mid (~30-90), but bright desert/coastline terrain on the globe view
// plateaus around ~128 (confirmed by frame check, not an article) -- 160 clears that false
// positive while staying below the true article cluster (see per-clip series on stdout).
const ARTICLE_YAVG_THRESHOLD = 160;
const SAMPLE_FPS = 2; // 0.5s resolution, matches merge/pad granularity below
const PAD = 0.25;

function detectArticleWindows(startSec) {
  const vf = `crop=${cw}:ih:${cropX}:0,fps=${SAMPLE_FPS},signalstats,metadata=print:key=lavfi.signalstats.YAVG`;
  const r = spawnSync("ffmpeg", [
    "-ss", String(startSec), "-t", String(DUR), "-i", MASTER,
    "-vf", vf, "-f", "null", "-",
  ], { encoding: "utf8" });
  const text = (r.stdout || "") + (r.stderr || "");
  const samples = []; // {t, yavg}
  let pendingT = null;
  for (const line of text.split("\n")) {
    const tm = line.match(/pts_time:([\d.]+)/);
    if (tm) pendingT = parseFloat(tm[1]);
    const ym = line.match(/lavfi\.signalstats\.YAVG=([\d.]+)/);
    if (ym && pendingT !== null) {
      samples.push({ t: pendingT, yavg: parseFloat(ym[1]) });
      pendingT = null;
    }
  }
  // merge consecutive above-threshold samples into [start,end] windows
  const step = 1 / SAMPLE_FPS;
  const windows = [];
  let cur = null;
  for (const s of samples) {
    if (s.yavg >= ARTICLE_YAVG_THRESHOLD) {
      if (!cur) cur = { start: s.t, end: s.t + step };
      else cur.end = s.t + step;
    } else if (cur) {
      windows.push(cur);
      cur = null;
    }
  }
  if (cur) windows.push(cur);
  // pad + clamp + round
  const padded = windows.map(w => ({
    start: Math.round(Math.max(0, w.start - PAD) * 100) / 100,
    end: Math.round(Math.min(DUR, w.end + PAD) * 100) / 100,
  }));
  return { samples, windows: padded };
}

for (const s of SEGS) {
  const srt = path.join(SHORTS, s.base + ".srt");
  const subPath = srt.replace(/\\/g, "/").replace(/^([A-Z]):/i, "$1\\:");
  const out = path.join(SHORTS, s.base + ".vertical.mp4");

  const { samples, windows } = detectArticleWindows(s.start);
  console.log(`--- ${s.base} YAVG series (fps=${SAMPLE_FPS}) ---`);
  console.log(samples.map(x => `${x.t.toFixed(1)}:${x.yavg.toFixed(1)}`).join(" "));
  console.log(`${s.base} article windows (threshold=${ARTICLE_YAVG_THRESHOLD}, padded):`, JSON.stringify(windows));

  let vf;
  if (windows.length === 0) {
    vf = `crop=${cw}:ih:${cropX}:0,scale=1080:1920,setsar=1,subtitles='${subPath}':force_style='${style}'`;
  } else {
    const enable = windows.map(w => `between(t,${w.start},${w.end})`).join("+");
    vf =
      `split=2[a0][a1];` +
      `[a0]crop=${cw}:ih:${cropX}:0,scale=1080:1920,setsar=1[chainA];` +
      `[a1]split=2[bg0][fg0];` +
      `[bg0]scale=1080:1920,gblur=sigma=30,eq=brightness=-0.06[bgb];` +
      `[fg0]scale=1080:-2[fgb];` +
      `[bgb][fgb]overlay=(W-w)/2:(H-h)/2,setsar=1[chainB];` +
      `[chainA][chainB]overlay=0:0:enable='${enable}'[ov];` +
      `[ov]subtitles='${subPath}':force_style='${style}'`;
  }

  const r = spawnSync("ffmpeg", [
    "-y", "-ss", String(s.start), "-t", String(DUR), "-i", MASTER,
    "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
    "-c:a", "aac", "-b:a", "128k", out, "-loglevel", "error",
  ], { encoding: "utf8" });
  console.log(r.status === 0 ? `ok ${s.base}` : `FAIL ${s.base}: ${r.stderr || r.error}`);
}
