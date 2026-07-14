#!/usr/bin/env node
// fetch_news_shots.mjs — news-article / tweet screenshot lane for format v2.
//
// For each source: load the page headless (Edge via TraderCockpit's existing
// Puppeteer dependency), step through
// "highlight stages" (each stage red-boxes the exact sentence the VO reads and
// scrolls it into view), screenshot each stage, then ffmpeg the stage PNGs into
// one clip: slow Ken-Burns per stage, hard cut between stages.
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
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

function kenBurns(png, mp4, dur, badge) {
  const frames = Math.round(dur * 30)
  // cover-and-crop to 16:9 BEFORE zoompan — FILL the frame, never letterbox.
  // (was decrease+pad:black, which left black bars on wider-than-16:9 article crops
  //  and those bars carried into the 9:16 shorts. operator flagged 2026-07-14.)
  let vf = 'scale=3840:2160:force_original_aspect_ratio=increase,'
    + 'crop=3840:2160,'
    + `zoompan=z='min(zoom+0.0008,1.12)':d=${frames}`
    + ":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30"
  // source badge: viewer must always see which outlet this is (operator ruling 2026-07-14)
  if (badge) {
    const safe = badge.replace(/[\\':,]/g, ' ')
    vf += `,drawtext=text='${safe}':fontfile='C\\:/Windows/Fonts/arialbd.ttf'`
      + ':fontsize=34:fontcolor=white:box=1:boxcolor=0xE8272C@0.92:boxborderw=14:x=40:y=32'
  }
  vf += ',format=yuv420p'
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
async function declutter(page) {
  // consent: click the accept button by its text, whatever the site calls it
  await page.evaluate(() => {
    const re = /^(allow all|accept all|accept|i agree|agree|got it|continue)$/i
    for (const b of document.querySelectorAll('button, a[role="button"], [role="button"]')) {
      if (re.test((b.textContent || '').trim())) { b.click(); break }
    }
  })
  await sleep(400)
  // Minimal: iframes (ads) + fixed/sticky overlays (cookie bars, floating banners).
  // ponytail: the tight crop-to-paragraph is the real declutter — broad class-pattern
  // hiding nuked Insurance Journal's article container (blank-page defect 2026-07-14).
  await page.evaluate(() => {
    for (const el of document.querySelectorAll('iframe')) el.style.display = 'none'
    for (const el of document.querySelectorAll('div, section, aside')) {
      const cs = getComputedStyle(el)
      if ((cs.position === 'fixed' || cs.position === 'sticky') && el.offsetHeight < 400) {
        el.style.display = 'none'
      }
    }
  })
}

// highlight the paragraph containing `needle` (whitespace-normalized, case-insensitive).
// Returns the element's bounding box (for a zoomed crop) or null if not found.
// ponytail: paragraph-level, not text-node — article sentences split across inline links.
async function highlight(page, needle) {
  return page.evaluate((needle) => {
    const norm = (s) => s.replace(/\s+/g, ' ').trim().toLowerCase()
    const n = norm(needle)
    for (const el of document.querySelectorAll('p, li, blockquote, h1, h2, h3, figcaption')) {
      if (el.children.length > 8) continue // big containers — keep the box tight
      if (!norm(el.textContent || '').includes(n)) continue
      el.style.outline = '3px solid #E8272C'
      el.style.outlineOffset = '3px'
      el.style.background = 'rgba(232,39,44,0.10)'
      el.scrollIntoView({ block: 'center' })
      const r = el.getBoundingClientRect()
      if (r.width < 10 || r.height < 10) continue // hidden element — keep searching
      // document coords: puppeteer's screenshot clip is page-relative, getBoundingClientRect
      // is viewport-relative — without the scroll offset the crop lands in the wrong place
      return {
        x: r.x + window.scrollX, y: r.y + window.scrollY, width: r.width, height: r.height,
        docW: document.documentElement.scrollWidth, docH: document.documentElement.scrollHeight,
      }
    }
    return null
  }, needle)
}

// Crop tight around the highlighted paragraph so the text is BIG and readable at 1080p
// (full-page shots render body copy unreadably small — the reference channel zooms in).
function cropFor(box) {
  if (!box) return null
  const padX = 90, padTop = 130, minW = 1000, minH = 460
  const x = Math.max(0, box.x - padX)
  const y = Math.max(0, box.y - padTop)
  const width = Math.min(box.docW - x, Math.max(box.width + padX * 2, minW))
  const height = Math.min(box.docH - y, Math.max(box.height + padTop * 2, minH))
  return { x, y, width, height }
}

async function clearHighlights(page) {
  await page.evaluate(() => {
    for (const el of document.querySelectorAll('[style*="outline"]')) {
      el.style.outline = ''; el.style.background = ''
    }
  })
}

function badgeFor(src) {
  return src.label
    ?? new URL(src.url).hostname.replace(/^(www|platform)\./, '').toUpperCase()
      + (src.dated ? `  ${src.dated}` : '')
}

async function run(sourcesPath, prodDir, dry, reuse) {
  const sources = JSON.parse(fs.readFileSync(sourcesPath, 'utf8'))
  sources.forEach((s, i) => {
    for (const k of ['out', 'url']) if (!s[k]) throw new Error(`sources[${i}] missing "${k}"`)
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

  const browser = needBrowser ? await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--window-size=1920,1080', '--disable-blink-features=AutomationControlled'],
    defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 2 },
  }) : null

  try {
    for (const src of sources) {
      const outMp4 = path.join(visuals, `${src.out}.mp4`)
      if (fs.existsSync(outMp4)) { console.log(`[${src.out}] exists, skip`); continue }
      if (reuse && cachedPngs(src).every((p) => fs.existsSync(p))) {
        console.log(`[${src.out}] reuse cached PNGs`)
        const clips = cachedPngs(src).map((png, i) => {
          const clip = path.join(work, `${src.out}-s${i}.mp4`)
          kenBurns(png, clip, src.holdSec ?? 8, badgeFor(src))
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
      const page = await browser.newPage()
      await page.setUserAgent(UA)
      try {
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 45_000 })
      } catch {
        console.log('  [warn] networkidle timeout — proceeding with whatever loaded')
      }
      await sleep(2500)
      await declutter(page)
      await sleep(500)

      const hold = src.holdSec ?? 8
      const clips = []
      const stages = src.highlights?.length ? src.highlights : [null]
      for (let i = 0; i < stages.length; i++) {
        await clearHighlights(page)
        let crop = null
        if (stages[i]) {
          const box = await highlight(page, stages[i])
          if (!box) console.log(`  [warn] highlight not found: "${stages[i].slice(0, 60)}..."`)
          else crop = cropFor(box)
          await sleep(600)
        }
        const png = path.join(work, `${src.out}-s${i}.png`)
        await page.screenshot({ path: png, ...(crop ? { clip: crop } : {}) })
        const clip = path.join(work, `${src.out}-s${i}.mp4`)
        // badge = outlet + optional date; override with src.label in sources.json
        const badge = src.label
          ?? new URL(url).hostname.replace(/^(www|platform)\./, '').toUpperCase()
            + (src.dated ? `  ${src.dated}` : '')
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
const dry = args.includes('--dry-run')
const reuse = args.includes('--reuse-png')
const pos = args.filter((a) => a !== '--dry-run' && a !== '--reuse-png')
if (pos.length < (dry ? 1 : 2)) {
  console.error('usage: node fetch_news_shots.mjs [--dry-run] [--reuse-png] <sources.json> <prod-dir>')
  process.exit(1)
}
run(pos[0], pos[1] ?? '.', dry, reuse).catch((e) => { console.error('FAILED:', e.message); process.exit(1) })
