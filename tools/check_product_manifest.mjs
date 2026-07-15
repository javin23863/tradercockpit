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
assert.throws(() => validatePrelaunchConfig({ ...prelaunch, waitlist: { ...prelaunch.waitlist, status: 'active' } }), /username/)
assert.throws(() => validatePrelaunchConfig({
  ...prelaunch,
  analytics: { ...prelaunch.analytics, status: 'active', scriptSrc: 'https://example.com/tracker.js' },
}), /Plausible/)
console.log('prelaunch-config/v1: 3/3 PASS')

if (process.argv.includes('--browser')) {
  const docs = fileURLToPath(new URL('../docs/', import.meta.url))
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
  const browser = await puppeteer.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true })
  try {
    const page = await browser.newPage()
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
    }))
    assert.equal(mobile.fits, true)
    assert.equal(mobile.boot, 'none')

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
        label: canvas.getAttribute('aria-label'), visible, warm,
        socials: [...document.querySelectorAll('.social-link')].map((link) => [link.dataset.channel, link.href]),
      }
    })
    assert.match(organic.label, /solar Apollo/)
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
  } finally {
    await browser.close()
    await new Promise((resolve) => server.close(resolve))
  }
  console.log('landing manifest fallback + solar Apollo interaction + mobile reduced-motion: PASS')
}
