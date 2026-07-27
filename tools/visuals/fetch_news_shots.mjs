#!/usr/bin/env node
// fetch_news_shots.mjs — news-article / tweet screenshot lane for format v2.
//
// For each source: load the page headless (Edge via TraderCockpit's existing
// Puppeteer dependency), step through
// "highlight stages" (each stage red-boxes the exact sentence the VO reads and
// scrolls it into the center of a normal 16:9 browser viewport), screenshot each
// stage, then ffmpeg the stage PNGs into one clip. The viewport is the frame:
// never substitute a tall full-page capture or a tight paragraph crop.
//
// sources.json (array):
//   [{ "out": "03a-cnbc", "url": "https://www.cnbc.com/...",
//      "highlights": ["exact sentence text", "another sentence"],
//      "holdSec": 8 }]
// Tweet support: "url": "tweet:1944000000000000000" -> platform.twitter.com embed.
//
// Usage:
//   node tools/visuals/fetch_news_shots.mjs <sources.json> <prod-dir>
//   node tools/visuals/fetch_news_shots.mjs --dry-run <sources.json>

import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import puppeteer from './puppeteer.mjs'

const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
const FRAME_W = 1920
const FRAME_H = 1080
const BADGE_RAIL = 140  // top rail, only used when no real masthead survives
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// Consent-button text. Substring, NOT anchored: AP's button reads "I Accept All" and the
// old /^accept all$/ matched nothing, so the modal shipped centre-frame (defect 2026-07-27).
const CONSENT_RE = /(accept|allow)\s*all|i\s*accept|i\s*agree|^(accept|agree|got it|continue|ok)$/i

// Masthead candidates. Tag-based lookup is not enough: AP renders <bsp-header class="Page-header">,
// so querySelector('header') returned null and the outlet's own identity was hidden as clutter.
const MASTHEAD_SEL = 'header, [role="banner"], [class*="masthead" i], [class*="page-header" i],'
  + ' [class*="site-header" i], [class*="siteHeader" i], [id*="masthead" i], [id*="site-header" i]'

// badge == null means the publication's OWN masthead is pinned in frame and is the
// provenance the viewer reads. Only when no masthead could be kept do we draw our own
// rail (fallback to operator ruling 2026-07-14). Drawing a label over a page whose real
// masthead we cut off is what shipped in daily-2026-07-27 — never again.
function newsFilter(badge) {
  // Source cards are evidence, not background texture. Keep every pixel, never zoom
  // into text after capture, and fill the frame — no side letterbox.
  // white world per operator ruling 2026-07-17: news cards share the white chart background
  if (!badge) return `scale=${FRAME_W}:${FRAME_H},fps=30,format=yuv420p`
  // no masthead: capture is FRAME_H-BADGE_RAIL tall, rail carries the drawn source band
  const safe = badge.replace(/[\\':,]/g, ' ')
  return `scale=${FRAME_W}:${FRAME_H - BADGE_RAIL},`
    + `pad=${FRAME_W}:${FRAME_H}:0:${BADGE_RAIL}:color=0xFFFFFF,fps=30,`
    + `drawtext=text='${safe}':fontfile='C\\:/Windows/Fonts/arialbd.ttf'`
    + ':fontsize=34:fontcolor=white:box=1:boxcolor=0xE8272C@0.92:boxborderw=14:x=40:y=32'
    + ',format=yuv420p'
}

function kenBurns(png, mp4, dur, badge) {
  const vf = newsFilter(badge)
  execFileSync('ffmpeg', ['-y', '-loop', '1', '-i', png, '-t', dur.toFixed(2),
    '-vf', vf, '-c:v', 'h264_nvenc', '-cq', '19', '-preset', 'p5', mp4], { stdio: 'pipe' })
}

function concatClips(clips, out) {
  const lst = out + '.txt'
  // absolute paths: ffmpeg concat resolves `file` entries relative to the list
  // file's own dir (visuals/), but clips live in news-work/ — relative would double up
  fs.writeFileSync(lst, clips.map((c) => `file '${path.resolve(c).replace(/\\/g, '/')}'\n`).join(''))
  execFileSync('ffmpeg', ['-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', out], { stdio: 'pipe' })
  fs.unlinkSync(lst)
}

// Kill consent banners + ads/sidebars. Without this the shots carry cookie bars and
// "Subscribe to Newsletter" boxes straight into the video (video-02 v2 defect 2026-07-14).
// -> true if the publication's own masthead is pinned in frame (so no drawn badge is needed)
async function declutter(page) {
  // consent: click every button whose text READS like consent. Substring, not anchored —
  // AP's button says "I Accept All" and the old /^accept all$/ matched nothing, so the
  // cookie modal sat dead centre in both AP clips of daily-2026-07-27.
  await page.evaluate((src) => {
    const re = new RegExp(src, 'i')
    for (const b of document.querySelectorAll('button, a[role="button"], [role="button"]')) {
      if (re.test((b.textContent || '').trim())) b.click()
    }
  }, CONSENT_RE.source)
  await sleep(600)
  // Hide iframes (ads) + floating overlays. Two rules keep this safe without a height guess:
  // never hide the element that CONTAINS the article (blank-page defect 2026-07-14), and
  // never hide the site's own masthead — hiding `header`/`nav` is exactly what cut AP's
  // masthead out of frame and left only the badge we draw ourselves (defect 2026-07-27).
  const masthead = await page.evaluate((sel) => {
    for (const el of document.querySelectorAll('iframe')) el.style.display = 'none'
    const main = document.querySelector('main, article')
    // Find the masthead by SHAPE, not by tag: AP's is <bsp-header class="Page-header">,
    // so `document.querySelector('header')` found nothing and the sweep hid the real one
    // (it is sticky at 56px, under the old `< 400` cut). Banner = near the top of the
    // document, spans most of the width, short. The tall one is an ad leaderboard.
    const cands = []
    for (const el of document.querySelectorAll(sel)) {
      const r = el.getBoundingClientRect()
      const top = r.top + scrollY
      // within the first screenful, not 260px: AP stacks a 270px ad leaderboard ABOVE
      // its masthead, which put the real banner out of a tighter cut
      if (top > innerHeight * 0.8 || r.width < innerWidth * 0.6) continue
      if (r.height < 24 || r.height > 220) continue  // taller = ad leaderboard, not a banner
      if (main && el.contains(main)) continue
      cands.push({ el, top, sticky: /fixed|sticky/.test(getComputedStyle(el).position) })
    }
    // a banner the site itself pins survives scrolling by design — prefer it, else topmost
    cands.sort((a, b) => (b.sticky - a.sticky) || (a.top - b.top))
    const own = cands.length ? cands[0].el : null
    // Pin the real masthead so the outlet is legible in EVERY stage, not just the
    // unscrolled first one — highlight stages scroll deep into the article.
    if (!own) return false
    own.dataset.tcMasthead = '1'  // the overlay backstop below must not flag our own pin
    Object.assign(own.style, {
      position: 'fixed', top: '0', left: '0', right: '0', zIndex: '2147483646',
    })
    const bg = getComputedStyle(own).backgroundColor
    if (!bg || bg === 'transparent' || /rgba\(0, 0, 0, 0\)/.test(bg)) own.style.background = '#fff'
    return true
  }, MASTHEAD_SEL)
  await sleep(300)
  await clearOverlays(page)
  return masthead
}

// Hide floating clutter, then assert nothing large is still over the page.
// MUST run immediately before every screenshot, not once at load: AP's floating video
// widget lazy-loads on scroll, so a check at load time passed while the widget was still
// absent and it rode into the frame anyway (defect 2026-07-27, second pass).
async function clearOverlays(page) {
  // Sweep, settle, re-check — up to three passes. AP re-inserts its floating video widget
  // after the first sweep, so a single sweep-then-assert races the page and throws on an
  // overlay that a second pass would have cleared.
  let blocker = null
  for (let pass = 0; pass < 3; pass++) {
    blocker = await sweepOnce(page)
    if (!blocker) return
    await sleep(400)
  }
  throw new Error(`overlay still covering the page after declutter: ${blocker}`)
}

async function sweepOnce(page) {
  await page.evaluate(() => {
    const main = document.querySelector('main, article')
    const own = document.querySelector('[data-tc-masthead]')
    // Sweep EVERY tag, not a five-tag allowlist: AP's widget is a custom element and rode
    // past `div, section, aside, header, nav` — the same allowlist blindness that made
    // querySelector('header') miss the masthead.
    for (const el of document.querySelectorAll('*')) {
      if (el === document.body || el === document.documentElement) continue
      if (own && (el === own || own.contains(el))) continue
      if (main && el.contains(main)) continue
      const cs = getComputedStyle(el)
      if (cs.position === 'fixed' || cs.position === 'sticky') el.style.display = 'none'
      else if (el.tagName === 'IFRAME') el.style.display = 'none'
    }
  })
  return page.evaluate(() => {
    const area = innerWidth * innerHeight
    const own = document.querySelector('[data-tc-masthead]')
    for (const el of document.querySelectorAll('*')) {
      if (own && (el === own || own.contains(el))) continue
      const cs = getComputedStyle(el)
      if (cs.position !== 'fixed' && cs.position !== 'sticky') continue
      if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') continue
      const r = el.getBoundingClientRect()
      // 1%, not 5%: AP's floating widget was ~2% of the frame and sailed under the old cut
      if (r.width * r.height <= area * 0.01) continue
      const cls = (typeof el.className === 'string' ? el.className : '').slice(0, 40)
      return `${el.tagName.toLowerCase()}${cls ? '.' + cls : ''} ${Math.round(r.width)}x${Math.round(r.height)}`
    }
    return null
  })
}

// Highlight the paragraph containing `needle` (whitespace-normalized,
// case-insensitive) and center it in the browser viewport.
// ponytail: paragraph-level, not text-node — article sentences split across inline links.
async function highlight(page, needle) {
  return page.evaluate((needle) => {
    const norm = (s) => s.replace(/\s+/g, ' ').trim().toLowerCase()
    const n = norm(needle)
    let best = null
    let bestArea = Infinity
    for (const el of document.querySelectorAll('p, li, blockquote, h1, h2, h3, figcaption, tr, td')) {
      if (el.children.length > 8) continue // big containers — keep the box tight
      if (!norm(el.textContent || '').includes(n)) continue
      const r = el.getBoundingClientRect()
      if (r.width < 10 || r.height < 10) continue // hidden element — keep searching
      const area = r.width * r.height
      if (area < bestArea) { best = el; bestArea = area }
    }
    if (!best) {
      const selection = window.getSelection()
      selection.removeAllRanges()
      if (!window.find(needle, false, false, true, false, false, false)) return null
      const range = selection.rangeCount ? selection.getRangeAt(0) : null
      if (!range) return null
      const r = range.getBoundingClientRect()
      const docX = r.x + window.scrollX
      const docY = r.y + window.scrollY
      window.scrollTo(0, Math.max(0, docY - window.innerHeight / 2 + r.height / 2))
      const marker = document.createElement('div')
      marker.className = 'tc-highlight-overlay'
      Object.assign(marker.style, {
        position: 'absolute', left: `${docX - 4}px`, top: `${docY - 4}px`,
        width: `${r.width + 8}px`, height: `${r.height + 8}px`,
        outline: '3px solid #E8272C', background: 'rgba(232,39,44,0.10)',
        pointerEvents: 'none', zIndex: '2147483647',
      })
      document.body.appendChild(marker)
      selection.removeAllRanges()
      return true
    }
    best.style.outline = '3px solid #E8272C'
    best.style.outlineOffset = '3px'
    best.style.background = 'rgba(232,39,44,0.10)'
    best.scrollIntoView({ block: 'center' })
    return true
  }, needle)
}

function screenshotOptions(png) {
  return { path: png }
}

async function clearHighlights(page) {
  await page.evaluate(() => {
    for (const el of document.querySelectorAll('.tc-highlight-overlay')) el.remove()
    window.getSelection()?.removeAllRanges()
    for (const el of document.querySelectorAll('[style*="outline"]')) {
      el.style.outline = ''; el.style.background = ''
    }
  })
}

// `url` is the RESOLVED url (tweet: sources rewrite to a platform.twitter.com embed,
// which `new URL(src.url)` cannot parse).
function badgeFor(src, url = src.url) {
  return src.label
    ?? new URL(url).hostname.replace(/^(www|platform)\./, '').toUpperCase()
      + (src.dated ? `  ${src.dated}` : '')
}

// Operator ruling 2026-07-21 (issued approving daily-2026-07-21): on-screen news shots come
// from major reputable outlets ONLY — no fool.com / retail-stock-blog tier. Official primary
// sources (regulators, company releases, wires) are always allowed.
const APPROVED_SHOT_HOSTS = [
  'nytimes.com', 'bloomberg.com', 'bnnbloomberg.ca', 'reuters.com', 'apnews.com',
  'aljazeera.com', 'wsj.com', 'ft.com', 'cnbc.com', 'npr.org', 'bbc.com', 'bbc.co.uk',
  'usnews.com', 'washingtonpost.com', 'cnn.com', 'abcnews.go.com', 'nbcnews.com',
  'federalreserve.gov', 'eia.gov', 'sec.gov', 'prnewswire.com', 'businesswire.com',
  'ir.supermicro.com', 'gevernova.com',
]
const hostAllowed = (url) => {
  const h = new URL(url).hostname.replace(/^www\./, '')
  return APPROVED_SHOT_HOSTS.some((a) => h === a || h.endsWith('.' + a))
}

async function run(sourcesPath, prodDir, dry, reuse) {
  const sources = JSON.parse(fs.readFileSync(sourcesPath, 'utf8'))
  sources.forEach((s, i) => {
    for (const k of ['out', 'url']) if (!s[k]) throw new Error(`sources[${i}] missing "${k}"`)
    if (!s.url.startsWith('tweet:') && !hostAllowed(s.url)) {
      throw new Error(`sources[${i}] "${s.out}": host not on APPROVED_SHOT_HOSTS `
        + `(operator ruling 2026-07-21 — majors only, no off-brand outlets): ${s.url}`)
    }
  })
  if (dry) { console.log(`DRY RUN OK — ${sources.length} sources validated`); return }

  const visuals = path.join(prodDir, 'visuals')
  const work = path.join(prodDir, 'news-work')
  fs.mkdirSync(visuals, { recursive: true })
  fs.mkdirSync(work, { recursive: true })

  const nStages = (src) => (src.highlights?.length ? src.highlights.length : 1)
  const cachedPngs = (src) => [...Array(nStages(src))].map((_, i) => path.join(work, `${src.out}-s${i}.png`))
  // --reuse-png: re-render mp4s from cached PNGs (fixed filter, config badges) — no fetch, deterministic.
  const needBrowser = sources.some((src) => {
    if (fs.existsSync(path.join(visuals, `${src.out}.mp4`))) return false
    if (!reuse) return true
    return !cachedPngs(src).every((p) => fs.existsSync(p))
  })

  const launch = () => puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--window-size=1920,1080', '--disable-blink-features=AutomationControlled'],
    defaultViewport: { width: FRAME_W, height: FRAME_H, deviceScaleFactor: 2 },
  })
  let browser = needBrowser ? await launch() : null
  // Edge intermittently answers newPage() with "Target.createTarget: Session with given id
  // not found" on the source AFTER a heavy page. One relaunch clears it; without this the
  // whole run dies partway and the lane has to be driven by hand.
  const newPage = async () => {
    try {
      return await browser.newPage()
    } catch (e) {
      console.log(`  [warn] browser target lost (${e.message.slice(0, 60)}) — relaunching`)
      try { await browser.close() } catch { /* already dead */ }
      browser = await launch()
      return browser.newPage()
    }
  }

  try {
    for (const src of sources) {
      const outMp4 = path.join(visuals, `${src.out}.mp4`)
      if (fs.existsSync(outMp4)) { console.log(`[${src.out}] exists, skip`); continue }
      if (reuse && cachedPngs(src).every((p) => fs.existsSync(p))) {
        console.log(`[${src.out}] reuse cached PNGs`)
        // the capture receipt records whether that PNG already carries a real masthead;
        // re-badging one that does would stack our label on the outlet's own header
        const receipt = path.join(work, `${src.out}-capture.json`)
        const badge = fs.existsSync(receipt)
          ? JSON.parse(fs.readFileSync(receipt, 'utf8')).badge
          : badgeFor(src)
        const clips = cachedPngs(src).map((png, i) => {
          const clip = path.join(work, `${src.out}-s${i}.mp4`)
          kenBurns(png, clip, src.holdSec ?? 8, badge)
          return clip
        })
        concatClips(clips, outMp4)
        console.log(`  -> ${outMp4}`)
        continue
      }
      const url = src.url.startsWith('tweet:')
        ? `https://platform.twitter.com/embed/Tweet.html?id=${src.url.slice(6)}&theme=dark`
        : src.url
      console.log(`[${src.out}] ${url}`)
      const page = await newPage()
      await page.setUserAgent(UA)
      try {
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 45_000 })
      } catch {
        console.log('  [warn] networkidle timeout — proceeding with whatever loaded')
      }
      await sleep(2500)
      const masthead = await declutter(page)
      // No real masthead survived -> shorten the viewport so the drawn badge rail is
      // added, not scaled into. With a masthead the page fills all 1080 rows.
      if (!masthead) {
        console.log(`  [warn] no masthead kept — falling back to a drawn source badge`)
        await page.setViewport({ width: FRAME_W, height: FRAME_H - BADGE_RAIL, deviceScaleFactor: 2 })
      }
      await sleep(500)
      // badge = outlet + optional date; override with src.label in sources.json.
      // null when the publication's own masthead is in frame — that IS the provenance.
      const badge = masthead ? null : badgeFor(src)
      fs.writeFileSync(path.join(work, `${src.out}-capture.json`),
        JSON.stringify({ out: src.out, url, masthead, badge }, null, 2))

      const hold = src.holdSec ?? 8
      const clips = []
      const stages = src.highlights?.length ? src.highlights : [null]
      for (let i = 0; i < stages.length; i++) {
        await clearHighlights(page)
        if (stages[i]) {
          // A source card whose declared sentence is not on it is not a receipt for the
          // claim it sits under. daily-2026-07-27 shipped one as a warning — now it stops.
          if (!await highlight(page, stages[i])) {
            throw new Error(`[${src.out}] highlight not found on the page: "${stages[i]}"`)
          }
          await sleep(600)
        }
        // re-sweep AFTER the scroll: lazy-loaded floaters only appear once scrolled into
        const png = path.join(work, `${src.out}-s${i}.png`)
        await clearOverlays(page)
        await page.screenshot(screenshotOptions(png))
        const clip = path.join(work, `${src.out}-s${i}.mp4`)
        kenBurns(png, clip, hold, badge)
        clips.push(clip)
      }
      await page.close()
      concatClips(clips, outMp4)
      console.log(`  -> ${outMp4}`)
    }
  } finally {
    if (browser) await browser.close()
  }
  console.log('\nDONE')
}

const args = process.argv.slice(2)
if (args.includes('--selftest')) {
  for (const vf of [newsFilter('SOURCE  JULY 15'), newsFilter(null)]) {
    if (vf.includes('crop=') || vf.includes('zoompan=')) {
      throw new Error(`news filter is not contain-only: ${vf}`)
    }
  }
  // masthead in frame -> full-bleed, no drawn band and no white letterbox
  const bare = newsFilter(null)
  if (!bare.includes(`scale=${FRAME_W}:${FRAME_H}`) || bare.includes('drawtext') || bare.includes('pad=')) {
    throw new Error(`masthead capture must fill the frame with no drawn badge: ${bare}`)
  }
  // no masthead -> shortened capture + rail, so the badge sits ABOVE the page, not on it
  const badged = newsFilter('SOURCE  JULY 15')
  if (!badged.includes(`scale=${FRAME_W}:${FRAME_H - BADGE_RAIL}`) || !badged.includes('drawtext')) {
    throw new Error(`badge fallback must reserve the top rail: ${badged}`)
  }
  // the exact string that defeated the old anchored regex (defect 2026-07-27)
  for (const label of ['I Accept All', 'Accept all', 'I Agree', 'Allow All', 'Got it']) {
    if (!CONSENT_RE.test(label)) throw new Error(`consent regex misses "${label}"`)
  }
  if (CONSENT_RE.test('Manage privacy choices') || CONSENT_RE.test('See Purposes')) {
    throw new Error('consent regex must not click through to a settings pane')
  }
  if ('clip' in screenshotOptions('selftest.png')) {
    throw new Error('source-card screenshots must use the centered 16:9 viewport')
  }
  if (!hostAllowed('https://ir.supermicro.com/release') || !hostAllowed('https://www.gevernova.com/news')) {
    throw new Error('official company-primary sources must stay on the approved roster')
  }
  console.log('NEWS FIT SELFTEST PASS')
  process.exit(0)
}
const dry = args.includes('--dry-run')
const reuse = args.includes('--reuse-png')
const pos = args.filter((a) => a !== '--dry-run' && a !== '--reuse-png')
if (pos.length < (dry ? 1 : 2)) {
  console.error('usage: node fetch_news_shots.mjs [--dry-run] [--reuse-png] <sources.json> <prod-dir>')
  process.exit(1)
}
run(pos[0], pos[1] ?? '.', dry, reuse).catch((e) => { console.error('FAILED:', e.message); process.exit(1) })
