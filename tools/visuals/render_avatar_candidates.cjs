#!/usr/bin/env node
// Render avatar-candidates.html with the repository's existing Puppeteer install.
const fs = require("fs");
const path = require("path");
const puppeteer = require(path.join(__dirname, "..", "..", "studio-kit",
  "pipeline", "generators", "node_modules", "puppeteer"));

const source = "file:///" + path.join(__dirname, "avatar-candidates.html").replace(/\\/g, "/");
const current = path.join(__dirname, "brand", "avatar.png");
const out = path.join(__dirname, "avatar-candidates");
const candidates = ["needle", "contrast", "monogram"];
const sizes = [
  ["comment", 32],
  ["youtube-comment", 40],
  ["youtube-profile", 98],
  ["tiktok-profile", 100],
  ["instagram-profile", 110],
  ["facebook-profile", 176],
  ["master", 800],
];

(async () => {
  fs.mkdirSync(out, {recursive: true});
  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--force-color-profile=srgb", "--hide-scrollbars"],
  });
  for (const [label, size] of sizes) {
    const page = await browser.newPage();
    await page.setViewport({width: size, height: size, deviceScaleFactor: 1});
    const encoded = fs.readFileSync(current).toString("base64");
    await page.setContent(`<style>*{margin:0}img{display:block;width:100vw;height:100vh}</style><img src="data:image/png;base64,${encoded}">`);
    await page.waitForFunction("document.images[0]?.complete");
    await page.screenshot({path: path.join(out, `current-${label}-${size}.png`)});
    await page.close();
    for (const candidate of candidates) {
      const candidatePage = await browser.newPage();
      await candidatePage.setViewport({width: size, height: size, deviceScaleFactor: 1});
      await candidatePage.goto(`${source}?c=${candidate}`, {waitUntil: "load"});
      try { await candidatePage.evaluateHandle("document.fonts.ready"); } catch (_) {}
      await candidatePage.screenshot({path: path.join(out, `${candidate}-${label}-${size}.png`)});
      await candidatePage.close();
    }
  }
  await browser.close();
  console.log(`ok ${candidates.length} candidates + current reference at ${sizes.length} display sizes`);
})().catch(error => { console.error(error); process.exit(1); });
