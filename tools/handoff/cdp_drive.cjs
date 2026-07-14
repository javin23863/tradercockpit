#!/usr/bin/env node
// Drive the debugged Chrome (port 9333) via puppeteer. Reliable DOM/coord control.
// Subcommands:
//   shot [urlSubstr] [out]         screenshot matching page (default match 'instagram')
//   nav  <urlSubstr> <url>         navigate matching page to url
//   click <urlSubstr> <x> <y>      mouse click at viewport coords
//   type  <urlSubstr> <text>       type text into focused element
//   fill  <urlSubstr> <sel> <text> set an input/textarea by selector (react-safe) + fire events
//   press <urlSubstr> <key>        press a key (e.g. Enter, Tab)
//   info                           list pages (url + title)
const path = require("path");
const puppeteer = require(path.join("C:", "Users", "MSI", "Desktop", "OpenMontage-Skill",
  "studio-kit", "pipeline", "generators", "node_modules", "puppeteer"));
const SHOT = path.join(__dirname, "shots", "screen.png"); // temp dirs vanish between sessions
require("fs").mkdirSync(path.dirname(SHOT), { recursive: true });

(async () => {
  const [cmd, sub, a, b] = process.argv.slice(2);
  const browser = await puppeteer.connect({ browserURL: "http://localhost:9333", defaultViewport: null });
  const pages = await browser.pages();
  async function pick(substr) {
    for (const p of pages) { try { if ((p.url() || "").includes(substr || "instagram")) return p; } catch (e) {} }
    return pages[pages.length - 1];
  }
  if (cmd === "info") {
    for (const p of pages) console.log(JSON.stringify({ url: p.url(), title: await p.title().catch(() => "") }));
  } else if (cmd === "shot") {
    const p = await pick(sub); const out = b || a || SHOT;
    await p.bringToFront().catch(() => {});
    await p.screenshot({ path: out });
    console.log("shot:", p.url(), "->", out);
  } else if (cmd === "nav") {
    const p = await pick(sub); await p.goto(a, { waitUntil: "domcontentloaded" }); console.log("nav ->", p.url());
  } else if (cmd === "click") {
    const p = await pick(sub); await p.mouse.click(Number(a), Number(b)); console.log("click", a, b, "on", p.url());
  } else if (cmd === "type") {
    const p = await pick(sub); await p.keyboard.type(a, { delay: 25 }); console.log("typed len", a.length);
  } else if (cmd === "press") {
    const p = await pick(sub); await p.keyboard.press(a); console.log("press", a);
  } else if (cmd === "eval") {
    const p = await pick(sub);
    const r = await p.evaluate(new Function(a));
    console.log("eval:", JSON.stringify(r));
  } else if (cmd === "fill") {
    const p = await pick(sub);
    const n = await p.$$eval(a, (els, val) => {
      const el = els[0]; if (!el) return 0;
      const proto = el.tagName === "TEXTAREA" ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(proto, "value").set;
      el.focus(); setter.call(el, val);
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
      return 1;
    }, b);
    console.log("fill", a, "matched", n);
  }
  browser.disconnect();
})().catch(e => { console.error("ERR", e.message); process.exit(1); });
