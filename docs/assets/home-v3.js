(() => {
  'use strict';
  const canvas = document.querySelector('#quant-universe-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  const pause = document.querySelector('#quant-universe-pause');
  const reset = document.querySelector('#quant-universe-reset');
  const readout = document.querySelector('#quant-universe-readout');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const TAU = Math.PI * 2;
  const random = (() => {
    let seed = 0x5eeda11;
    return () => {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  })();
  const points = Array.from({length: 210}, (_, i) => {
    const u = random(), v = random(), radius = .62 + random() * .42;
    const theta = TAU * u, phi = Math.acos(2 * v - 1);
    const score = random() * 2 - 1;
    return {i, score, weight:.25 + random()*.75,
      x:radius*Math.sin(phi)*Math.cos(theta),
      y:radius*Math.cos(phi), z:radius*Math.sin(phi)*Math.sin(theta)};
  });
  const bars = Array.from({length:58}, (_, i) => {
    const drift = Math.sin(i*.37)*.23 + Math.cos(i*.15)*.12;
    const delta = (random()-.46)*.5 + drift*.15;
    return {i, delta, height:.16+random()*.62, depth:random()*.9};
  });
  let yaw=-.52, pitch=.12, running=!reduced, raf=0, last=performance.now();  function fit() {
    const r=canvas.getBoundingClientRect(), dpr=Math.min(devicePixelRatio||1,2);
    const w=Math.max(300,Math.floor(r.width)), h=Math.max(430,Math.floor(r.height));
    if(canvas.width!==Math.floor(w*dpr)||canvas.height!==Math.floor(h*dpr)){
      canvas.width=Math.floor(w*dpr); canvas.height=Math.floor(h*dpr);
    }
    ctx.setTransform(dpr,0,0,dpr,0,0); return {w,h};
  }
  function rotate(p){
    const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
    const x=p.x*cy-p.z*sy, z=p.x*sy+p.z*cy;
    return {x,y:p.y*cp-z*sp,z:p.y*sp+z*cp};
  }
  function project(p,w,h,scale=.39){
    const q=rotate(p), depth=2.85-q.z, s=Math.min(w,h)*scale/depth;
    return {x:w*.51+q.x*s,y:h*.43-q.y*s,z:q.z,s};
  }
  function color(score,alpha=1){
    if(score>.12) return `rgba(73,239,154,${alpha})`;
    if(score<-.12) return `rgba(255,82,110,${alpha})`;
    return `rgba(61,232,255,${alpha})`;
  }
  function sphereBody(w,h){
    const r=Math.min(w,h)*.285;
    ctx.save();ctx.translate(w*.51,h*.43);ctx.scale(1,.93);
    const g=ctx.createRadialGradient(-r*.34,-r*.28,r*.04,0,0,r);
    g.addColorStop(0,'rgba(67,246,220,.24)');g.addColorStop(.25,'rgba(20,99,128,.18)');
    g.addColorStop(.68,'rgba(5,20,33,.9)');g.addColorStop(1,'rgba(0,4,10,.98)');
    ctx.beginPath();ctx.arc(0,0,r,0,TAU);ctx.fillStyle=g;ctx.shadowBlur=50;ctx.shadowColor='rgba(61,232,255,.2)';ctx.fill();ctx.shadowBlur=0;
    const edge=ctx.createLinearGradient(-r,0,r,0);edge.addColorStop(0,'rgba(255,82,110,.16)');edge.addColorStop(.5,'rgba(61,232,255,.03)');edge.addColorStop(1,'rgba(73,239,154,.18)');
    ctx.strokeStyle=edge;ctx.lineWidth=1.3;ctx.stroke();ctx.restore();
  }
  function sphereGrid(w,h){
    ctx.save(); ctx.lineWidth=.8;
    for(let lat=-2;lat<=2;lat++){
      ctx.beginPath();
      for(let i=0;i<=80;i++){
        const t=TAU*i/80, y=lat*.22, r=Math.sqrt(Math.max(.05,1-y*y));
        const s=project({x:r*Math.cos(t),y,z:r*Math.sin(t)},w,h,.42);
        i?ctx.lineTo(s.x,s.y):ctx.moveTo(s.x,s.y);
      }
      ctx.strokeStyle='rgba(61,232,255,.11)';ctx.stroke();
    }
    for(let lon=0;lon<8;lon++){
      const a=TAU*lon/8;ctx.beginPath();
      for(let i=0;i<=48;i++){
        const p=-Math.PI/2+Math.PI*i/48;
        const s=project({x:Math.cos(p)*Math.cos(a),y:Math.sin(p),z:Math.cos(p)*Math.sin(a)},w,h,.42);
        i?ctx.lineTo(s.x,s.y):ctx.moveTo(s.x,s.y);
      }
      ctx.strokeStyle='rgba(90,167,255,.075)';ctx.stroke();
    }
    ctx.restore();
  }
  function orbit(w,h,rx,ry,tilt,stroke){
    ctx.save();ctx.translate(w*.51,h*.43);ctx.rotate(tilt);ctx.beginPath();ctx.ellipse(0,0,rx,ry,0,0,TAU);ctx.strokeStyle=stroke;ctx.lineWidth=1;ctx.stroke();ctx.restore();
  }  function drawBars(w,h){
    const horizon=h*.69, baseY=h*.84, left=w*.08, span=w*.84;
    for(const b of bars){
      const x=left+span*b.i/(bars.length-1), perspective=.55+.45*(1-b.depth);
      const y=baseY-(baseY-horizon)*b.depth;
      const height=(35+b.height*105)*perspective, width=Math.max(2,5*perspective);
      ctx.strokeStyle=color(b.delta,.75);ctx.lineWidth=Math.max(1,1.3*perspective);
      ctx.beginPath();ctx.moveTo(x,y-height*.62);ctx.lineTo(x,y+height*.38);ctx.stroke();
      ctx.fillStyle=color(b.delta,.55);ctx.fillRect(x-width/2,y-height*.32,width,height*.48);
    }
    const ground=ctx.createLinearGradient(0,horizon,0,h);
    ground.addColorStop(0,'rgba(61,232,255,.07)');ground.addColorStop(1,'rgba(0,0,0,0)');
    ctx.fillStyle=ground;ctx.beginPath();ctx.moveTo(w*.04,horizon);ctx.lineTo(w*.96,horizon);ctx.lineTo(w*.82,h);ctx.lineTo(w*.18,h);ctx.closePath();ctx.fill();
  }
  function drawConnections(projected){
    ctx.save();ctx.lineWidth=.55;
    for(let i=0;i<projected.length;i+=5){
      const a=projected[i];
      let best=null,bestD=1e9;
      for(let j=i+1;j<Math.min(projected.length,i+18);j++){
        const b=projected[j], dx=a.x-b.x,dy=a.y-b.y,d=dx*dx+dy*dy;
        if(d<bestD){bestD=d;best=b;}
      }
      if(best&&bestD<9500){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(best.x,best.y);ctx.strokeStyle='rgba(61,232,255,.065)';ctx.stroke();}
    }
    ctx.restore();
  }
  function draw(){
    const {w,h}=fit();ctx.clearRect(0,0,w,h);
    const bg=ctx.createRadialGradient(w*.51,h*.43,10,w*.51,h*.43,Math.max(w,h)*.55);
    bg.addColorStop(0,'rgba(14,232,220,.13)');bg.addColorStop(.28,'rgba(35,129,255,.055)');bg.addColorStop(1,'rgba(0,0,0,0)');
    ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
    orbit(w,h,w*.39,h*.11,-.18,'rgba(54,241,193,.32)');
    orbit(w,h,w*.33,h*.08,.22,'rgba(255,82,110,.24)');
    orbit(w,h,w*.29,h*.055,-.42,'rgba(90,167,255,.18)');
    sphereBody(w,h);
    sphereGrid(w,h);
    const projected=points.map(p=>({...project(p,w,h,.42),p})).sort((a,b)=>a.z-b.z);
    drawConnections(projected);
    for(const q of projected){
      const alpha=.26+q.p.weight*.58, radius=Math.max(1.4,2.2+q.p.weight*3.5+(q.z+1)*.7);
      ctx.shadowBlur=12;ctx.shadowColor=color(q.p.score,.35);ctx.beginPath();ctx.arc(q.x,q.y,radius,0,TAU);ctx.fillStyle=color(q.p.score,alpha);ctx.fill();ctx.shadowBlur=0;
    }
    const core=ctx.createRadialGradient(w*.51,h*.43,2,w*.51,h*.43,Math.min(w,h)*.15);
    core.addColorStop(0,'rgba(230,255,255,.2)');core.addColorStop(.18,'rgba(61,232,255,.09)');core.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=core;ctx.fillRect(0,0,w,h);
    drawBars(w,h);
  }
  function frame(now){raf=0;const dt=Math.min(40,now-last);last=now;if(running&&!document.hidden)yaw+=dt*.000075;draw();if(running&&!document.hidden)raf=requestAnimationFrame(frame);}
  function start(){if(!running||document.hidden||raf)return;last=performance.now();raf=requestAnimationFrame(frame)}
  function stop(){if(raf)cancelAnimationFrame(raf);raf=0}
  pause?.addEventListener('click',()=>{running=!running;pause.textContent=running?'Pause motion':'Resume motion';pause.setAttribute('aria-pressed',String(!running));running?start():(stop(),draw())});
  reset?.addEventListener('click',()=>{yaw=-.52;pitch=.12;draw()});
  canvas.addEventListener('pointermove',e=>{if(reduced)return;const r=canvas.getBoundingClientRect();yaw=-.52+((e.clientX-r.left)/r.width-.5)*.7;pitch=.12-((e.clientY-r.top)/r.height-.5)*.32;if(!running)draw()},{passive:true});
  window.addEventListener('resize',draw,{passive:true});document.addEventListener('visibilitychange',()=>document.hidden?stop():running?start():draw());
  if(readout)readout.textContent='210 deterministic synthetic research points · green/red encode positive/negative synthetic outcomes · no market data';
  draw();if(reduced){pause?.setAttribute('hidden','')}else start();
})();
(async () => {
  'use strict';
  const rootUrl=new URL('../', document.currentScript?.src ?? location.href);
  const price=document.querySelector('[data-commerce-price]');
  const plan=document.querySelector('[data-commerce-plan]');
  const state=document.querySelector('[data-commerce-state]');
  const checkout=document.querySelector('[data-commerce-checkout]');
  try{
    const response=await fetch(new URL('commerce-public.v1.json',rootUrl),{credentials:'same-origin',cache:'no-store'});
    if(!response.ok)throw new Error('commerce unavailable');
    const data=await response.json();
    if(data?.schema!=='public-commerce/v1'||!Number.isInteger(data?.plan?.unitAmount))throw new Error('commerce invalid');
    const formatted=new Intl.NumberFormat('en-US',{style:'currency',currency:data.plan.currency,maximumFractionDigits:0}).format(data.plan.unitAmount/100);
    if(price)price.textContent=formatted;
    if(plan)plan.textContent=data.plan.name;
    if(state)state.textContent=data.checkout?.enabled?'Checkout available':'Prelaunch · checkout locked';
    if(checkout&&data.checkout?.enabled&&/^https:\/\/[^\s]+$/.test(data.checkout.url||'')){checkout.removeAttribute('disabled');checkout.textContent='Continue to secure checkout';checkout.addEventListener('click',()=>location.assign(data.checkout.url),{once:true});}
  }catch{if(state)state.textContent='Billing status unavailable';}

  try{
    const response=await fetch(new URL('social-links.v1.json',rootUrl),{credentials:'same-origin',cache:'force-cache'});
    if(!response.ok)throw new Error('social unavailable');
    const data=await response.json();
    document.querySelectorAll('[data-social]').forEach(link=>{
      const profile=data?.profiles?.[link.dataset.social];
      if(profile?.status==='verified'&&/^https:\/\/[^\s]+$/.test(profile.url||'')){
        link.href=profile.url;link.removeAttribute('aria-disabled');link.removeAttribute('tabindex');
      }else{link.removeAttribute('href');link.setAttribute('aria-disabled','true');link.setAttribute('tabindex','-1');}
    });
  }catch{}
})();
