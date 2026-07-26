#!/usr/bin/env node
// cdp_chart_shot.mjs — screenshot the live TradingView chart at a FORCED tall
// viewport, bypassing the short CDP webview (seen 1989x329 after an unmaximized
// relaunch — the `tv screenshot` region then renders a thin strip, useless for 16:9).
//
// Clear stale viewport emulation before capturing the Electron window's real compositor
// surface. Fail closed when the live window is too short for a usable chart. Then clip
// to the biggest canvas (the chart pane) so toolbars/sidebars are excluded.
//
//   node tools/visuals/cdp_chart_shot.mjs <out.png> [width] [height]
import puppeteer from './puppeteer.mjs'
const argv = process.argv.slice(2).filter((a) => a !== '--fit')
const FIT = process.argv.includes('--fit')  // Alt+R refit: ONLY on the first call after
// a viewport change. It can pop the "Continue your last replay?" modal, and resuming
// a SAVED replay switches the chart to the saved SYMBOL (hijacked an SPX shot to Brent).
const [out] = argv
if (!out) { console.error('usage: cdp_chart_shot.mjs <out.png> [w] [h] [--fit]'); process.exit(1) }

const AD = `(()=>{let n=0;for(const f of document.querySelectorAll('iframe[src*="safeframe"],iframe[src*="googlesyn"],iframe[src*="doubleclick"]')){let x=f;for(let i=0;i<6&&x.parentElement;i++){const cs=getComputedStyle(x.parentElement);if(cs.position==='fixed'||cs.position==='absolute'){x=x.parentElement}else break}x.style.display='none';n++}return n})()`

console.error('[cdp-shot] connect')
const browser = await puppeteer.connect({
  browserURL: 'http://127.0.0.1:9222',
  defaultViewport: null,
  protocolTimeout: 10000,
})
console.error('[cdp-shot] connected')
try {
  // TradingView Desktop exposes several internal/empty renderer targets. browser.pages()
  // waits while Puppeteer materializes every one of them, so one wedged renderer can stall
  // an otherwise healthy chart capture. Resolve only the live chart target.
  const target = browser.targets().find((candidate) => /\/chart\//.test(candidate.url()))
  if (!target) throw new Error('TradingView chart target not found on CDP :9222')
  console.error('[cdp-shot] chart target')
  const page = await target.page()
  if (!page) throw new Error('TradingView chart target did not resolve to a page')
  console.error('[cdp-shot] chart page')
  await page.bringToFront()
  const cdp = await page.createCDPSession()
  await cdp.send('Emulation.clearDeviceMetricsOverride')
  await new Promise((r) => setTimeout(r, 800))
  const viewport = await page.evaluate(() => ({ width: innerWidth, height: innerHeight }))
  if (viewport.width < 1200 || viewport.height < 700) {
    throw new Error(`TradingView chart viewport too small: ${viewport.width}x${viewport.height}`)
  }
  console.error(`[cdp-shot] viewport ${viewport.width}x${viewport.height}`)
  // park pointer off the chart canvas — a hovering crosshair swaps the OHLC header
  // to the hovered bar and draws a dashed crosshair into the shot; (5,5) hovers the
  // account button and pops its tooltip, so use empty toolbar space instead
  await page.mouse.move(800, 15)
  await page.evaluate(AD).catch(() => {})
  await new Promise((r) => setTimeout(r, 1800))   // reflow + repaint
  if (FIT) {
    // viewport change does NOT re-fit the chart (candles right-anchored, axis clips)
    // — Alt+R = TradingView "reset chart view"
    await page.keyboard.down('Alt'); await page.keyboard.press('KeyR'); await page.keyboard.up('Alt')
    await new Promise((r) => setTimeout(r, 1200))
  }
  // close (never Continue!) any modal — Continue resumes a SAVED replay and can
  // switch the chart to the saved symbol, hijacking the shot
  await page.evaluate(() => {
    const dlg = document.querySelector('[data-dialog-name], [class*="dialog"]')
    if (!dlg) return
    const x = dlg.querySelector('button[aria-label="Close"], [class*="close"]')
    if (x) x.click()
  }).catch(() => {})
  // clip to the largest canvas = the chart pane (excludes left toolbar / price-scale gutter)
  const box = await page.evaluate(() => {
    let best = null, area = 0
    for (const c of document.querySelectorAll('canvas')) {
      const r = c.getBoundingClientRect()
      if (r.width * r.height > area && r.width > 600 && r.height > 400) { area = r.width * r.height; best = r }
    }
    if (!best) return null
    // extend right to include the price axis (~70px), keep top header
    return { x: Math.max(0, best.x - 2), y: Math.max(0, best.y - 42),
             width: best.width + 78, height: best.height + 44 }
  })
  // re-park right before the shot — the OS cursor (operator's real mouse) can wander
  // onto the canvas during the reflow sleeps and repaint a crosshair
  await page.mouse.move(800, 15)
  await new Promise((r) => setTimeout(r, 300))
  await page.screenshot({
    path: out,
    captureBeyondViewport: false,
    ...(box ? { clip: box } : { fullPage: false }),
  })
  console.error('[cdp-shot] screenshot')
  console.log('shot', out, box ? `${Math.round(box.width)}x${Math.round(box.height)}` : 'fullview')
} finally {
  await browser.disconnect()
}
