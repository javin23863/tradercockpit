import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),continuity=path.join(root,'.github/evidence/reference-continuity-served'),generated=path.join(root,'.github/evidence/reference-content/after');
const selected={
 'docs--1440.png':'reading-docs-1440.png',
 'learn--390.png':'reading-learn-390.png',
 'methods--1440.png':'reading-methods-1440.png',
 'learn-concepts-monte-carlo-html-390.png':'reading-monte-carlo-390.png',
 'pricing--390.png':'reading-pricing-390.png',
 'support--1440.png':'reading-support-1440.png',
 'trust--1440.png':'reading-trust-1440.png',
 'updates--1440.png':'reading-updates-1440.png'
};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),fileSha=p=>sha(fs.readFileSync(p));
function manifestHash(hashes){return sha(Buffer.from(JSON.stringify(Object.entries(hashes).sort(([a],[b])=>a.localeCompare(b)))));}
function convert(receipt,packaged){
 if(receipt.schema==='tradercockpit.reference-content-package/v2')return receipt;
 if(receipt.schema!=='tradercockpit.reference-content/v1'||!receipt.evidence)throw new Error('Unsupported reading receipt');
 const hashes=receipt.evidence;
 const out={...receipt,schema:'tradercockpit.reference-content-package/v2'};
 delete out.evidence;
 out.generatedEvidence={retention:'ephemeral_full_run_not_committed',count:Object.keys(hashes).length,manifestSha256:manifestHash(hashes),hashes};
 out.packagedEvidence=packaged;
 return out;
}
function migrateExisting(name,useSelected){
 const p=path.join(continuity,name),r=JSON.parse(fs.readFileSync(p,'utf8')),packaged={};
 if(useSelected){
   const hashes=r.evidence||r.generatedEvidence?.hashes||{};
   for(const [src,dest] of Object.entries(selected)){const f=path.join(continuity,dest);if(!fs.existsSync(f))throw new Error('Selected packaged screenshot missing: '+dest);const digest=fileSha(f);if(hashes[src]!==digest)throw new Error('Selected packaged screenshot does not match generated hash: '+dest);packaged[dest]=digest;}
 }
 const out=convert(r,packaged);if(out.schema==='tradercockpit.reference-content-package/v2')out.packagedEvidence=packaged;
 fs.writeFileSync(p,JSON.stringify(out,null,2)+'\n');
}
if(process.argv.includes('--migrate-existing')){
 migrateExisting('reading-before-receipt.json',false);migrateExisting('reading-after-receipt.json',true);
 console.log(JSON.stringify({migrated:['reading-before-receipt.json','reading-after-receipt.json'],status:'PASS'}));process.exit(0);
}
const sourcePath=path.join(generated,'receipt.json'),source=JSON.parse(fs.readFileSync(sourcePath,'utf8'));
if(source.schema!=='tradercockpit.reference-content/v1')throw new Error('Generated receipt must be v1 full-run receipt');
for(const [name,digest] of Object.entries(source.evidence)){const f=path.join(generated,name);if(!fs.existsSync(f)||fileSha(f)!==digest)throw new Error('Generated reading evidence missing or changed: '+name);}
const packaged={};
for(const [src,dest] of Object.entries(selected)){const from=path.join(generated,src),to=path.join(continuity,dest);fs.copyFileSync(from,to);packaged[dest]=fileSha(to);}
const out=convert(source,packaged);fs.writeFileSync(path.join(continuity,'reading-after-receipt.json'),JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({generated:Object.keys(source.evidence).length,packaged:Object.keys(packaged).length,manifestSha256:out.generatedEvidence.manifestSha256,status:'PASS'},null,2));
