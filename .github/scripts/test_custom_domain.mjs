import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {serve} from './reference-preview-server.mjs';
const docs=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../docs');
const DOMAIN='trader-cockpit.com';
const SITE=`https://${DOMAIN}/`;
assert.equal(fs.readFileSync(path.join(docs,'CNAME'),'utf8').trim(),DOMAIN,'docs/CNAME must name the custom domain');
const host=await serve(docs,{prefix:'/'});
try {
  const robots=await fetch(new URL('robots.txt',host.base));
  assert.equal(robots.status,200,'The site must serve the public robots file');
  assert.match(await robots.text(),/Sitemap: https:\/\/trader-cockpit\.com\/sitemap\.xml/);
  const sitemap=await (await fetch(new URL('sitemap.xml',host.base))).text();
  const urls=[...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m=>m[1]);
  assert.ok(urls.length>30);
  for(const url of urls) {
    assert.ok(url.startsWith(SITE),url+' must be on the custom domain');
    const response=await fetch(new URL(new URL(url).pathname,host.base));
    assert.equal(response.status,200,url+' must be served from the domain root');
  }
  const stale=[];
  (function visit(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,entry.name);if(entry.isDirectory())visit(p);else if(/\.(html|xml|json|txt|mjs|js|webmanifest)$/.test(entry.name)&&fs.readFileSync(p,'utf8').includes('javin23863.github.io'))stale.push(path.relative(docs,p));}})(docs);
  assert.deepEqual(stale,[],'No published file may point at the old github.io address');
  console.log(`PUBLICATION URLS: PASS (${urls.length} sitemap destinations served from the root of ${DOMAIN})`);
} finally {await host.close();}
