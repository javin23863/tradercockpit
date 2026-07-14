import assert from 'node:assert/strict'
import fs from 'node:fs'
import http from 'node:http'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { validateProductManifest } from '../docs/product-manifest.mjs'
import puppeteer from './visuals/puppeteer.mjs'

globalThis.location = { href: 'https://javin23863.github.io/tradercockpit/' }
const manifest = JSON.parse(fs.readFileSync(new URL('../docs/product-manifest.v1.json', import.meta.url), 'utf8'))
assert.equal(validateProductManifest(manifest).status, 'waitlist')
assert.throws(() => validateProductManifest(null), /schema/)
assert.throws(() => validateProductManifest({ ...manifest, schema: 'product-manifest/v2' }), /schema/)
assert.throws(() => validateProductManifest({ ...manifest, cta: { label: 'Buy', url: 'javascript:alert(1)' } }), /https or mailto/)
console.log('product-manifest/v1: 4/4 PASS')

if (process.argv.includes('--browser')) {
  const docs = fileURLToPath(new URL('../docs/', import.meta.url))
  let mode = 'valid'
  const server = http.createServer((request, response) => {
    const pathname = new URL(request.url, 'http://localhost').pathname
    if (pathname === '/product-manifest.v1.json') {
      if (mode === 'missing') { response.writeHead(404).end(); return }
      response.setHeader('Content-Type', 'application/json')
      response.end(mode === 'malformed' ? '{' : JSON.stringify(mode === 'unsupported' ? { ...manifest, schema: 'product-manifest/v2' } : manifest))
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
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'networkidle0' })
    const organic = await page.evaluate(() => {
      const canvas = document.getElementById('apollo-core')
      const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data
      let visible = 0
      for (let i = 3; i < pixels.length; i += 4) if (pixels[i]) visible++
      return { label: canvas.getAttribute('aria-label'), visible }
    })
    assert.match(organic.label, /bioluminescent Apollo/)
    assert.ok(organic.visible > 100, 'organic canvas should paint a visible state')

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
  console.log('landing manifest fallback + organic Apollo interaction + mobile reduced-motion: PASS')
}
