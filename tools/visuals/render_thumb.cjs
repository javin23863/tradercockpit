#!/usr/bin/env node
// Render a 1280x720 YouTube thumbnail from tools/visuals/thumbnail.html.
// Usage:
//   node render_thumb.cjs --out thumb.png --eyebrow "BRENT CRUDE" --num "$120?" \
//        --phrase "The *Hormuz* Toll" --dir up [--sub "..."]
//   node render_thumb.cjs --json spec.json --out thumb.png      # {eyebrow,num,phrase,dir,sub,palette}
// (Named .cjs, not .py, to reuse the working studio-kit puppeteer — one toolchain. publish.py
//  just takes the resulting png via --thumbnail.)
const path = require("path");
const fs = require("fs");
const {DEFAULT_SPEC, checkThumbnailSpec} = require("./check_thumbnail.cjs");
const puppeteer = require(path.join(__dirname, "..", "..", "studio-kit",
  "pipeline", "generators", "node_modules", "puppeteer"));

function argval(name) {
  const i = process.argv.indexOf("--" + name);
  return i > -1 ? process.argv[i + 1] : undefined;
}

(async () => {
  let spec = {...DEFAULT_SPEC};
  const jsonPath = argval("json");
  if (jsonPath) spec = {...spec, ...JSON.parse(fs.readFileSync(jsonPath, "utf8"))};
  for (const k of ["eyebrow", "num", "phrase", "dir", "sub", "palette", "logoCorner"]) {
    const v = argval(k);
    if (v !== undefined) spec[k] = v;
  }
  const checked = checkThumbnailSpec(spec);
  if (checked.status !== "PASS") throw new Error(`thumbnail rules BLOCK:\n- ${checked.hardFail.join("\n- ")}`);
  spec = checked.spec;
  const out = argval("out") || "thumb.png";

  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(spec)) if (v != null) q.set(k, v);
  const HTML = "file:///" + path.join(__dirname, "thumbnail.html").replace(/\\/g, "/")
    + "?" + q.toString();

  const b = await puppeteer.launch({ headless: true,
    args: ["--no-sandbox", "--force-color-profile=srgb", "--hide-scrollbars"] });
  const p = await b.newPage();
  await p.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1 });
  await p.goto(HTML, { waitUntil: "load" });
  try { await p.evaluateHandle("document.fonts.ready"); } catch (e) {}
  await new Promise(r => setTimeout(r, 300));
  await p.screenshot({ path: out });
  await b.close();
  console.log("thumb ->", out);
})().catch(e => { console.error(e); process.exit(1); });
