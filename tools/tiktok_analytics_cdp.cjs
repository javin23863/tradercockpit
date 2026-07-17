#!/usr/bin/env node
// Read-only TikTok Studio metrics collector. Requires the operator's logged-in
// debug Chrome on port 9333; prints JSON and never clicks a mutating control.

const path = require("path");
const puppeteer = require(path.join(
  __dirname, "..", "studio-kit", "pipeline", "generators", "node_modules", "puppeteer"
));

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

(async () => {
  const browser = await puppeteer.connect({ browserURL: "http://127.0.0.1:9333", defaultViewport: null });
  const pages = await browser.pages();
  let page = pages.find((candidate) => candidate.url().includes("tiktokstudio/content"));
  if (!page) {
    page = pages.find((candidate) => candidate.url().includes("tiktok.com"));
    if (!page) throw new Error("logged-in TikTok Studio page not found");
    await page.goto("https://www.tiktok.com/tiktokstudio/content", { waitUntil: "domcontentloaded" });
    await sleep(3000);
  }

  const posts = await page.evaluate(() => {
    const anchors = [...document.querySelectorAll('a[href*="/video/"]')];
    return anchors.map((anchor) => {
      let row = anchor;
      while (row && row !== document.body) {
        const links = row.querySelectorAll?.('a[href*="/video/"]').length ?? 0;
        const text = row.innerText || "";
        if (links === 1 && /\b(Everyone|Only me|Friends)\b/.test(text)) break;
        row = row.parentElement;
      }
      const lines = (row?.innerText || anchor.innerText || "")
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean);
      const counts = lines
        .filter((line) => /^\d[\d,]*$/.test(line))
        .map((line) => Number(line.replaceAll(",", "")));
      return {
        id: new URL(anchor.href).pathname.split("/").filter(Boolean).at(-1),
        url: anchor.href,
        title: (anchor.innerText || "").trim(),
        createdLabel: lines.find((line) => /^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b/.test(line)) || null,
        privacy: lines.find((line) => ["Everyone", "Only me", "Friends"].includes(line)) || null,
        reviewStatus: lines.find((line) => /review/i.test(line)) || null,
        views: counts.at(-3) ?? null,
        likes: counts.at(-2) ?? null,
        comments: counts.at(-1) ?? null,
      };
    });
  });

  await browser.disconnect();
  process.stdout.write(JSON.stringify({
    schema: "tradercockpit-tiktok-studio/v1",
    fetchedAt: new Date().toISOString(),
    account: "@trader.cockpit",
    status: "ready",
    posts,
  }));
})().catch((error) => {
  process.stdout.write(JSON.stringify({
    schema: "tradercockpit-tiktok-studio/v1",
    fetchedAt: new Date().toISOString(),
    account: "@trader.cockpit",
    status: "unavailable",
    error: error.message,
    posts: [],
  }));
  process.exitCode = 2;
});
