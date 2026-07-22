#!/usr/bin/env node
// Read-only TikTok watchlist collector for engagement.py. Visits each handle's
// public profile in the operator's logged-in debug Chrome (port 9333), takes the
// newest videos from the grid, opens each to read like/comment counts. Never
// clicks a mutating control — navigation and DOM reads only.
//
// Usage: node tiktok_watchlist_cdp.cjs @handle1 @handle2 ...
//        node tiktok_watchlist_cdp.cjs --selftest
//
// TikTok video ids are snowflakes: id >> 32 = unix seconds. That gives every
// post a real ISO timestamp, so engagement.py can rank these honestly (unlike
// the Studio "Jul 18" labels, which score 0 by design).

const path = require("path");
const puppeteer = require(path.join(
  __dirname, "..", "studio-kit", "pipeline", "generators", "node_modules", "puppeteer"
));

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const VIDEOS_PER_ACCOUNT = 3;

const idToIso = (id) => new Date(Number(BigInt(id) >> 32n) * 1000).toISOString();

const parseCount = (text) => {
  // "12.3K" / "1.2M" / "845" -> number
  const m = String(text || "").trim().match(/^([\d.,]+)\s*([KMB])?$/i);
  if (!m) return null;
  const mult = { K: 1e3, M: 1e6, B: 1e9 }[(m[2] || "").toUpperCase()] || 1;
  return Math.round(parseFloat(m[1].replaceAll(",", "")) * mult);
};

function selftest() {
  // snowflake sanity: a real 2025 video id must decode into a plausible year
  const year = new Date(idToIso("7562239082818997526")).getUTCFullYear();
  if (year < 2019 || year > 2030) throw new Error(`snowflake decode broken: ${year}`);
  if (parseCount("12.3K") !== 12300) throw new Error("parseCount K broken");
  if (parseCount("1.2M") !== 1200000) throw new Error("parseCount M broken");
  if (parseCount("845") !== 845) throw new Error("parseCount plain broken");
  if (parseCount("") !== null) throw new Error("parseCount empty broken");
  console.log("selftest ok");
}

(async () => {
  const args = process.argv.slice(2);
  if (args.includes("--selftest")) { selftest(); return; }
  const handles = args.filter((a) => a.startsWith("@"));
  if (!handles.length) throw new Error("no @handles given");

  const browser = await puppeteer.connect({ browserURL: "http://127.0.0.1:9333", defaultViewport: null });
  const page = await browser.newPage();
  const posts = [];
  const errors = [];

  for (const handle of handles) {
    try {
      await page.goto(`https://www.tiktok.com/${handle}`, { waitUntil: "domcontentloaded" });
      await sleep(3500);
      const grid = await page.evaluate(() => {
        const anchors = [...document.querySelectorAll('a[href*="/video/"]')];
        return anchors.map((a) => ({
          url: a.href.split("?")[0],
          id: new URL(a.href).pathname.split("/").filter(Boolean).at(-1),
          title: (a.closest("[data-e2e]")?.querySelector("img")?.alt || a.innerText || "").trim().slice(0, 200),
        })).filter((v) => /^\d{15,}$/.test(v.id));
      });
      if (!grid.length) {
        errors.push(`${handle}: no videos found on profile (page blocked, empty account, or layout changed)`);
        continue;
      }
      // newest first by snowflake id; grid order can include pinned posts
      const newest = [...new Map(grid.map((v) => [v.id, v])).values()]
        .sort((a, b) => (BigInt(b.id) > BigInt(a.id) ? 1 : -1))
        .slice(0, VIDEOS_PER_ACCOUNT);
      for (const video of newest) {
        try {
          await page.goto(video.url, { waitUntil: "domcontentloaded" });
          await sleep(3000);
          const counts = await page.evaluate(() => ({
            // ponytail: data-e2e selectors, TikTok's own test hooks — most stable
            // scrape surface available; if they vanish, counts go null and the
            // post scores 0 visibly rather than lying.
            likes: document.querySelector('[data-e2e="like-count"]')?.innerText ?? null,
            comments: document.querySelector('[data-e2e="comment-count"]')?.innerText ?? null,
            desc: document.querySelector('[data-e2e="browse-video-desc"]')?.innerText ?? "",
          }));
          posts.push({
            platform: "tiktok",
            account: handle,
            id: video.id,
            title: (counts.desc || video.title).slice(0, 200),
            description: (counts.desc || "").slice(0, 400),
            createdAt: idToIso(video.id),
            url: video.url,
            views: null,
            likes: parseCount(counts.likes),
            comments: parseCount(counts.comments),
          });
        } catch (err) {
          errors.push(`${handle} ${video.id}: ${err.message}`);
        }
      }
    } catch (err) {
      errors.push(`${handle}: ${err.message}`);
    }
  }

  await page.close();
  await browser.disconnect();
  process.stdout.write(JSON.stringify({
    schema: "tradercockpit-tiktok-watchlist/v1",
    fetchedAt: new Date().toISOString(),
    status: "ready",
    posts,
    errors,
  }));
})().catch((error) => {
  process.stdout.write(JSON.stringify({
    schema: "tradercockpit-tiktok-watchlist/v1",
    fetchedAt: new Date().toISOString(),
    status: "unavailable",
    error: error.message,
    posts: [],
    errors: [],
  }));
  process.exitCode = 2;
});
