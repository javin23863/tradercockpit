import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {serve} from './reference-preview-server.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const host=await serve(path.join(root,'docs'));
console.log('Local reference website: '+host.base);
console.log('Read-only loopback preview of the real docs tree. No deployment or checkout enablement.');
let closing=false;
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,async()=>{if(closing)return;closing=true;await host.close();});
