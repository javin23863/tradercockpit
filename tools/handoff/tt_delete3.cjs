// TikTok Studio delete: element.click() opens the row menu (proven), real mouse
// click on the Delete item + confirm (React needs trusted events for those).
const path = require("path");
const puppeteer = require(path.join("C:", "Users", "MSI", "Desktop", "OpenMontage-Skill",
  "studio-kit", "pipeline", "generators", "node_modules", "puppeteer"));
const SHOTS = path.join(__dirname, "shots");
require("fs").mkdirSync(SHOTS, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));

const TARGETS = [
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
    await sleep(4500);
    const opened = await p.evaluate(m => {
      const row = [...document.querySelectorAll("tr,div")].filter(d =>
        d.textContent.includes(m) && d.querySelector("button") && d.textContent.length < 600).pop();
      if (!row) return false;
      const btns = [...row.querySelectorAll("button,[role=button]")];
      btns[btns.length - 1].click();
      return true;
    }, t);
    if (!opened) { console.log("  row not found (gone already?)"); continue; }
    await sleep(1200);
    const item = await p.evaluate(() => {
      const e = [...document.querySelectorAll("div,li,span")].find(x =>
        x.textContent.trim() === "Delete" && x.getBoundingClientRect().width > 0 && x.getBoundingClientRect().width < 300);
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
    });
    if (!item) { console.log("  Delete item not visible"); await p.screenshot({ path: path.join(SHOTS, `noitem-${i}.png`) }); continue; }
    await p.mouse.click(item.x, item.y);
    await sleep(1800);
    await p.screenshot({ path: path.join(SHOTS, `dlg-${i}.png`) });
    const conf = await p.evaluate(() => {
      const es = [...document.querySelectorAll("button,div[role=button]")].filter(x =>
        /^Delete$/.test(x.textContent.trim()) && x.getBoundingClientRect().width > 0);
      const e = es[es.length - 1];
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2, n: es.length };
    });
    if (conf) { await p.mouse.click(conf.x, conf.y); console.log(`  confirm clicked (of ${conf.n})`); }
    else console.log("  no confirm button found");
    await sleep(3000);
  }
  await p.goto("https://www.tiktok.com/tiktokstudio/content", { waitUntil: "domcontentloaded" });
  await sleep(4500);
  await p.screenshot({ path: path.join(SHOTS, "after-delete.png") });
  const left = await p.evaluate(() => document.body.textContent.match(/clip-00\d|crude flows|20% toll/g));
  console.log("markers remaining:", JSON.stringify(left));
  b.disconnect();
})().catch(e => { console.error("ERR", e.message); process.exit(1); });
