#!/usr/bin/env node
// godseye_capture.mjs — automated cinematic footage capture from the God's Eye
// Electron app (Cesium globe, repo C:\Users\MSI\repos\godseye) for YouTube news
// videos. Attaches to the running (or freshly-launched) GodsEye.exe over CDP
// via puppeteer-core, drives window.__viewer in page context, records
// canvas.captureStream via MediaRecorder, and transcodes each clip to mp4
// with ffmpeg. Never touches the godseye repo itself — read-only neighbor.
//
// Usage:
//   node godseye_capture.mjs <shotlist.json> <outdir>
//   node godseye_capture.mjs --dry-run <shotlist.json>
//
// Shot list schema (array of):
//   { name, lon, lat, height?, headingDeg?, pitchDeg?, holdSec,
//     orbitDegPerSec?, preset?, caption?, clickIds?: [], settleSec?, utcHour? }
//
// clickIds entries are either:
//   - a literal DOM id, e.g. "dark-scan" / "gate-scan" / "cable-load" (real
//     buttons that exist in index.html / are created with a fixed id)
//   - "layer:NAME" e.g. "layer:GLOBAL INFRA" — the DATA LAYERS checkboxes are
//     built dynamically (src/layer-panel.ts addLayerRow) with NO id at all,
//     only a visible label text — this convention finds the row by
//     label.layer-row textContent and clicks its checkbox. Most named layers
//     (CRITICAL INFRA, MILITARY, NIGHT LIGHTS, FLIGHTS, SATELLITES,
//     EARTHQUAKES 24H) are already ON by default — only click to turn them
//     OFF, or to turn on opt-in layers (GLOBAL INFRA, WEATHER RADAR default
//     off; SUBMARINE CABLES/SHIPS/DARK VESSELS/HORMUZ GATE are on-demand and
//     need their own LOAD/SCAN button, e.g. "cable-load", not a layer toggle).
//
// utcHour (0-23, not in the original brief): freezes viewer.clock.currentTime
// at that UTC hour today. Added because NIGHT LIGHTS only renders on the dark
// side of Cesium's real-time day/night terminator — without this, a
// "night lights" shot silently shows nothing if it happens to be Gulf
// daytime when you run the script.
// WARNING (2026-07-13): setting the clock triggered a Cesium fatal that killed
// the ge-raw3 run on its final shot — the skill rule is "NEVER set the viewer
// clock". Avoid utcHour; shoot regions while naturally dark (Gulf ≈ 22-02 UTC)
// or fake the look with the DUSK preset.
//
// # ponytail: single flat script, no framework, no config file. Reuses
// godseye's own puppeteer-core install (a devDependency of that repo) via an
// absolute import path so nothing gets installed here.

import { spawn, execFileSync } from 'node:child_process'
import { pathToFileURL } from 'node:url'
import fs from 'node:fs'
import path from 'node:path'

const GODSEYE_REPO = 'C:\\Users\\MSI\\repos\\godseye'
const EXE = path.join(GODSEYE_REPO, 'release', 'win-unpacked', 'GodsEye.exe')
const PUPPETEER_CORE = path.join(GODSEYE_REPO, 'node_modules', 'puppeteer-core', 'lib', 'puppeteer', 'puppeteer-core.js')
const APP_ORIGIN = 'http://127.0.0.1:39847'
const CDP_PORT = 9222

// src/styles-fx.ts PRESETS — keys 1-9 in the app, clicked here by button textContent.
const PRESETS = ['NORMAL', 'CRT', 'NVG', 'FLIR', 'ANIME', 'NOIR', 'IRONBOW', 'DUSK', 'CINEMA']

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms))
}
function slug(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
}

// -- shot list validation (shared by dry-run and real run) ------------------
function validateShots(shots) {
  if (!Array.isArray(shots) || shots.length === 0) throw new Error('shot list must be a non-empty JSON array')
  shots.forEach((s, i) => {
    const tag = `shot[${i}]${s.name ? ` (${s.name})` : ''}`
    if (typeof s.name !== 'string' || !s.name) throw new Error(`${tag}: "name" required (string)`)
    for (const k of ['lon', 'lat']) if (typeof s[k] !== 'number') throw new Error(`${tag}: "${k}" required (number)`)
    if (s.height !== undefined && typeof s.height !== 'number') throw new Error(`${tag}: "height" must be a number (meters)`)
    if (typeof s.holdSec !== 'number' || s.holdSec <= 0) throw new Error(`${tag}: "holdSec" required (number > 0, seconds)`)
    if (s.headingDeg !== undefined && typeof s.headingDeg !== 'number') throw new Error(`${tag}: "headingDeg" must be a number`)
    if (s.pitchDeg !== undefined && typeof s.pitchDeg !== 'number') throw new Error(`${tag}: "pitchDeg" must be a number`)
    if (s.preset !== undefined && !PRESETS.includes(s.preset)) throw new Error(`${tag}: "preset" must be one of ${PRESETS.join(', ')}`)
    if (s.caption !== undefined && typeof s.caption !== 'string') throw new Error(`${tag}: "caption" must be a string`)
    if (s.clickIds !== undefined && !Array.isArray(s.clickIds)) throw new Error(`${tag}: "clickIds" must be an array of strings`)
    if (s.orbitDegPerSec !== undefined && typeof s.orbitDegPerSec !== 'number') throw new Error(`${tag}: "orbitDegPerSec" must be a number`)
    if (s.settleSec !== undefined && typeof s.settleSec !== 'number') throw new Error(`${tag}: "settleSec" must be a number`)
    if (s.utcHour !== undefined && (typeof s.utcHour !== 'number' || s.utcHour < 0 || s.utcHour > 23))
      throw new Error(`${tag}: "utcHour" must be a number 0-23`)
  })
}
function readShotList(file) {
  const shots = JSON.parse(fs.readFileSync(file, 'utf8'))
  validateShots(shots)
  return shots
}

// -- CDP connect / launch ----------------------------------------------------
async function tryConnect(puppeteer) {
  try {
    const res = await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`)
    if (!res.ok) return null
  } catch {
    return null // nothing listening yet — normal while waiting for launch
  }
  return puppeteer.connect({ browserURL: `http://127.0.0.1:${CDP_PORT}`, defaultViewport: null })
}

async function connectOrLaunch(puppeteer) {
  const already = await tryConnect(puppeteer)
  if (already) {
    console.log(`found existing CDP endpoint on ${CDP_PORT} (GodsEye already running with debugging on)`)
    return already
  }
  if (!fs.existsSync(EXE)) throw new Error(`GodsEye.exe not found at ${EXE} — build the app first`)
  console.log(`launching GodsEye.exe --remote-debugging-port=${CDP_PORT}`)
  const child = spawn(EXE, [`--remote-debugging-port=${CDP_PORT}`], { detached: true, stdio: 'ignore' })
  child.unref()
  const started = Date.now()
  while (Date.now() - started < 15_000) {
    await sleep(500)
    const b = await tryConnect(puppeteer)
    if (b) return b
  }
  throw new Error(
    `could not reach CDP on ${CDP_PORT} within 15s after launch. Most likely GodsEye was ALREADY RUNNING ` +
      '(single-instance lock silently swallows the debug flag on a second launch and just focuses the ' +
      'existing window) — close it fully via tray -> Quit, then retry.',
  )
}

// picture-quality bump: render at full 2x scale and stream sharper 3D tiles.
// # ponytail: SSE 8 (Cesium default 16) is the tuning knob — raise it back
// toward 16 if the RTX 3080 stutters or tiles never finish streaming.
async function applyQuality(page) {
  await page.evaluate(() => {
    const v = window.__viewer
    v.resolutionScale = 2 // app default is min(devicePixelRatio, 2)
    for (let i = 0; i < v.scene.primitives.length; i++) {
      const p = v.scene.primitives.get(i)
      if (p && p.maximumScreenSpaceError !== undefined) p.maximumScreenSpaceError = 8
    }
  })
}

async function findAppPage(browser) {
  const started = Date.now()
  while (Date.now() - started < 20_000) {
    const pages = await browser.pages()
    const hit = pages.find((p) => p.url().startsWith(APP_ORIGIN))
    if (hit) return hit
    await sleep(500)
  }
  throw new Error(`no page found with url starting with ${APP_ORIGIN} — is GodsEye actually loaded?`)
}

// click a DOM target: literal id, "layer:NAME" / "layer:NAME:off" (checkbox by
// row label), or "basemap:MODE" ( #basemaps button ). Returns true if it acted.
// "layer:" is idempotent — ensures the layer is ON (or OFF with the :off
// suffix) instead of blind-toggling. LESSON (2026-07-13, ge-raw4): default-on
// layers (CRITICAL INFRA, MILITARY) got toggled OFF by shot lists that meant
// "make sure this is visible", so the infra shot recorded with no infra.
async function clickTarget(page, idOrLayer) {
  return page.evaluate((idOrLayer) => {
    if (idOrLayer.startsWith('layer:')) {
      let name = idOrLayer.slice('layer:'.length)
      let want = true
      if (name.endsWith(':off')) { name = name.slice(0, -4); want = false }
      const row = [...document.querySelectorAll('#layers label.layer-row')].find((l) => l.textContent?.includes(name))
      const box = row?.querySelector('input[type=checkbox]')
      if (!box) return false
      if (box.checked !== want) box.click()
      return true
    }
    if (idOrLayer.startsWith('basemap:')) {
      const mode = idOrLayer.slice('basemap:'.length)
      const btn = document.querySelector(`#basemaps button[data-mode="${mode}"]`)
      if (!btn) return false
      btn.click(); return true
    }
    const el = document.getElementById(idOrLayer)
    if (!el) return false
    el.click(); return true
  }, idOrLayer)
}

// -- per-shot execution -------------------------------------------------------
async function runShot(page, shot, outDir, n) {
  if (shot.utcHour !== undefined) {
    await page.evaluate((h) => {
      const v = window.__viewer
      // no global Cesium in page context (main.ts imports named exports, doesn't attach a
      // namespace) — borrow the real JulianDate class off a live instance instead.
      const JulianDate = v.clock.currentTime.constructor
      const d = new Date()
      d.setUTCHours(h, 0, 0, 0)
      v.clock.currentTime = JulianDate.fromDate(d)
    }, shot.utcHour)
  }

  if (shot.preset) {
    const ok = await page.evaluate((name) => {
      const btn = [...document.querySelectorAll('#style-presets button')].find((b) => b.textContent === name)
      if (!btn) return false
      btn.click()
      return true
    }, shot.preset)
    if (!ok) throw new Error(`preset button not found: ${shot.preset}`)
  }

  for (const id of shot.clickIds ?? []) {
    const ok = await clickTarget(page, id)
    if (!ok) throw new Error(`click target not found: ${id}`)
  }

  if (shot.caption) {
    await page.evaluate((text) => {
      document.getElementById('hud-summary').textContent = text
      // # ponytail: main.ts's templateSummary() overwrites #hud-summary every 5s (and an LLM
      // caption every 60s) — we can't touch main.ts, so fight it for the life of this shot
      // with a cheap re-assert interval instead.
      clearInterval(window.__capCaptionTimer)
      window.__capCaptionTimer = setInterval(() => {
        document.getElementById('hud-summary').textContent = text
      }, 500)
    }, shot.caption)
  }

  const flyTo = (durationSec) =>
    page.evaluate(
      (lon, lat, height, headingDeg, pitchDeg, duration) =>
        new Promise((resolve, reject) => {
          const v = window.__viewer
          const Cartesian3 = v.camera.position.constructor // same trick: borrow the class off a live Cartesian3
          const toRad = (d) => (d * Math.PI) / 180
          v.camera.flyTo({
            destination: Cartesian3.fromDegrees(lon, lat, height ?? 2_000_000),
            orientation: { heading: toRad(headingDeg ?? 0), pitch: toRad(pitchDeg ?? -30), roll: 0 },
            duration,
            complete: resolve,
            cancel: () => reject(new Error('camera flyTo was cancelled (interrupted by another flyTo?)')),
          })
        }),
      shot.lon,
      shot.lat,
      shot.height,
      shot.headingDeg,
      shot.pitchDeg,
      durationSec,
    )

  // Orbit AROUND the shot target, keeping it centered. camera.rotateRight()
  // (the old approach) orbits around the GLOBE center — at 2°/s over a 35s
  // hold the camera drifts ~70° of longitude and films the wrong country.
  // Started only AFTER the camera arrives (lookAt would fight an in-flight flyTo).
  const startOrbit = () => shot.orbitDegPerSec && page.evaluate((orbitDegPerSec, lon, lat) => {
    const v = window.__viewer
    const Cartesian3 = v.camera.position.constructor
    const Matrix4 = v.camera.viewMatrix.constructor
    const target = Cartesian3.fromDegrees(lon, lat, 0)
    const range = Cartesian3.distance(v.camera.position, target)
    const pitch = v.camera.pitch // negative = looking down
    let heading = v.camera.heading
    const rate = (orbitDegPerSec * Math.PI) / 180
    const d = range * Math.cos(-pitch)
    const up = range * Math.sin(-pitch)
    let last = performance.now()
    const remove = v.clock.onTick.addEventListener(() => {
      const now = performance.now()
      heading += rate * ((now - last) / 1000)
      last = now
      v.camera.lookAt(target, new Cartesian3(-d * Math.sin(heading), -d * Math.cos(heading), up))
    })
    window.__orbitRemover = () => {
      remove()
      v.camera.lookAtTransform(Matrix4.IDENTITY) // unlock the transform or the next flyTo misbehaves
    }
  }, shot.orbitDegPerSec, shot.lon, shot.lat)

  const startRecorder = () => page.evaluate(() => {
    const v = window.__viewer
    const canvas = v.scene.canvas
    window.__cap = { chunks: [] }
    const rec = new MediaRecorder(canvas.captureStream(30), {
      mimeType: 'video/webm;codecs=vp9',
      videoBitsPerSecond: 12_000_000,
    })
    rec.ondataavailable = (e) => e.data.size && window.__cap.chunks.push(e.data)
    window.__cap.rec = rec
    window.__cap.stopped = new Promise((resolve) => (rec.onstop = resolve))
    rec.start(1000) // 1s timeslice: chunks arrive incrementally so no single evaluate() payload gets huge
  })

  if (shot.fromHeight) {
    // cinematic zoom-in: park high over the target, record the descent flyTo itself
    await page.evaluate(
      (lon, lat, fromHeight) => {
        const v = window.__viewer
        const Cartesian3 = v.camera.position.constructor
        v.camera.setView({ destination: Cartesian3.fromDegrees(lon, lat, fromHeight) })
      },
      shot.lon, shot.lat, shot.fromHeight,
    )
    await sleep(2500) // let the space view settle
    await startRecorder()
    await flyTo(shot.flyDurationSec ?? 6)
    await startOrbit()
  } else {
    await flyTo(3)
    await sleep((shot.settleSec ?? 4) * 1000) // let 3D tiles stream in before recording
    // View-bboxed scans (ships-sub / gate-scan / dark-scan) MUST run after the camera
    // arrives, so they subscribe to THIS view (the strait) rather than the previous
    // shot's location. Then wait for the feed to populate before recording starts.
    for (const id of shot.scanAfter ?? []) {
      const ok = await clickTarget(page, id)
      if (!ok) throw new Error(`scanAfter target not found: ${id}`)
    }
    if (shot.scanAfter?.length) await sleep((shot.scanWaitSec ?? 5) * 1000)
    await startOrbit()
    await startRecorder()
  }

  await sleep(shot.holdSec * 1000)

  await page.evaluate(() => {
    if (window.__orbitRemover) { window.__orbitRemover(); window.__orbitRemover = null }
    clearInterval(window.__capCaptionTimer)
    window.__cap.rec.stop()
  })
  await page.evaluate(() => window.__cap.stopped) // wait for the final ondataavailable + onstop

  // drain chunks one at a time (already ~1s-sized Blobs from the timeslice above) rather
  // than one giant transfer — cheap chunked-read loop per the size-safety note in the brief.
  const webmPath = path.join(outDir, `${n}-${slug(shot.name)}.webm`)
  const out = fs.createWriteStream(webmPath)
  for (;;) {
    const b64 = await page.evaluate(
      () =>
        new Promise((resolve) => {
          const blob = window.__cap.chunks.shift()
          if (!blob) return resolve(null)
          const r = new FileReader()
          r.onload = () => resolve(String(r.result).split(',')[1])
          r.readAsDataURL(blob)
        }),
    )
    if (b64 === null) break
    out.write(Buffer.from(b64, 'base64'))
  }
  await new Promise((resolve, reject) => out.end((err) => (err ? reject(err) : resolve())))
  console.log(`  saved ${webmPath}`)

  const mp4Path = webmPath.replace(/\.webm$/, '.mp4')
  // canvas is odd-sized/non-16:9 (window minus HUD chrome) — cover-crop to 1920x1080, force CFR 30.
  // DOM HUD (#hud-summary) is NOT part of the WebGL canvas, so captions are burned here instead.
  let vf = 'scale=1920:1080:force_original_aspect_ratio=increase:force_divisible_by=2,crop=1920:1080'
  if (shot.caption) {
    const text = shot.caption.replace(/'/g, '’').replace(/:/g, '\\:').replace(/%/g, '\\%')
    vf += `,drawtext=fontfile='C\\:/Windows/Fonts/consola.ttf':text='${text}'` +
      ':fontcolor=0xFFB000:fontsize=34:x=60:y=h-110:box=1:boxcolor=black@0.45:boxborderw=18'
  }
  execFileSync('ffmpeg', ['-y', '-i', webmPath, '-vf', vf,
    '-r', '30', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', mp4Path], {
    stdio: 'inherit',
  })
  console.log(`  transcoded ${mp4Path}`)
}

// -- modes --------------------------------------------------------------------
async function runDryRun(shotlistPath) {
  console.log('dry-run: validating shot list schema ->', shotlistPath)
  const shots = readShotList(shotlistPath)
  console.log(`  OK: ${shots.length} shots -> ${shots.map((s) => s.name).join(', ')}`)

  console.log('dry-run: resolving puppeteer-core (godseye devDependency) ->', PUPPETEER_CORE)
  const mod = await import(pathToFileURL(PUPPETEER_CORE).href)
  if (typeof mod.default?.connect !== 'function') throw new Error('puppeteer-core loaded but .connect is not a function')
  console.log('  OK: module resolved and loaded, puppeteer.connect is callable')
  console.log('DRY RUN OK — no app launched, no capture performed.')
}

async function runCapture(shotlistPath, outDir) {
  const shots = readShotList(shotlistPath)
  fs.mkdirSync(outDir, { recursive: true })

  const puppeteer = (await import(pathToFileURL(PUPPETEER_CORE).href)).default
  const browser = await connectOrLaunch(puppeteer)
  const page = await findAppPage(browser)
  page.on('pageerror', (e) => console.error('  [page error]', e.message))

  console.log(`connected to ${APP_ORIGIN} — waiting for window.__viewer...`)
  await page.waitForFunction(() => !!window.__viewer, { timeout: 30_000 })
  await applyQuality(page)

  for (let i = 0; i < shots.length; i++) {
    const n = String(i + 1).padStart(2, '0')
    const shot = shots[i]
    if (fs.existsSync(path.join(outDir, `${n}-${slug(shot.name)}.mp4`))) {
      console.log(`\n[${n}/${shots.length}] ${shot.name} — mp4 exists, skip`)
      continue
    }
    console.log(`\n[${n}/${shots.length}] ${shot.name}`)
    try {
      await runShot(page, shot, outDir, n)
    } catch (e) {
      // a Cesium fatal (e.g. geometry RangeError) stops rendering behind a modal — reload recovers
      console.error(`  shot failed (${e.message.slice(0, 120)}) — reloading app and retrying once`)
      await page.reload({ waitUntil: 'load' })
      await page.waitForFunction(() => !!window.__viewer, { timeout: 30_000 })
      await applyQuality(page) // reload reset the viewer — re-apply before the retry
      await sleep(5000)
      await runShot(page, shot, outDir, n)
    }
  }

  await browser.disconnect() // we only attached — leave GodsEye running
  console.log(`\nALL ${shots.length} SHOTS CAPTURED -> ${outDir}`)
}

// -- CLI ------------------------------------------------------------------
const args = process.argv.slice(2)
const dryRun = args.includes('--dry-run')
const positional = args.filter((a) => a !== '--dry-run')

try {
  if (dryRun) {
    if (positional.length < 1) throw new Error('usage: node godseye_capture.mjs --dry-run <shotlist.json>')
    await runDryRun(positional[0])
  } else {
    if (positional.length < 2) throw new Error('usage: node godseye_capture.mjs <shotlist.json> <outdir>')
    await runCapture(positional[0], positional[1])
  }
} catch (e) {
  console.error('FAILED:', e.message)
  process.exit(1)
}
