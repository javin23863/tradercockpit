import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import assert from 'node:assert/strict';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),dir=path.join(root,'.github/evidence/reference-continuity-served');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
for(const name of ['reading-before-receipt.json','reading-after-receipt.json']){
 const p=path.join(dir,name),r=JSON.parse(fs.readFileSync(p,'utf8'));
 assert.equal(r.schema,'tradercockpit.reference-content-package/v2',name+' must distinguish generated vs packaged evidence');
 assert.ok(!Object.hasOwn(r,'evidence'),name+' must not imply omitted screenshots are packaged');
 assert.equal(r.generatedEvidence.retention,'ephemeral_full_run_not_committed');
 assert.equal(r.generatedEvidence.count,r.rows.length);
 assert.deepEqual(Object.keys(r.generatedEvidence.hashes).sort(),r.rows.map(x=>x.screenshot).sort());
 const manifest=crypto.createHash('sha256').update(Buffer.from(JSON.stringify(Object.entries(r.generatedEvidence.hashes).sort(([a],[b])=>a.localeCompare(b))))).digest('hex');
 assert.equal(r.generatedEvidence.manifestSha256,manifest,name+' generated evidence manifest hash drift');
 const generatedDigests=new Set(Object.values(r.generatedEvidence.hashes));
 for(const [file,digest] of Object.entries(r.packagedEvidence||{})){const f=path.join(dir,file);assert.ok(fs.existsSync(f),name+' packaged evidence missing: '+file);assert.equal(sha(f),digest,name+' packaged evidence hash drift: '+file);assert.ok(generatedDigests.has(digest),name+' packaged evidence is not from the generated browser run: '+file);}
}
const after=JSON.parse(fs.readFileSync(path.join(dir,'reading-after-receipt.json'),'utf8'));assert.ok(Object.keys(after.packagedEvidence).length>=8,'current reading receipt must package representative evidence');
console.log(JSON.stringify({receipts:2,currentPackaged:Object.keys(after.packagedEvidence).length,status:'PASS'},null,2));
