import assert from 'node:assert/strict';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {serve} from './reference-preview-server.mjs';
const docs=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../docs');
const host=await serve(docs,{prefix:'/'});
try {
  const robots=await fetch(new URL('/robots.txt',host.base));
  assert.equal(robots.status,200,'The custom-domain root must serve robots.txt');
  assert.match(await robots.text(),/Sitemap: https:\/\/tradercockpit\.app\/sitemap\.xml/);
  const sitemap=await (await fetch(new URL('/sitemap.xml',host.base))).text();
  const urls=[...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m=>m[1]);
  assert.ok(urls.length>30);
  for(const url of urls) {
    assert.ok(url.startsWith('https://tradercockpit.app/'));
    const response=await fetch(new URL(new URL(url).pathname,host.base));
    assert.equal(response.status,200,url+' must work after removing the project prefix');
  }
  console.log(`CUSTOM DOMAIN: PASS (${urls.length} sitemap destinations at root; live DNS/HTTPS still require activation)`);
} finally {await host.close();}
