// Every published page, served over loopback at desktop and phone width: loads clean, one h1, no sideways scroll,
// no broken image, nothing fetched from another host. Then the two controls a visitor relies on: plan lists and search.
// usage: TC_PUPPETEER_MODULE=<puppeteer-core entry> TC_CHROME=<browser> node test_site_served.mjs
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';import {fileURLToPath,pathToFileURL} from 'node:url';
import {serve} from './reference-preview-server.mjs';
const docs=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../docs');
const pp=process.env.TC_PUPPETEER_MODULE;const puppeteer=(await import(pp?pathToFileURL(path.resolve(pp)).href:'puppeteer')).default;
const pages=[];(function walk(d){for(const e of fs.readdirSync(d,{withFileTypes:true})){const p=path.join(d,e.name);if(e.isDirectory()){if(e.name!=='assets')walk(p);}else if(e.name.endsWith('.html')&&!fs.readFileSync(p,'utf8').includes('http-equiv="refresh"'))pages.push(path.relative(docs,p).split(path.sep).join('/').replace(/index\.html$/,''));}})(docs);
const host=await serve(docs);const browser=await puppeteer.launch({executablePath:process.env.TC_CHROME,headless:true,args:['--disable-dev-shm-usage']});const bad=[];
try{
 for(const width of [1440,390])for(const url of pages.sort()){
  const p=await browser.newPage();const problems=[];
  p.on('pageerror',e=>problems.push('error '+String(e).slice(0,120)));p.on('console',m=>{if(m.type()==='error')problems.push('console '+m.text().slice(0,120));});
  p.on('request',r=>{if(/^https?:/.test(r.url())&&!r.url().startsWith(host.base))problems.push('external '+r.url());});
  p.on('response',r=>{if(r.status()>=400&&url!=='404.html')problems.push(r.status()+' '+r.url().replace(host.base,''));});
  await p.setViewport({width,height:width===390?844:900,deviceScaleFactor:1,isMobile:width===390,hasTouch:width===390});
  await p.goto(host.base+url,{waitUntil:'load',timeout:20000});
  const m=await p.evaluate(()=>{const seen=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0;};return {over:document.documentElement.scrollWidth-innerWidth,h1:[...document.querySelectorAll('h1')].filter(seen).length,broken:[...document.images].filter(i=>i.complete&&!i.naturalWidth).map(i=>i.getAttribute('src')),small:[...document.querySelectorAll('.site-nav a,.site-nav button')].filter(e=>seen(e)&&e.getBoundingClientRect().height<40).length};});
  if(m.over>1)problems.push('sideways scroll '+m.over+'px');if(m.h1!==1)problems.push(m.h1+' visible h1');if(m.broken.length)problems.push('broken image '+m.broken[0]);if(width===390&&m.small)problems.push(m.small+' header targets under 40px');
  if(problems.length)bad.push(`${width} /${url}: ${problems.join('; ')}`);await p.close();
 }
 const p=await browser.newPage();await p.setViewport({width:1440,height:900});
 await p.goto(host.base+'pricing/',{waitUntil:'load'});await p.click('[data-access-plan="Core"]');await p.waitForSelector('#plan-core[open]',{timeout:3000});
 assert.match(await p.$eval('#plan-core',e=>e.textContent),/Apollo tasks at a time[\s\S]*Strategy Builder[\s\S]*Your work stays on your PC/,'a plan lists everything it includes');
 await p.goto(host.base+'learn/',{waitUntil:'load'});await p.click('.site-search-trigger');await p.waitForSelector('.site-search-dialog[open]');await p.type('#site-search-input','monte carlo');await p.waitForSelector('.site-search-result',{timeout:5000});
 await p.keyboard.press('Escape');assert.equal(await p.$('.site-search-dialog[open]'),null,'Escape closes search');
}finally{await browser.close();await host.close();}
if(bad.length){console.log('SERVED SITE: FAIL');for(const b of bad)console.log('- '+b);process.exit(1);}
console.log(`SERVED SITE: PASS (${pages.length} pages at 1440 and 390; plan lists and search work)`);
