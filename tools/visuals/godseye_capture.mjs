#!/usr/bin/env node
// Capture Godseye footage over CDP. Godseye owns all viewer, DOM, scene-state,
// evidence, and MediaRecorder behavior behind window.godseyeAutomationV1.
// TraderCockpit only schedules shots, writes chunks, and transcodes them.

import { spawn, execFileSync } from 'node:child_process'
import { pathToFileURL } from 'node:url'
import fs from 'node:fs'
import path from 'node:path'
import puppeteer from './puppeteer.mjs'

const GODSEYE_REPO = 'C:\\Users\\MSI\\repos\\godseye'
const EXES = ['Godseye.exe', 'GodsEye.exe'].map((name) => path.join(GODSEYE_REPO, 'release', 'win-unpacked', name))
const EXE = EXES.find(fs.existsSync) ?? EXES[0]
const APP_ORIGIN = 'http://127.0.0.1:39847'
const CDP_PORT = 9222
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
const slug = (value) => value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')

function validateShots(shots) {
  if (!Array.isArray(shots) || !shots.length) throw new Error('shot list must be a non-empty JSON array')
  shots.forEach((shot, index) => {
    const tag = `shot[${index}]${shot.name ? ` (${shot.name})` : ''}`
    if (typeof shot.name !== 'string' || !shot.name) throw new Error(`${tag}: "name" required`)
    for (const key of ['lon', 'lat', 'height', 'holdSec']) {
      if (typeof shot[key] !== 'number') throw new Error(`${tag}: "${key}" required (number)`)
    }
    if (shot.holdSec <= 0 || shot.height <= 0) throw new Error(`${tag}: height and holdSec must be positive`)
    for (const key of ['headingDeg', 'pitchDeg', 'orbitDegPerSec', 'settleSec', 'fromHeight', 'flyDurationSec', 'scanWaitSec']) {
      if (shot[key] !== undefined && typeof shot[key] !== 'number') throw new Error(`${tag}: "${key}" must be a number`)
    }
    for (const key of ['clickIds', 'scanAfter']) {
      if (shot[key] !== undefined && (!Array.isArray(shot[key]) || shot[key].some((item) => typeof item !== 'string'))) {
        throw new Error(`${tag}: "${key}" must be an array of strings`)
      }
    }
    if (shot.preset !== undefined && typeof shot.preset !== 'string') throw new Error(`${tag}: "preset" must be a string`)
    if (shot.caption !== undefined && typeof shot.caption !== 'string') throw new Error(`${tag}: "caption" must be a string`)
    if (shot.utcHour !== undefined) throw new Error(`${tag}: utcHour is retired; Godseye owns observation time`)
  })
}

function readShotList(file) {
  const shots = JSON.parse(fs.readFileSync(file, 'utf8'))
  validateShots(shots)
  return shots
}

async function tryConnect() {
  try {
    const response = await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`)
    if (!response.ok) return null
  } catch {
    return null
  }
  return puppeteer.connect({ browserURL: `http://127.0.0.1:${CDP_PORT}`, defaultViewport: null })
}

async function connectOrLaunch() {
  const existing = await tryConnect()
  if (existing) return existing
  if (!fs.existsSync(EXE)) throw new Error(`Godseye executable not found at ${EXE} — build the app first`)
  const child = spawn(EXE, [`--remote-debugging-port=${CDP_PORT}`], { detached: true, stdio: 'ignore' })
  child.unref()
  const started = Date.now()
  while (Date.now() - started < 15_000) {
    await sleep(500)
    const browser = await tryConnect()
    if (browser) return browser
  }
  throw new Error('Godseye did not expose CDP within 15s; quit an already-running non-debug instance and retry')
}

async function findAppPage(browser) {
  const started = Date.now()
  while (Date.now() - started < 20_000) {
    const page = (await browser.pages()).find((candidate) => candidate.url().startsWith(APP_ORIGIN))
    if (page) return page
    await sleep(500)
  }
  throw new Error(`no Godseye page found at ${APP_ORIGIN}`)
}

async function runShot(page, shot, outDir, number) {
  const base = path.join(outDir, `${number}-${slug(shot.name)}`)
  const webmPath = `${base}.webm`
  const evidencePath = `${base}.evidence.json`
  const request = {
    op: 'begin',
    presentation: 'story',
    camera: {
      lon: shot.lon,
      lat: shot.lat,
      height: shot.height,
      headingDeg: shot.headingDeg,
      pitchDeg: shot.pitchDeg,
      fromHeight: shot.fromHeight,
    },
    style: shot.preset,
    actions: shot.clickIds ?? [],
    afterActions: shot.scanAfter ?? [],
    orbitDegPerSec: shot.orbitDegPerSec,
    settleSec: shot.settleSec,
    flyDurationSec: shot.flyDurationSec,
    actionWaitSec: shot.scanWaitSec,
    quality: { resolutionScale: 2, maximumScreenSpaceError: 8 },
  }
  await page.evaluate((value) => window.godseyeAutomationV1(value), request)
  await sleep(shot.holdSec * 1000)

  const finished = await page.evaluate(
    (artifact) => window.godseyeAutomationV1({ op: 'finish', artifacts: [artifact] }),
    { name: path.basename(webmPath), uri: pathToFileURL(path.resolve(webmPath)).href, mediaType: 'video/webm' },
  )
  fs.writeFileSync(evidencePath, JSON.stringify(finished.evidence, null, 2))

  const out = fs.createWriteStream(webmPath)
  for (;;) {
    const chunk = await page.evaluate(() => window.godseyeAutomationV1({ op: 'drain' }))
    if (chunk === null) break
    out.write(Buffer.from(chunk, 'base64'))
  }
  await new Promise((resolve, reject) => {
    out.on('error', reject)
    out.end(resolve)
  })

  const mp4Path = `${base}.mp4`
  let vf = 'scale=1920:1080:force_original_aspect_ratio=increase:force_divisible_by=2,crop=1920:1080'
  if (shot.caption) {
    const caption = shot.caption.replace(/'/g, '’').replace(/:/g, '\\:').replace(/%/g, '\\%')
    vf += `,drawtext=fontfile='C\\:/Windows/Fonts/consola.ttf':text='${caption}'` +
      ':fontcolor=0xFFB000:fontsize=34:x=60:y=h-110:box=1:boxcolor=black@0.45:boxborderw=18'
  }
  execFileSync('ffmpeg', ['-y', '-i', webmPath, '-vf', vf, '-r', '30', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', mp4Path], { stdio: 'inherit' })
  console.log(`saved ${mp4Path} + ${evidencePath}`)
}

async function dryRun(shotlistPath) {
  const shots = readShotList(shotlistPath)
  if (typeof puppeteer.connect !== 'function') throw new Error('TraderCockpit Puppeteer does not expose connect()')
  console.log(`DRY RUN OK — ${shots.length} shots; TraderCockpit Puppeteer resolved`)
}

async function capture(shotlistPath, outDir) {
  const shots = readShotList(shotlistPath)
  fs.mkdirSync(outDir, { recursive: true })
  const browser = await connectOrLaunch()
  const page = await findAppPage(browser)
  page.on('pageerror', (error) => console.error('[Godseye page error]', error.message))
  await page.waitForFunction(() => typeof window.godseyeAutomationV1 === 'function', { timeout: 30_000 })
  try {
    for (let index = 0; index < shots.length; index++) {
      const number = String(index + 1).padStart(2, '0')
      const shot = shots[index]
      if (fs.existsSync(path.join(outDir, `${number}-${slug(shot.name)}.mp4`))) continue
      try {
        await runShot(page, shot, outDir, number)
      } catch (error) {
        console.error(`shot failed (${error.message.slice(0, 120)}) — reloading and retrying once`)
        await page.reload({ waitUntil: 'load' })
        await page.waitForFunction(() => typeof window.godseyeAutomationV1 === 'function', { timeout: 30_000 })
        await sleep(5000)
        await runShot(page, shot, outDir, number)
      }
    }
  } finally {
    await browser.disconnect()
  }
}

const args = process.argv.slice(2)
const isDryRun = args.includes('--dry-run')
const positional = args.filter((arg) => arg !== '--dry-run')
try {
  if (isDryRun) {
    if (!positional[0]) throw new Error('usage: godseye_capture.mjs --dry-run <shotlist.json>')
    await dryRun(positional[0])
  } else {
    if (!positional[0] || !positional[1]) throw new Error('usage: godseye_capture.mjs <shotlist.json> <outdir>')
    await capture(positional[0], positional[1])
  }
} catch (error) {
  console.error('FAILED:', error.message)
  process.exit(1)
}
