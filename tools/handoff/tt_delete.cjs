// Delete listed posts from TikTok Studio content manager (row menu -> Delete -> confirm).
const path = require("path");
const puppeteer = require(path.join("C:", "Users", "MSI", "Desktop", "OpenMontage-Skill",
  "studio-kit", "pipeline", "generators", "node_modules", "puppeteer"));
const SHOTS = path.join(__dirname, "shots");
require("fs").mkdirSync(SHOTS, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));

// row-title match strings of the posts to delete
const TARGETS = process.argv.slice(2).length ? process.argv.slice(2) : [
  "$83 crude flows straight",
  "clip-001-hook-1",
  "clip-003-hook-3",
  "Trump just put a 20% toll",
];

(async () => {
  const b = await puppeteer.connect({ browserURL: "http://localhost:9333", defaultViewport: null });
  const p = (await b.pages()).find(x => (x.url() || "").includes("tiktokstudio/content"));
  await p.bringToFront();

  for (const [i, t] of TARGETS.entries()) {
    console.log(`--- delete: ${t}`);
    await p.goto("https://www.tiktok.com/tiktokstudio/content", { waitUntil: "domcontentloaded" });
    await sleep(4000);
    const opened = await p.evaluate(m => {
      const row = [...document.querySelectorAll("tr,div")].filter(d =>
        d.textContent.includes(m) && d.querySelector("button") && d.textContent.length < 600).pop();
      if (!row) return false;
      const btns = [...row.querySelectorAll("button,[role=button]")];
      btns[btns.length - 1].click();
      return true;
    }, t);
    if (!opened) { console.log("  row not found (already gone?)"); continue; }
    await sleep(800);
    const del = await p.evaluate(() => {
      const e = [...document.querySelectorAll("div,li,span")].find(x => x.textContent.trim() === "Delete" && x.getBoundingClientRect().width > 0 && x.getBoundingClientRect().width < 300);
      if (e) { e.click(); return true; } return false;
    });
    console.log("  Delete clicked:", del);
    await sleep(1200);
    // confirm dialog
    const conf = await p.evaluate(() => {
      const e = [...document.querySelectorAll("button,div[role=button]")].find(x => /^Delete$/.test(x.textContent.trim()) && x.getBoundingClientRect().width > 0);
      if (e) { e.click(); return true; } return false;
    });
    console.log("  confirmed:", conf);
    await sleep(2500);
    await p.screenshot({ path: path.join(SHOTS, `del-${i}.png`) });
  }
  await p.goto("https://www.tiktok.com/tiktokstudio/content", { waitUntil: "domcontentloaded" });
  await sleep(4000);
  const left = await p.evaluate(() => [...document.querySelectorAll("tr,div")]
    .filter(d => d.textContent.length < 600 && /clip-|crude|Trump|banks/.test(d.textContent) && d.querySelector("button"))
    .map(d => d.textContent.slice(0, 60)));
  console.log("rows remaining:", JSON.stringify([...new Set(left)].slice(0, 8)));
  b.disconnect();
})().catch(e => { console.error("ERR", e.message); process.exit(1); });
