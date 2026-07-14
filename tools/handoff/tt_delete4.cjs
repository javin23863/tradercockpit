// TikTok Studio delete — full trusted-hover chain.
// Scar: element.click() opens the row menu but leaves it invisible/unpositioned, so
// coordinate clicks on its items miss. The menu only materializes under a real hover:
// hover row -> hover "..." -> click it -> hover Delete -> click -> confirm.
const path = require("path");
const puppeteer = require(path.join("C:", "Users", "MSI", "Desktop", "OpenMontage-Skill",
  "studio-kit", "pipeline", "generators", "node_modules", "puppeteer"));
const SHOTS = path.join(__dirname, "shots");
require("fs").mkdirSync(SHOTS, { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));

// pass row-title substrings as argv, else this default set
const TARGETS = process.argv.slice(2).length ? process.argv.slice(2) : [
  "clip-004-hook-4",
  "clip-002-hook-2",
  "clip-001-hook-1",
  "How high can oil actually go",
  "clip-006-segment-1",
];

(async () => {
  const b = await puppeteer.connect({ browserURL: "http://localhost:9333", defaultViewport: null });
  const pages = await b.pages();
  const p = pages.find(x => (x.url() || "").includes("tiktok")) || pages[pages.length - 1];
  await p.bringToFront();

  for (const [i, t] of TARGETS.entries()) {
    console.log(`--- ${t}`);
    await p.goto("https://www.tiktok.com/tiktokstudio/content", { waitUntil: "domcontentloaded" });
    await sleep(5000);
    // the row-actions column sits off-screen right at 100% — zoom out so it's clickable
    await p.evaluate(() => { document.body.style.zoom = "0.6"; });
    await sleep(800);
    const box = await p.evaluate(m => {
      const row = [...document.querySelectorAll("tr,div")].filter(d =>
        d.textContent.includes(m) && d.querySelector("button") && d.textContent.length < 600).pop();
      if (!row) return null;
      const r = row.getBoundingClientRect();
      const btns = [...row.querySelectorAll("button,[role=button]")];
      const bb = btns[btns.length - 1].getBoundingClientRect();
      return { row: { x: r.x + 200, y: r.y + r.height / 2 }, btn: { x: bb.x + bb.width / 2, y: bb.y + bb.height / 2 } };
    }, t);
    if (!box) { console.log("  row gone"); continue; }
    await p.mouse.move(box.row.x, box.row.y); await sleep(700);   // reveal row actions
    await p.mouse.move(box.btn.x, box.btn.y); await sleep(500);   // hover the "..."
    await p.mouse.click(box.btn.x, box.btn.y); await sleep(1500); // open menu (trusted)
    const item = await p.evaluate(() => {
      const e = [...document.querySelectorAll("div,li,span")].find(x =>
        x.textContent.trim() === "Delete" && x.getBoundingClientRect().width > 0 && x.getBoundingClientRect().width < 300);
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2, vis: r.width + "x" + r.height + "@" + Math.round(r.x) + "," + Math.round(r.y) };
    });
    console.log("  menu item:", item ? item.vis : "NOT FOUND");
    if (!item) { await p.screenshot({ path: path.join(SHOTS, `m-${i}.png`) }); continue; }
    await p.mouse.move(item.x, item.y); await sleep(400);
    await p.mouse.click(item.x, item.y); await sleep(2000);
    await p.screenshot({ path: path.join(SHOTS, `c-${i}.png`) });
    const conf = await p.evaluate(() => {
      const es = [...document.querySelectorAll("button,div[role=button]")].filter(x =>
        /^(Delete|Confirm|Yes)$/i.test(x.textContent.trim()) && x.getBoundingClientRect().width > 40);
      const e = es[es.length - 1];
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2, t: e.textContent.trim() };
    });
    if (conf) {
      await p.mouse.move(conf.x, conf.y); await sleep(300);
      await p.mouse.click(conf.x, conf.y);
      console.log("  confirmed via:", conf.t);
    } else console.log("  no confirm dialog");
    await sleep(3500);
  }
  await p.goto("https://www.tiktok.com/tiktokstudio/content", { waitUntil: "domcontentloaded" });
  await sleep(5000);
  await p.screenshot({ path: path.join(SHOTS, "after-delete.png") });
  const left = await p.evaluate(() => [...new Set((document.body.textContent.match(/clip-00\d|crude flows|20% toll/g) || []))]);
  console.log("markers remaining:", JSON.stringify(left));
  b.disconnect();
})().catch(e => { console.error("ERR", e.message); process.exit(1); });
