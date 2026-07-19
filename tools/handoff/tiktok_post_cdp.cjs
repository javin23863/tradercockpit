// Post the remaining shorts to TikTok by driving TikTok Studio over CDP (port 9333).
// The cli.py/undetected-chromedriver path is broken; this uses the operator's logged-in session.
const path = require("path");
const puppeteer = require(path.join(__dirname, "..", "..", "studio-kit", "pipeline",
  "generators", "node_modules", "puppeteer"));
const SHOTDIR = path.join(__dirname, "shots"); // temp dirs vanish between sessions — keep receipts repo-local
require("fs").mkdirSync(SHOTDIR, { recursive: true });
const cliVideo = process.argv[2] && path.resolve(process.argv[2]);
const cliCaption = process.argv[3];
if (cliVideo && !cliCaption) throw new Error("usage: node tiktok_post_cdp.cjs <video> <caption>");
const S = cliVideo ? path.dirname(cliVideo) + path.sep :
  "C:\\Users\\MSI\\Desktop\\OpenMontage-Skill\\productions\\video-02-hormuz-v4\\shorts\\";
const sleep = ms => new Promise(r => setTimeout(r, ms));
const clickText = (t) => `(() => { const e=[...document.querySelectorAll('button,div[role=button],span,div')].find(x=>x.textContent.trim()===${JSON.stringify(t)}); if(e){e.click();return true;} return false; })()`;

const CLIPS = cliVideo ? [{ f: path.basename(cliVideo), c: cliCaption }] : [
  { f: "clip-006-segment-1.vertical.mp4",
    c: "Trump just put a 20% toll on every ship through the Strait of Hormuz - and oil ripped 10% in a day. Here's what it means for your portfolio. #oil #hormuz #stockmarket #investing #FinTok" },
  { f: "clip-003-hook-3-so-how-high-can-crude.vertical.mp4",
    c: "How high can oil actually go? Every big desk's number - Goldman, JPMorgan, gov models - on one chart. $100 to $150. None of them models it sitting still. #oil #brentcrude #stockmarket #investing #FinTok" },
  { f: "clip-001-hook-1-is-the-straight-actually-closed-.vertical.mp4",
    c: "Is the Strait of Hormuz actually closed? Wrong question. The right one moves oil - 5 vessels last week vs 130 a day. #oil #hormuz #geopolitics #stockmarket #FinTok" },
  { f: "clip-002-hook-2-because-83-crude-flows-straight.vertical.mp4",
    c: "$83 crude flows straight into producer earnings. Exxon +4%, Chevron +3% on the day. The war-premium rotation, one chart deeper. #oil #energystocks #exxon #investing #FinTok" },
  { f: "clip-004-hook-4-but-the-headline-number-matters.vertical.mp4",
    c: "5 big banks report before the bell. The headline EPS matters less than 3 lines inside: net interest income, trading revenue, credit provisions. #banks #jpmorgan #earnings #stockmarket #FinTok" },
];

(async () => {
  const b = await puppeteer.connect({ browserURL: "http://localhost:9333", defaultViewport: null });
  const pages = await b.pages();
  const p = pages.find(x => (x.url() || "").includes("tiktok")) || pages[pages.length - 1];
  await p.bringToFront();

  for (const [i, clip] of CLIPS.entries()) {
    console.log(`\n--- [${i + 1}/${CLIPS.length}] ${clip.f}`);
    await p.goto("https://www.tiktok.com/tiktokstudio/upload", { waitUntil: "domcontentloaded" });
    await sleep(4000);
    const [fc] = await Promise.all([
      p.waitForFileChooser({ timeout: 15000 }),
      p.evaluate(new Function("return " + clickText("Select video"))),
    ]);
    await fc.accept([S + clip.f]);
    console.log("  uploaded, processing...");
    await sleep(16000);
    // dismiss any modals/promos
    for (const t of ["Cancel", "Got it"]) {
      await p.evaluate(new Function("return " + clickText(t))).catch(() => {});
      await sleep(600);
    }
    // caption: TikTok prefills the FILENAME, and does it LATE (after the editor mounts) —
    // clearing once races the prefill and leaves "clip-00N....vertical" in the caption.
    // Clear-verify-retry until the box is actually empty, then type, then verify before Post.
    const focusCe = () => p.evaluate(() => {
      const ce = [...document.querySelectorAll('div[contenteditable="true"]')].find((node) => {
        const rect = node.getBoundingClientRect();
        const style = getComputedStyle(node);
        return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
      });
      if (!ce) return false;
      ce.scrollIntoView({ block: "center" }); ce.focus();
      return true;
    });
    if (!await focusCe()) { console.log("  !! caption editor not found"); continue; }
    let cleared = false;
    for (let a = 0; a < 6 && !cleared; a++) {
      await sleep(1500);                       // let any late prefill land
      await focusCe();
      await p.keyboard.down("Control"); await p.keyboard.press("KeyA"); await p.keyboard.up("Control");
      await p.keyboard.press("Backspace");
      await sleep(600);
      const txt = await p.evaluate(() => {
        const ce = [...document.querySelectorAll('div[contenteditable="true"]')].find((node) => node.getBoundingClientRect().width > 0);
        return ce?.textContent || "";
      });
      cleared = txt.trim() === "";
      console.log(`  clear attempt ${a + 1}: ${cleared ? "empty" : JSON.stringify(txt.slice(0, 30))}`);
    }
    if (!cleared) { console.log("  !! could not clear caption, SKIPPING (not posting)"); continue; }
    await p.keyboard.type(clip.c, { delay: 12 });
    await sleep(1200);
    await p.keyboard.press("Escape");   // kill hashtag dropdown
    await p.keyboard.press("Tab");      // commit editor state through its blur handler
    await sleep(1800);
    const cap = await p.evaluate(() => {
      const editors = [...document.querySelectorAll('div[contenteditable="true"]')];
      return editors.find((node) => node.getBoundingClientRect().width > 0)?.textContent || "";
    });
    if (!cap.startsWith(clip.c.slice(0, 25))) {
      console.log("  !! caption mismatch, NOT posting:", JSON.stringify(cap.slice(0, 40)));
      continue;
    }
    console.log("  caption ok:", cap.length, "chars");
    const posted = await p.evaluate(() => {
      const btn = [...document.querySelectorAll("button")].find(e => e.textContent.trim() === "Post" && !e.disabled);
      if (btn) { btn.click(); return true; } return false;
    });
    console.log("  Post clicked:", posted);
    await sleep(9000);
    await p.screenshot({ path: path.join(SHOTDIR, `tt-${i + 1}.png`) });
    console.log("  url now:", p.url());
    if (p.url().includes("tiktokstudio/content")) {
      const receipt = await p.evaluate(() => {
        const link = document.querySelector('a[href*="/video/"]');
        if (!link) return null;
        let row = link;
        while (row && row !== document.body) {
          if (/\b(Everyone|Only me|Friends)\b/.test(row.innerText || "") &&
              row.querySelectorAll('a[href*="/video/"]').length === 1) break;
          row = row.parentElement;
        }
        return { title: link.textContent.trim(), url: link.href, state: row?.innerText || "" };
      });
      console.log("  public receipt:", JSON.stringify(receipt));
      if (receipt?.title === clip.f.replace(/\.mp4$/i, "")) {
        console.log("  !! TikTok published the filename instead of the approved caption; do not silently report caption success");
      }
    }
  }
  b.disconnect();
  console.log("\nDONE tiktok batch");
})().catch(e => { console.error("ERR", e.message); process.exit(1); });
