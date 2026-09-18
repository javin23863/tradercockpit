import fs from 'node:fs';import path from 'node:path';import cp from 'node:child_process';import crypto from 'node:crypto';import {fileURLToPath,pathToFileURL} from 'node:url';
import {serve,publicFiles} from './reference-preview-server.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),docs=path.join(root,'docs');
const pp=process.env.TC_PUPPETEER_MODULE;const puppeteer=(await import(pp?pathToFileURL(path.resolve(pp)).href:'puppeteer')).default;
const output=process.env.TC_REFERENCE_EVIDENCE||path.join(root,'.github/evidence/reference-served');fs.mkdirSync(output,{recursive:true});
const before=publicFiles(docs),digest=x=>crypto.createHash('sha256').update(x).digest('hex');
const git=(...args)=>cp.execFileSync('git',args,{cwd:root,encoding:'utf8'}).trim();
const host=await serve(docs);let browser;const rows=[];
const views=['','#/learn','#/learn/monte-carlo','#/learn/checklist','#/platform/charts','#/platform/models','#/access?plan=Quant'];
const files=Object.keys(before).filter(p=>p.endsWith('.html'));
const route=p=>p==='index.html'?'':p.endsWith('/index.html')?p.slice(0,-10):p;
const slug=s=>s.replace(/[^a-z0-9]+/gi,'-').replace(/^-|-$/g,'')||'home';
const delay=n=>new Promise(resolve=>setTimeout(resolve,n));
try{
 browser=await puppeteer.launch({executablePath:process.env.TC_CHROME,headless:true,args:['--disable-dev-shm-usage']});
 const jobs=process.argv.includes('--home-only')?views:([...files.map(route),...views.slice(1)]);
 for(const url of jobs)for(const width of [1440,390]){
  const p=await browser.newPage();const errors=[],consoleErrors=[],external=[],httpFailures=[];
  p.on('pageerror',e=>errors.push(String(e)));p.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
  p.on('request',r=>{if(/^https?:/.test(r.url())&&!r.url().startsWith(host.base))external.push(r.url());});p.on('response',r=>{if(r.status()>=400)httpFailures.push({url:r.url().replace(host.base,''),status:r.status()});});
  await p.setViewport({width,height:width===390?844:1000,deviceScaleFactor:1,isMobile:width===390,hasTouch:width===390});
  let status=0;try{const response=await p.goto(host.base+url,{waitUntil:'domcontentloaded',timeout:15000});status=response.status();await p.evaluate(()=>document.fonts.ready);await delay(350);
   if(url===''||url.startsWith('#/'))await p.waitForFunction(()=>document.documentElement.dataset.commerce==='verified',{timeout:6000});
  }catch(e){errors.push(String(e));}
  const metrics=await p.evaluate(()=>{const visible=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none';};return {overflow:document.documentElement.scrollWidth>innerWidth+1,width:innerWidth,title:document.title,h1s:[...document.querySelectorAll('h1')].filter(visible).map(e=>e.textContent.trim()),brokenImages:[...document.images].filter(e=>e.loading!=='lazy'&&(!e.complete||!e.naturalWidth)).map(e=>e.getAttribute('src')),images:[...document.images].slice(0,5).map(e=>({src:e.getAttribute('src'),width:e.naturalWidth,complete:e.complete})),commerce:document.documentElement.dataset.commerce||null,product:document.querySelector('#product-state')?.textContent,hiddenWaitlist:document.querySelector('#waitlist-form')?.hidden,price:[...document.querySelectorAll('.price strong')].map(e=>e.textContent),scene:[...document.querySelectorAll('.scene-stack')].map(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};})};});
  const shot=slug(url)+'-'+width+'.png';
  if(url===''||url.startsWith('#/')){
   await p.screenshot({path:path.join(output,shot),fullPage:false});
   if(url==='') {await p.evaluate(async()=>{for(let y=0;y<document.documentElement.scrollHeight;y+=600){scrollTo(0,y);await new Promise(r=>setTimeout(r,60));}scrollTo(0,0);});await delay(250);await p.screenshot({path:path.join(output,'full-'+shot),fullPage:true});}
  }
  const bad=status!==200||errors.length>0||consoleErrors.length>0||httpFailures.length>0||external.length>0||metrics.overflow||metrics.h1s.length!==1||metrics.brokenImages.length>0;
  rows.push({url,width,status,errors,consoleErrors,httpFailures,external,...metrics,bad});console.log(JSON.stringify({url,width,bad,errors,httpFailures,overflow:metrics.overflow}));await p.close();
 }
 const after=publicFiles(docs);if(JSON.stringify(before)!==JSON.stringify(after))throw new Error('Publishing bytes changed during browser pass');
 const evidence=Object.fromEntries(fs.readdirSync(output).filter(n=>n.endsWith('.png')).map(n=>[n,digest(fs.readFileSync(path.join(output,n)))]));
 const receipt={schema:'tradercockpit.full-served-site/v1',scope:'COMPLETE_PUBLISHING_DOCS_TREE_OVER_LOOPBACK_HTTP_WITH_PRODUCTION_PREFIX',capturedAt:new Date().toISOString(),browser:await browser.version(),parentCommit:git('rev-parse','HEAD'),worktreeStatus:git('status','--porcelain'),publicFiles:before,publicDigest:digest(JSON.stringify(before)),count:rows.length,failures:rows.filter(r=>r.bad).length,rows,evidence,visualApproval:false,reviewReady:false};
 fs.writeFileSync(path.join(output,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({renders:receipt.count,failures:receipt.failures,publicDigest:receipt.publicDigest,output},null,2));if(receipt.failures)process.exitCode=1;
}finally{if(browser)await browser.close();await host.close();}
