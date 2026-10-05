import assert from 'node:assert/strict';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {serve} from './reference-preview-server.mjs';
const docs=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../docs');
const host=await serve(docs,{prefix:'/tradercockpit/'});
try {
  const robots=await fetch(new URL('robots.txt',host.base));
  assert.equal(robots.status,200,'The Pages project must serve the public robots file');
  assert.match(await robots.text(),/Sitemap: https:\/\/javin23863\.github\.io\/tradercockpit\/sitemap\.xml/);
  const sitemap=await (await fetch(new URL('sitemap.xml',host.base))).text();
  const urls=[...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m=>m[1]);
  assert.ok(urls.length>30);
  for(const url of urls) {
    assert.ok(url.startsWith('https://javin23863.github.io/tradercockpit/'));
    const response=await fetch(new URL(new URL(url).pathname,host.base));
    assert.equal(response.status,200,url+' must retain the current Pages project prefix');
  }
  console.log(`PUBLICATION URLS: PASS (${urls.length} sitemap destinations on the current Pages project; custom domain remains pending)`);
} finally {await host.close();}
