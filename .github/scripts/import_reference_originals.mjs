import fs from 'node:fs';import path from 'node:path';import cp from 'node:child_process';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const product=process.env.TC_PRODUCT_REPO;if(!product)throw new Error('Set TC_PRODUCT_REPO to an authorized existing product worktree');
const records=JSON.parse(fs.readFileSync(path.join(root,'.github/reference-site/provenance/product-captures.json'),'utf8')).captures;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const before=cp.execFileSync('git',['status','--porcelain'],{cwd:product,encoding:'utf8'});
const pending=[],overrides={};
for(const r of records){
 if(!['charts','models'].includes(r.id)||!/^([a-f0-9]{40})$/.test(r.ref))throw new Error('Invalid capture metadata');
 const raw=cp.execFileSync('git',['show',r.ref+':'+r.path],{cwd:product,maxBuffer:4000000});
 if(sha(raw)!==r.original_sha256||raw.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')throw new Error('Original PNG identity failed');
 const dimensions=[raw.readUInt32BE(16),raw.readUInt32BE(20)];if(JSON.stringify(dimensions)!==JSON.stringify(r.original_dimensions))throw new Error('Capture resolution failed');
 const name='assets/reference-site/original-'+r.id+'.png',dest=path.join(root,'docs',name);
 if(fs.existsSync(dest)&&sha(fs.readFileSync(dest))!==sha(raw))throw new Error('Conflicting original; no overwrite');
 pending.push({dest,raw});overrides[r.id]={src:name,width:dimensions[0],height:dimensions[1],hash:r.original_sha256};
}
if(cp.execFileSync('git',['status','--porcelain'],{cwd:product,encoding:'utf8'})!==before)throw new Error('Product worktree changed; no install');
for(const {dest,raw} of pending){if(!fs.existsSync(dest))fs.writeFileSync(dest,raw,{flag:'wx'});}
fs.writeFileSync(path.join(root,'docs/assets/reference-site/capture-overrides.js'),'/* Verified retained development captures; synthetic test data, not release approval. */\nwindow.TRADERCOCKPIT_CAPTURE_OVERRIDES=Object.freeze('+JSON.stringify(overrides)+');\n');
console.log(JSON.stringify({originals:overrides,productWorktreeUnchanged:true},null,2));
