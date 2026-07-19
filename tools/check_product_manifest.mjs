import assert from 'node:assert/strict'
import fs from 'node:fs'
import http from 'node:http'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { validateProductManifest } from '../docs/product-manifest.mjs'
import { validatePrelaunchConfig } from '../docs/prelaunch-config.mjs'
import puppeteer from './visuals/puppeteer.mjs'

globalThis.location = { href: 'https://javin23863.github.io/tradercockpit/' }
const manifest = JSON.parse(fs.readFileSync(new URL('../docs/product-manifest.v1.json', import.meta.url), 'utf8'))
const prelaunch = JSON.parse(fs.readFileSync(new URL('../docs/prelaunch-config.v1.json', import.meta.url), 'utf8'))
assert.equal(validateProductManifest(manifest).status, 'waitlist')
assert.throws(() => validateProductManifest(null), /schema/)
assert.throws(() => validateProductManifest({ ...manifest, schema: 'product-manifest/v2' }), /schema/)
assert.throws(() => validateProductManifest({ ...manifest, cta: { label: 'Buy', url: 'javascript:alert(1)' } }), /https or mailto/)
console.log('product-manifest/v1: 4/4 PASS')
assert.equal(validatePrelaunchConfig(prelaunch).waitlist.status, 'pending_operator_account')
assert.throws(() => validatePrelaunchConfig({ ...prelaunch, waitlist: { ...prelaunch.waitlist, status: 'active', username: '' } }), /username/)
assert.throws(() => validatePrelaunchConfig({
  ...prelaunch,
  analytics: { ...prelaunch.analytics, status: 'active', scriptSrc: 'https://example.com/tracker.js' },
}), /Plausible/)
console.log('prelaunch-config/v1: 3/3 PASS')

if (process.argv.includes('--browser')) {
  const docs = fileURLToPath(new URL('../docs/', import.meta.url))
  const repository = path.resolve(fileURLToPath(new URL('../', import.meta.url)))
  const evidenceOption = process.argv.find((argument) => argument.startsWith('--helios-evidence='))
  const evidenceDirectory = evidenceOption ? path.resolve(repository, evidenceOption.split('=').slice(1).join('=')) : null
  if (evidenceDirectory) assert.ok(evidenceDirectory.startsWith(`${repository}${path.sep}`), 'evidence must stay inside the repository')
  let mode = 'valid'
  let prelaunchMode = 'pending'
  const activePrelaunch = {
    ...prelaunch,
    waitlist: { ...prelaunch.waitlist, status: 'active', username: 'tradercockpit-test' },
  }
  const server = http.createServer((request, response) => {
    const pathname = new URL(request.url, 'http://localhost').pathname
    if (pathname === '/product-manifest.v1.json') {
      if (mode === 'missing') { response.writeHead(404).end(); return }
      response.setHeader('Content-Type', 'application/json')
      response.end(mode === 'malformed' ? '{' : JSON.stringify(mode === 'unsupported' ? { ...manifest, schema: 'product-manifest/v2' } : manifest))
      return
    }
    if (pathname === '/prelaunch-config.v1.json') {
      response.setHeader('Content-Type', 'application/json')
      response.end(JSON.stringify(prelaunchMode === 'active' ? activePrelaunch : prelaunch))
      return
    }
    const file = path.join(docs, pathname === '/' ? 'index.html' : pathname.slice(1))
    if (!file.startsWith(docs) || !fs.existsSync(file)) { response.writeHead(404).end(); return }
    response.setHeader('Content-Type', file.endsWith('.mjs') ? 'text/javascript' : file.endsWith('.html') ? 'text/html' : 'application/octet-stream')
    response.end(fs.readFileSync(file))
  })
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve))
  const port = server.address().port
  const browserOptions = {
    executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true,
    args: ['--disable-background-timer-throttling', '--disable-backgrounding-occluded-windows', '--disable-renderer-backgrounding'],
  }
  let browser = await puppeteer.launch(browserOptions)
  try {
    let page = await browser.newPage()
    for (const candidate of ['valid', 'missing', 'malformed', 'unsupported']) {
      mode = candidate
      await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'networkidle0' })
      const result = await page.evaluate(() => ({
        state: document.documentElement.dataset.productManifest,
        assistant: document.getElementById('apollo-name').textContent,
        cta: document.getElementById('product-cta').getAttribute('href'),
      }))
      assert.equal(result.state, candidate === 'valid' ? 'verified' : 'fallback')
      assert.equal(result.assistant, candidate === 'valid' ? 'Apollo' : 'ASSISTANT CONCEPT')
      assert.match(result.cta, /^mailto:/)
    }
    mode = 'valid'
    prelaunchMode = 'active'
    await page.goto(`http://127.0.0.1:${port}/?utm_source=tiktok&utm_medium=social&utm_campaign=test`, { waitUntil: 'networkidle0' })
    const waitlist = await page.evaluate(() => ({
      state: document.documentElement.dataset.prelaunch,
      hidden: document.getElementById('waitlist-form').hidden,
      action: document.getElementById('waitlist-form').action,
      productHidden: document.getElementById('product-cta').hidden,
      source: document.getElementById('waitlist-source').value,
      utmSource: document.getElementById('waitlist-utm-source').value,
      utmMedium: document.getElementById('waitlist-utm-medium').value,
      utmCampaign: document.getElementById('waitlist-utm-campaign').value,
    }))
    assert.deepEqual(waitlist, {
      state: 'waitlist-active',
      hidden: false,
      action: 'https://buttondown.com/api/emails/embed-subscribe/tradercockpit-test',
      productHidden: true,
      source: 'source-tiktok',
      utmSource: 'tiktok',
      utmMedium: 'social',
      utmCampaign: 'test',
    })
    prelaunchMode = 'pending'
    await page.setViewport({ width: 390, height: 844 })
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }])
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'networkidle0' })
    const mobile = await page.evaluate(() => ({
      fits: document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      boot: getComputedStyle(document.getElementById('boot')).display,
      plausibleScripts: [...document.scripts].filter((script) => /plausible/i.test(script.src)).length,
      cookies: document.cookie,
    }))
    assert.equal(mobile.fits, true)
    assert.equal(mobile.boot, 'none')
    assert.equal(mobile.plausibleScripts, 0)
    assert.equal(mobile.cookies, '')

    await page.setViewport({ width: 1024, height: 900 })
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }])
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'networkidle0' })
    await page.click('#boot')
    const organic = await page.evaluate(() => {
      const canvas = document.getElementById('apollo-core')
      const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data
      let visible = 0, warm = 0
      for (let i = 3; i < pixels.length; i += 4) {
        if (pixels[i]) visible++
        if (pixels[i] && pixels[i - 3] > pixels[i - 1] * 1.35 && pixels[i - 2] > pixels[i - 1]) warm++
      }
      return {
        label: canvas.getAttribute('aria-label'), role: canvas.getAttribute('role'), describedBy: canvas.getAttribute('aria-describedby'), tabIndex: canvas.tabIndex, visible, warm,
        socials: [...document.querySelectorAll('.social-link')].map((link) => [link.dataset.channel, link.href]),
      }
    })
    assert.match(organic.label, /solar Apollo/)
    assert.equal(organic.role, 'button')
    assert.equal(organic.describedBy, 'apollo-interaction-note')
    assert.equal(organic.tabIndex, 0)
    assert.ok(organic.visible > 100, 'solar canvas should paint a visible state')
    assert.ok(organic.warm > 100, 'solar canvas should paint a warm sun and flares')
    assert.deepEqual(organic.socials, [
      ['youtube', 'https://www.youtube.com/@Thetradercockpit'],
      ['instagram', 'https://www.instagram.com/tradercockpit/'],
      ['tiktok', 'https://www.tiktok.com/@trader.cockpit'],
      ['facebook', 'https://www.facebook.com/profile.php?id=61591774715570'],
    ])
    const pulseBefore = await page.$eval('#apollo-core', (canvas) => canvas.dataset.sunRadius)
    await new Promise((resolve) => setTimeout(resolve, 180))
    const pulseAfter = await page.$eval('#apollo-core', (canvas) => canvas.dataset.sunRadius)
    assert.notEqual(pulseAfter, pulseBefore, 'Apollo sun radius should pulse when motion is allowed')
    await page.focus('#apollo-core')
    await page.keyboard.press('Enter')
    assert.equal(await page.$eval('#apollo-core', (canvas) => canvas.dataset.eruption), 'active')
    await page.waitForFunction(() => Number(document.getElementById('apollo-core').dataset.eruptionEnergy) > .35, { polling: 'raf', timeout: 1000 })
    const eruption = await page.$eval('#apollo-core', (canvas) => ({ state: canvas.dataset.eruption, energy: Number(canvas.dataset.eruptionEnergy) }))
    assert.equal(eruption.state, 'active')
    assert.ok(eruption.energy > .35, 'keyboard-triggered solar eruption should paint a visible energy burst')

    const chipHit = await page.$eval('.chip', (chip) => {
      document.documentElement.style.scrollBehavior = 'auto'
      chip.scrollIntoView({ block: 'center', inline: 'center' })
      const rect = chip.getBoundingClientRect()
      const target = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2)
      return {
        chipRect: [rect.x, rect.y, rect.width, rect.height], scrollY,
        targetTag: target?.tagName || '', targetId: target?.id || '', targetClass: target?.className || '',
        targetMotion: target?.dataset?.heliosMotion || '', targetText: target?.textContent || '', isChip: target === chip,
      }
    })
    assert.equal(chipHit.isChip, true, `legacy strategy chip is covered: ${JSON.stringify(chipHit)}`)
    await page.click('.chip')
    assert.equal(await page.$eval('#apollo-state', (el) => el.textContent), 'THINKING')
    await new Promise((resolve) => setTimeout(resolve, 700))
    assert.equal(await page.$eval('#apollo-state', (el) => el.textContent), 'PREVIEWING')
    await page.click('#initiate')
    const confirmation = await page.evaluate(() => ({
      hidden: document.getElementById('confirm-panel').hidden,
      state: document.getElementById('apollo-state').textContent,
      focus: document.activeElement.id,
    }))
    assert.deepEqual(confirmation, { hidden: false, state: 'CONFIRMING', focus: 'confirm-run' })
    await page.click('#cancel-run')
    assert.equal(await page.$eval('#apollo-state', (el) => el.textContent), 'PREVIEWING')

    await page.click('#voice-preview')
    const voice = await page.evaluate(() => ({
      pressed: document.getElementById('voice-preview').getAttribute('aria-pressed'),
      note: document.getElementById('voice-note').textContent,
    }))
    assert.equal(voice.pressed, 'true')
    assert.match(voice.note, /no audio captured/)

    await page.setViewport({ width: 1536, height: 1024, deviceScaleFactor: 1 })
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }])
    await page.close()
    page = await browser.newPage()
    await page.setViewport({ width: 1536, height: 1024, deviceScaleFactor: 1 })
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }])
    await page.goto(`http://127.0.0.1:${port}/?motionTime=12`, { waitUntil: 'networkidle0' })
    await page.evaluate(() => document.getElementById('boot').classList.add('done'))
    const shell = await page.evaluate(() => ({
      h1: document.querySelectorAll('h1').length,
      main: document.querySelectorAll('main').length,
      width: document.getElementById('helios-app').getBoundingClientRect().width,
      height: document.getElementById('helios-app').getBoundingClientRect().height,
      fits: document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      panels: [...document.querySelectorAll('[data-helios-view]')].map((panel) => {
        const rect = panel.getBoundingClientRect()
        return { view: panel.dataset.heliosView, x: rect.x, y: rect.y, width: rect.width, height: rect.height }
      }),
      graphics: [...document.querySelectorAll('[data-helios-view]')].map((panel) => {
        const rect = panel.querySelector('.panel-graphic').getBoundingClientRect()
        return { view: panel.dataset.heliosView, y: rect.y, height: rect.height }
      }),
      canvases: [...document.querySelectorAll('#helios-app canvas')].map((canvas) => canvas.getAttribute('aria-hidden')),
      destinations: [...new Set([...document.querySelectorAll('[data-view-target]')].map((button) => button.dataset.viewTarget))],
      graphNodes: document.querySelectorAll('.strategy-graph .graphic-label').length,
      settingsControls: [...document.querySelectorAll('.control-row button')].map((button) => ({
        type: button.type, disabled: button.getAttribute('aria-disabled'),
      })),
      minimumPublicFont: Math.min(...[...document.querySelectorAll(
        '.deck-head h2,.graphic-label,.home-message b,.home-message p,.home-message time,.evidence-chips b,.evidence-chips span,.deck-nav button,.phase-tabs button,.phase-registry,.exact-evidence button,.strategy-library p,.strategy-mini,.eligibility-center,.status-bar,.system-controls p,.control-row button',
      )].map((element) => Number.parseFloat(getComputedStyle(element).fontSize))),
      unsafeClaims: /CERTIFIED AUTOMATION|Active & Monitoring|BROKER\s+Connected|Promising|Private by design|Full provenance|Continuous learning/i.test(document.getElementById('helios-app').innerText),
    }))
    const readability = await page.evaluate(() => {
      const parseHex = (value) => {
        const hex = value.trim().replace('#', '')
        return [0, 2, 4].map((offset) => Number.parseInt(hex.slice(offset, offset + 2), 16) / 255)
      }
      const luminance = (value) => {
        const [red, green, blue] = parseHex(value).map((channel) => channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4)
        return .2126 * red + .7152 * green + .0722 * blue
      }
      const style = getComputedStyle(document.getElementById('helios-app'))
      const foreground = luminance(style.getPropertyValue('--h-faint'))
      const background = luminance(style.getPropertyValue('--h-bg'))
      const selectors = '.home-message,.evidence-chips,.phase-tabs,.phase-registry,.exact-evidence,.strategy-library,.status-bar,.system-controls,.deck-nav button,.phase-tabs button,.exact-evidence button,.strategy-mini,.control-row button'
      const clipped = [...document.querySelectorAll(selectors)].filter((element) => (
        element.scrollHeight > element.clientHeight + 1 || element.scrollWidth > element.clientWidth + 1
      )).map((element) => ({
        label: element.getAttribute('aria-label') || element.className || element.tagName,
        client: [element.clientWidth, element.clientHeight],
        scroll: [element.scrollWidth, element.scrollHeight],
      }))
      return { faintContrast: (Math.max(foreground, background) + .05) / (Math.min(foreground, background) + .05), clipped }
    })
    assert.deepEqual({ h1: shell.h1, main: shell.main, fits: shell.fits }, { h1: 1, main: 1, fits: true })
    assert.ok(Math.abs(shell.width - 1536) <= 1 && Math.abs(shell.height - 1024) <= 1)
    assert.deepEqual(shell.destinations, ['home', 'test', 'strategies', 'live', 'settings'])
    assert.ok(shell.canvases.length >= 12 && shell.canvases.every((value) => value === 'true'), 'graphic canvases must stay out of the accessibility tree')
    assert.equal(shell.unsafeClaims, false)
    assert.equal(shell.graphNodes, 7)
    assert.equal(shell.settingsControls.length, 5)
    assert.ok(shell.settingsControls.every(({ type, disabled }) => type === 'button' && disabled === 'true'))
    assert.ok(shell.minimumPublicFont >= 11, `public panel copy must stay at least 11 px; saw ${shell.minimumPublicFont}`)
    assert.ok(readability.faintContrast >= 4.5, `faint public copy contrast missed AA: ${readability.faintContrast}`)
    assert.deepEqual(readability.clipped, [], `public panel copy must not clip: ${JSON.stringify(readability.clipped)}`)
    const expectedPanels = [
      ['home', 8, 353], ['test', 371, 282], ['strategies', 663, 283], ['live', 956, 251], ['settings', 1217, 300],
    ]
    shell.panels.forEach((panel, index) => {
      const [view, x, width] = expectedPanels[index]
      assert.equal(panel.view, view)
      assert.ok(Math.abs(panel.x - x) <= 4, `${view} x geometry drifted`)
      assert.ok(Math.abs(panel.width - width) <= 4, `${view} width geometry drifted`)
      assert.ok(Math.abs(panel.y - 64) <= 1 && Math.abs(panel.height - 409) <= 1, `${view} vertical geometry drifted`)
    })

    const keyboard = []
    for (const view of shell.destinations) {
      const selector = `[data-helios-view="home"] [data-view-target="${view}"]`
      await page.focus(selector)
      await page.keyboard.press('Enter')
      keyboard.push(await page.$eval(selector, (button) => ({
        view: document.getElementById('helios-app').dataset.activeView,
        current: button.getAttribute('aria-current'),
        hash: location.hash,
        focus: document.activeElement === button,
        outlineWidth: Number.parseFloat(getComputedStyle(button).outlineWidth),
      })))
    }
    assert.deepEqual(keyboard.map(({ view }) => view), shell.destinations)
    assert.ok(keyboard.every(({ view, current, hash, focus, outlineWidth }) => current === 'page' && hash === `#${view}` && focus && outlineWidth >= 2))

    const temporal = await page.evaluate(() => {
      const hashCanvas = (canvas) => {
        const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data
        let value = 2166136261
        for (let index = 0; index < pixels.length; index++) value = Math.imul(value ^ pixels[index], 16777619)
        return value >>> 0
      }
      const hashes = () => [...document.querySelectorAll('#helios-app canvas')].map(hashCanvas)
      window.__renderAt({ time: 2, paused: true })
      const first = hashes()
      window.__renderAt({ time: 8, paused: true })
      const later = hashes()
      window.__renderAt({ time: 2, paused: true })
      const repeat = hashes()
      const voice = {}
      for (const state of window.__heliosMotion.contract.voiceStates) {
        dispatchEvent(new CustomEvent('helios:voice-state', { detail: { state } }))
        window.__renderAt({ time: 4, paused: true })
        voice[state] = hashCanvas(document.querySelector('[data-helios-motion="voice"]'))
      }
      return {
        first, later, repeat, voice,
        contract: window.__heliosMotion.contract,
        probe2: window.__heliosMotion.probe(2),
        probe8: window.__heliosMotion.probe(8),
      }
    })
    assert.deepEqual(temporal.first, temporal.repeat, 'fixed-time t=2 must be byte-deterministic')
    assert.ok(temporal.first.some((value, index) => value !== temporal.later[index]), 't=2 and t=8 must differ')
    assert.equal(new Set(Object.values(temporal.voice)).size, 5, 'all five voice morphologies must be distinct')
    assert.deepEqual(temporal.contract.particle.stages, [.28, .62, .88])
    assert.deepEqual(temporal.contract.particle.guidance, [.026, .14, .17, .24])
    assert.equal(temporal.contract.chronosphere.shells, 7)
    assert.equal(temporal.contract.correlation.frontsPerSide, 6)
    assert.equal(temporal.contract.probability.bands, 7)
    assert.equal(temporal.probe2.particle.finiteValues, temporal.probe2.particle.valueCount)
    assert.ok(temporal.probe2.chronospherePhases.every((phase, index) => phase !== temporal.probe8.chronospherePhases[index]))
    for (const probe of [temporal.probe2, temporal.probe8]) {
      assert.ok(probe.probability.every((value, index, values) => !index || value < values[index - 1]), 'quantile bands must remain ordered')
      for (const values of probe.probabilitySamples) {
        assert.ok(values.every((value, index) => !index || value < values[index - 1]), 'quantile bands must not cross across the 43-point sweep')
      }
    }
    assert.ok(Math.abs((temporal.probe8.executionAngle - temporal.probe2.executionAngle) - 2.28) < 1e-9)

    const fixedFrames = {}
    await page.evaluate(() => dispatchEvent(new CustomEvent('helios:voice-state', { detail: { state: 'listening' } })))
    for (const time of [0, 2, 8, 12]) {
      await page.evaluate((value) => window.__renderAt({ time: value, paused: true }), time)
      if (evidenceDirectory) fixedFrames[time] = await page.screenshot({ type: 'webp', quality: 82 })
    }
    const regionClips = Object.fromEntries(shell.panels.map(({ view, x, y, width, height }) => [view, {
      x: Math.round(x), y: Math.round(y), width: Math.round(width), height: Math.round(height),
    }]))
    const regionWebps = {}
    if (evidenceDirectory) {
      for (const [view, clip] of Object.entries(regionClips)) {
        regionWebps[view] = await page.screenshot({ type: 'webp', quality: 82, clip })
      }
    }

    await page.goto(`http://127.0.0.1:${port}/?motionTime=12`, { waitUntil: 'networkidle0' })
    await page.evaluate(() => {
      document.getElementById('boot').classList.add('done')
      dispatchEvent(new CustomEvent('helios:voice-state', { detail: { state: 'listening' } }))
      window.__renderAt({ time: 12, paused: false })
    })
    await new Promise((resolve) => setTimeout(resolve, 450))
    const liveStatus = await page.evaluate(() => window.__heliosMotion.status())
    const liveFrame = evidenceDirectory ? await page.screenshot({ type: 'webp', quality: 82 }) : null
    const pauseStart = await page.evaluate(() => {
      window.__heliosMotion.pause()
      return window.__heliosMotion.status()
    })
    await new Promise((resolve) => setTimeout(resolve, 350))
    const pauseHeld = await page.evaluate(() => window.__heliosMotion.status())
    const pausedFrame = evidenceDirectory ? await page.screenshot({ type: 'webp', quality: 82 }) : null
    await page.evaluate(() => window.__heliosMotion.play())
    await new Promise((resolve) => setTimeout(resolve, 450))
    const resumeStatus = await page.evaluate(() => window.__heliosMotion.status())
    const resumedFrame = evidenceDirectory ? await page.screenshot({ type: 'webp', quality: 82 }) : null
    assert.equal(liveStatus.running, true)
    assert.equal(pauseStart.running, false)
    assert.equal(pauseHeld.running, false)
    assert.ok(Math.abs(pauseHeld.time - pauseStart.time) < 1e-9, 'paused motion time must hold')
    assert.equal(resumeStatus.running, true)
    assert.ok(resumeStatus.time > pauseHeld.time + .2, 'resumed motion time must advance')

    const hiddenBefore = await page.evaluate(() => window.__heliosMotion.status())
    const backgroundPage = await browser.newPage()
    await backgroundPage.goto('about:blank')
    await backgroundPage.bringToFront()
    await new Promise((resolve) => setTimeout(resolve, 350))
    const hiddenPaused = await page.evaluate(() => ({ ...window.__heliosMotion.status(), documentHidden: document.hidden }))
    await page.bringToFront()
    await new Promise((resolve) => setTimeout(resolve, 50))
    const hiddenReturn = await page.evaluate(() => ({ ...window.__heliosMotion.status(), documentHidden: document.hidden }))
    await new Promise((resolve) => setTimeout(resolve, 300))
    const hiddenResumed = await page.evaluate(() => window.__heliosMotion.status())
    await backgroundPage.close()
    assert.equal(hiddenPaused.documentHidden, true)
    assert.equal(hiddenPaused.running, false)
    assert.ok(hiddenPaused.time - hiddenBefore.time <= .12, 'hidden lifecycle must not accumulate elapsed motion')
    assert.equal(hiddenReturn.documentHidden, false)
    assert.equal(hiddenResumed.running, true)
    assert.ok(hiddenResumed.time > hiddenReturn.time + .12, 'visible lifecycle must resume motion')

    await page.close()
    await browser.close()
    browser = await puppeteer.launch(browserOptions)
    page = await browser.newPage()
    await page.setViewport({ width: 1536, height: 1024, deviceScaleFactor: 1 })
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }])
    await page.goto(`http://127.0.0.1:${port}/?motionTime=12`, { waitUntil: 'networkidle0' })
    await page.evaluate(() => {
      document.getElementById('boot').classList.add('done')
      dispatchEvent(new CustomEvent('helios:voice-state', { detail: { state: 'listening' } }))
      window.__heliosMotion.pause()
      window.__heliosMotion.play()
    })
    await new Promise((resolve) => setTimeout(resolve, 8000))
    const desktopMotion = await page.evaluate(() => window.__heliosMotion.status())
    assert.ok(desktopMotion.measuredFps >= 22, `desktop motion floor missed: ${JSON.stringify(desktopMotion)}`)
    assert.ok(desktopMotion.measuredFps <= 26.5, `desktop motion exceeded its 24 FPS contract: ${desktopMotion.measuredFps}`)
    assert.ok(desktopMotion.p95FrameMs <= 66.7, `desktop p95 interval missed: ${desktopMotion.p95FrameMs}`)
    assert.ok(desktopMotion.longFrameRatio <= .02, `desktop long-frame ratio missed: ${desktopMotion.longFrameRatio}`)
    assert.ok(desktopMotion.renderP95Ms <= 20, `desktop render budget missed: ${desktopMotion.renderP95Ms}`)

    await page.evaluate(() => window.__renderAt({ time: 12, paused: true }))
    const desktopPng = await page.screenshot({ type: 'png' })
    const desktopWebp = evidenceDirectory ? await page.screenshot({ type: 'webp', quality: 82 }) : null
    const referencePng = fs.readFileSync(new URL('../tests/fixtures/helios-v27-public-web-reference.png', import.meta.url))
    const comparison = await page.evaluate(async ({ referenceUrl, actualUrl, regionBounds }) => {
      const load = (source) => new Promise((resolve, reject) => {
        const image = new Image(); image.onload = () => resolve(image); image.onerror = reject; image.src = source
      })
      const [reference, actual] = await Promise.all([load(referenceUrl), load(actualUrl)])
      if (reference.width !== actual.width || reference.height !== actual.height) throw new Error('visual fixtures must have identical dimensions')
      const canvas = document.createElement('canvas'); canvas.width = reference.width; canvas.height = reference.height
      const context = canvas.getContext('2d', { willReadFrequently: true })
      context.drawImage(reference, 0, 0); const expected = context.getImageData(0, 0, canvas.width, canvas.height).data
      context.clearRect(0, 0, canvas.width, canvas.height); context.drawImage(actual, 0, 0); const observed = context.getImageData(0, 0, canvas.width, canvas.height).data
      const heat = context.createImageData(canvas.width, canvas.height)
      let absolute = 0, squared = 0, over24 = 0, over64 = 0
      for (let offset = 0; offset < expected.length; offset += 4) {
        let maximum = 0
        for (let channel = 0; channel < 3; channel++) {
          const difference = Math.abs(expected[offset + channel] - observed[offset + channel])
          absolute += difference; squared += difference * difference; maximum = Math.max(maximum, difference)
        }
        if (maximum > 24) over24++
        if (maximum > 64) over64++
        heat.data[offset] = maximum; heat.data[offset + 1] = maximum > 64 ? 26 : 0; heat.data[offset + 2] = 0; heat.data[offset + 3] = 255
      }
      context.putImageData(heat, 0, 0)
      const heatmap = canvas.toDataURL('image/png')
      context.clearRect(0, 0, canvas.width, canvas.height)
      context.globalAlpha = 1
      context.drawImage(reference, 0, 0)
      context.globalAlpha = .5
      context.drawImage(actual, 0, 0)
      context.globalAlpha = 1
      const overlay = canvas.toDataURL('image/png')
      const measure = ({ x, y, width, height }) => {
        let regionAbsolute = 0, regionSquared = 0, regionOver24 = 0, regionOver64 = 0
        for (let row = y; row < y + height; row++) {
          for (let column = x; column < x + width; column++) {
            const offset = (row * canvas.width + column) * 4
            let maximum = 0
            for (let channel = 0; channel < 3; channel++) {
              const difference = Math.abs(expected[offset + channel] - observed[offset + channel])
              regionAbsolute += difference
              regionSquared += difference * difference
              maximum = Math.max(maximum, difference)
            }
            if (maximum > 24) regionOver24++
            if (maximum > 64) regionOver64++
          }
        }
        const regionPixels = width * height
        return {
          x, y, width, height,
          mae: regionAbsolute / (regionPixels * 3),
          rmse: Math.sqrt(regionSquared / (regionPixels * 3)),
          over24Percent: regionOver24 / regionPixels * 100,
          over64Percent: regionOver64 / regionPixels * 100,
        }
      }
      const pixels = canvas.width * canvas.height
      return {
        width: canvas.width, height: canvas.height,
        mae: absolute / (pixels * 3), rmse: Math.sqrt(squared / (pixels * 3)),
        over24Percent: over24 / pixels * 100, over64Percent: over64 / pixels * 100,
        heatmap, overlay,
        regions: Object.fromEntries(Object.entries(regionBounds).map(([name, bounds]) => [name, measure(bounds)])),
      }
    }, {
      referenceUrl: `data:image/png;base64,${referencePng.toString('base64')}`,
      actualUrl: `data:image/png;base64,${Buffer.from(desktopPng).toString('base64')}`,
      regionBounds: regionClips,
    })
    assert.ok(comparison.mae <= 23, `visual MAE missed: ${comparison.mae}`)
    assert.ok(comparison.over24Percent <= 26, `visual >24 threshold missed: ${comparison.over24Percent}`)
    assert.ok(comparison.over64Percent <= 15, `visual >64 threshold missed: ${comparison.over64Percent}; graphics ${JSON.stringify(shell.graphics)}; regions ${JSON.stringify(comparison.regions)}`)

    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }])
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'networkidle0' })
    const reduced = await page.evaluate(async () => {
      const hash = (canvas) => {
        const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data
        let value = 2166136261
        for (let index = 0; index < pixels.length; index++) value = Math.imul(value ^ pixels[index], 16777619)
        return value >>> 0
      }
      const hashes = () => [...document.querySelectorAll('#helios-app canvas')].map(hash)
      const before = hashes(); await new Promise((resolve) => setTimeout(resolve, 350)); const after = hashes()
      return { before, after, status: window.__heliosMotion.status() }
    })
    assert.equal(reduced.status.reducedMotion, true)
    assert.equal(reduced.status.running, false)
    assert.deepEqual(reduced.before, reduced.after, 'reduced motion must hold every graphic at a fixed living frame')

    await page.close()
    await browser.close()
    browser = await puppeteer.launch(browserOptions)
    page = await browser.newPage()
    await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 })
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }])
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'networkidle0' })
    await page.evaluate(() => document.getElementById('boot').classList.add('done'))
    await new Promise((resolve) => setTimeout(resolve, 8000))
    const mobileMotion = await page.evaluate(() => window.__heliosMotion.status())
    assert.ok(mobileMotion.measuredFps >= 17, `mobile motion floor missed: ${JSON.stringify(mobileMotion)}`)
    assert.ok(mobileMotion.measuredFps <= 20.5, `mobile motion exceeded its 18 FPS contract: ${mobileMotion.measuredFps}`)
    assert.ok(mobileMotion.p95FrameMs <= 75, `mobile p95 interval missed: ${mobileMotion.p95FrameMs}`)
    assert.ok(mobileMotion.longFrameRatio <= .02, `mobile long-frame ratio missed: ${mobileMotion.longFrameRatio}`)
    await page.evaluate(() => window.__renderAt({ time: 12, paused: true }))
    const mobileHomeWebp = evidenceDirectory ? await page.screenshot({ type: 'webp', quality: 82 }) : null
    await page.focus('[data-helios-view="home"] [data-view-target="test"]')
    await page.keyboard.press('Enter')
    await new Promise((resolve) => setTimeout(resolve, 50))
    const mobileTest = await page.evaluate(() => {
      const canvas = document.querySelector('[data-helios-view="test"] canvas')
      const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data
      let paintedCanvasPixels = 0
      for (let offset = 3; offset < pixels.length; offset += 4) if (pixels[offset]) paintedCanvasPixels++
      return {
        fits: document.documentElement.scrollWidth <= document.documentElement.clientWidth,
        activeView: document.getElementById('helios-app').dataset.activeView,
        visible: [...document.querySelectorAll('[data-helios-view]')].filter((panel) => !panel.hidden).map((panel) => panel.dataset.heliosView),
        focusInsideHidden: Boolean(document.activeElement.closest('[hidden]')),
        paintedCanvasPixels,
        targets: [...document.querySelectorAll('[data-helios-view="test"] button')].filter((button) => button.getClientRects().length).map((button) => {
          const rect = button.getBoundingClientRect(); return [rect.width, rect.height]
        }),
        minimumPublicFont: Math.min(...[...document.querySelectorAll(
          '[data-helios-view="test"] .deck-head h2,[data-helios-view="test"] .graphic-label,[data-helios-view="test"] .deck-nav button,[data-helios-view="test"] .phase-tabs button,[data-helios-view="test"] .phase-registry,[data-helios-view="test"] .exact-evidence button',
        )].map((element) => Number.parseFloat(getComputedStyle(element).fontSize))),
      }
    })
    assert.deepEqual(mobileTest.visible, ['test'])
    assert.equal(mobileTest.activeView, 'test')
    assert.equal(mobileTest.fits, true)
    assert.equal(mobileTest.focusInsideHidden, false)
    assert.ok(mobileTest.paintedCanvasPixels > 0, 'newly visible mobile destination canvas must render while motion is paused')
    assert.ok(mobileTest.targets.every(([width, height]) => width >= 44 && height >= 44), 'mobile navigation targets must be at least 44 px')
    assert.ok(mobileTest.minimumPublicFont >= 11, 'mobile public panel copy must stay at least 11 px')
    const mobileTestWebp = evidenceDirectory ? await page.screenshot({ type: 'webp', quality: 82 }) : null

    const metrics = {
      generatedAt: new Date().toISOString(),
      oracleSha256: 'bc872bfb3b819e4e4e10dea3ede784cf5909a58f0d8b4989ea145439c9dcf6d2',
      viewport: { desktop: [1536, 1024], mobile: [390, 844] },
      visual: { mae: comparison.mae, rmse: comparison.rmse, over24Percent: comparison.over24Percent, over64Percent: comparison.over64Percent, regions: comparison.regions, thresholds: { mae: 23, over24Percent: 26, over64Percent: 15 } },
      motion: {
        desktop: desktopMotion, mobile: mobileMotion, deterministicT2: true, changedT2ToT8: true, uniqueVoiceStates: 5,
        livePauseResume: { live: liveStatus, pauseStart, pauseHeld, resumed: resumeStatus },
        hiddenLifecycle: { before: hiddenBefore, paused: hiddenPaused, returned: hiddenReturn, resumed: hiddenResumed },
      },
      accessibility: { keyboard, minimumPublicFont: shell.minimumPublicFont, faintContrast: readability.faintContrast, clipped: readability.clipped, reducedMotionHashCount: reduced.before.length },
      prelaunch: { pendingAnalyticsScripts: mobile.plausibleScripts, pendingCookies: mobile.cookies },
      responsive: mobileTest,
    }
    if (evidenceDirectory) {
      fs.mkdirSync(evidenceDirectory, { recursive: true })
      const fixedDirectory = path.join(evidenceDirectory, 'fixed-time')
      const regionDirectory = path.join(evidenceDirectory, 'regions')
      fs.mkdirSync(fixedDirectory, { recursive: true })
      fs.mkdirSync(regionDirectory, { recursive: true })
      fs.writeFileSync(path.join(evidenceDirectory, 'metrics.json'), `${JSON.stringify(metrics, null, 2)}\n`)
      fs.writeFileSync(path.join(evidenceDirectory, 'desktop-1536x1024.webp'), desktopWebp)
      fs.writeFileSync(path.join(evidenceDirectory, 'mobile-home-390x844.webp'), mobileHomeWebp)
      fs.writeFileSync(path.join(evidenceDirectory, 'mobile-test-390x844.webp'), mobileTestWebp)
      fs.writeFileSync(path.join(evidenceDirectory, 'desktop-diff-heatmap.png'), Buffer.from(comparison.heatmap.split(',')[1], 'base64'))
      fs.writeFileSync(path.join(evidenceDirectory, 'desktop-overlay.png'), Buffer.from(comparison.overlay.split(',')[1], 'base64'))
      for (const [time, frame] of Object.entries(fixedFrames)) fs.writeFileSync(path.join(fixedDirectory, `t-${time}.webp`), frame)
      for (const [view, frame] of Object.entries(regionWebps)) fs.writeFileSync(path.join(regionDirectory, `${view}.webp`), frame)
      fs.writeFileSync(path.join(evidenceDirectory, 'motion-live.webp'), liveFrame)
      fs.writeFileSync(path.join(evidenceDirectory, 'motion-paused.webp'), pausedFrame)
      fs.writeFileSync(path.join(evidenceDirectory, 'motion-resumed.webp'), resumedFrame)
    }
    console.log(`helios public web: visual MAE ${comparison.mae.toFixed(3)}, >24 ${comparison.over24Percent.toFixed(3)}%, >64 ${comparison.over64Percent.toFixed(3)}%; desktop ${desktopMotion.measuredFps.toFixed(2)} fps; mobile ${mobileMotion.measuredFps.toFixed(2)} fps: PASS`)
  } finally {
    await browser.close()
    await new Promise((resolve) => server.close(resolve))
  }
  console.log('landing manifest fallback + interactive erupting solar Apollo + mobile reduced-motion: PASS')
}
