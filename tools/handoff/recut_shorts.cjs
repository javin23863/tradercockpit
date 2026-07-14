// Deterministically re-cut the 5 posted shorts from the FIXED master-clean.mp4,
// reusing manifest ranges + existing per-clip SRTs. Replicates clip.js reframeVertical.
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

for (const s of SEGS) {
  const srt = path.join(SHORTS, s.base + ".srt");
  const subPath = srt.replace(/\\/g, "/").replace(/^([A-Z]):/i, "$1\\:");
  const out = path.join(SHORTS, s.base + ".vertical.mp4");
  const vf = `crop=${cw}:ih:${cropX}:0,scale=1080:1920,setsar=1,subtitles='${subPath}':force_style='${style}'`;
  const r = spawnSync("ffmpeg", [
    "-y", "-ss", String(s.start), "-t", String(DUR), "-i", MASTER,
    "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
    "-c:a", "aac", "-b:a", "128k", out, "-loglevel", "error",
  ], { encoding: "utf8" });
  console.log(r.status === 0 ? `ok ${s.base}` : `FAIL ${s.base}: ${r.stderr || r.error}`);
}
