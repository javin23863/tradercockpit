#!/usr/bin/env node
// Render tools/visuals/brand-v2.html -> tools/visuals/brand/*.png at exact pixel sizes.
// Reuses the studio-kit puppeteer (same as capture_gauntlet.cjs). Usage: node render_brand.cjs
const path = require("path");
const fs = require("fs");
const puppeteer = require(path.join(__dirname, "..", "..", "studio-kit",
  "pipeline", "generators", "node_modules", "puppeteer"));

const HTML = "file:///" + path.join(__dirname, "brand-v2.html").replace(/\\/g, "/");
const OUT = path.join(__dirname, "brand");

const MODES = [
  { m: "avatar",  w: 800,  h: 800,  t: false, out: "avatar.png" },
  { m: "banner",  w: 2560, h: 1440, t: false, out: "banner.png" },
  { m: "fbcover", w: 1640, h: 624,  t: false, out: "fb-cover.png" },
  { m: "wm",      w: 150,  h: 150,  t: true,  out: "watermark.png" },
  { m: "logo",    w: 1200, h: 320,  t: true,  out: "logo.png" },
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--force-color-profile=srgb", "--hide-scrollbars"],
  });
  for (const s of MODES) {
    const p = await b.newPage();
    await p.setViewport({ width: s.w, height: s.h, deviceScaleFactor: 1 });
    await p.goto(HTML + "?m=" + s.m, { waitUntil: "load" });
    try { await p.evaluateHandle("document.fonts.ready"); } catch (e) {}
    await new Promise(r => setTimeout(r, 350));   // let webfont metrics settle
    await p.screenshot({ path: path.join(OUT, s.out), omitBackground: s.t });
    await p.close();
    console.log("ok", s.out, `${s.w}x${s.h}`);
  }
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
