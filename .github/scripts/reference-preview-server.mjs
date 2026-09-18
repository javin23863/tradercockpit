import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
export function publicFiles(root) {
  const out={};
  function visit(dir) { for(const entry of fs.readdirSync(dir,{withFileTypes:true})) {const p=path.join(dir,entry.name);if(entry.isSymbolicLink())throw new Error('No symlinks in preview');if(entry.isDirectory())visit(p);else if(entry.isFile())out[path.relative(root,p).split(path.sep).join('/')]=crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');} }
  visit(root);return Object.fromEntries(Object.entries(out).sort(([a],[b])=>a.localeCompare(b)));
}
export async function serve(root) {
  root=fs.realpathSync(root);const prefix='/tradercockpit/';
  const types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.png':'image/png','.webp':'image/webp','.jpg':'image/jpeg','.svg':'image/svg+xml','.xml':'application/xml','.txt':'text/plain; charset=utf-8'};
  const server=http.createServer((req,res)=>{
    const finish=(status,body,type='text/plain; charset=utf-8')=>{res.writeHead(status,{'Content-Type':type,'X-Content-Type-Options':'nosniff','Cache-Control':'no-store'});res.end(req.method==='HEAD'?undefined:body);};
    if(!['GET','HEAD'].includes(req.method))return finish(405,'Read-only preview');
    let raw;try{raw=decodeURIComponent((req.url||'/').split('?')[0]);}catch{return finish(400,'Invalid URL');}
    if(raw==='/'||raw==='/tradercockpit'){res.writeHead(302,{Location:prefix});return res.end();}
    if(!raw.startsWith(prefix)||raw.includes('\\')||raw.includes('\0')||raw.split('/').includes('..'))return finish(404,'Not found');
    let rel=raw.slice(prefix.length);if(rel.endsWith('/')||!rel)rel+='index.html';
    let file=path.join(root,rel);
    if(fs.existsSync(file)&&fs.statSync(file).isDirectory()){res.writeHead(302,{Location:raw+'/'});return res.end();}
    if(!fs.existsSync(file)||!fs.statSync(file).isFile())return finish(404,fs.readFileSync(path.join(root,'404.html')),'text/html; charset=utf-8');
    if(!fs.realpathSync(file).startsWith(root+path.sep))return finish(403,'Forbidden');
    finish(200,fs.readFileSync(file),types[path.extname(file)]||'application/octet-stream');
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  return {server,base:`http://127.0.0.1:${server.address().port}${prefix}`,close:()=>new Promise(resolve=>{server.closeAllConnections();server.close(resolve);})};
}
