import { mountAnalytical3D } from './analytical-vtk.js';

(() => {
  'use strict';
  const IDS = ['strategy-universe-canvas','monte-carlo-canvas','robustness-canvas','correlation-canvas','distribution-canvas','regime-canvas','walk-forward-canvas','oos-canvas','drawdown-canvas','selection-canvas'];
  if (!IDS.some((id) => document.getElementById(id))) return;
  const TEAL='#3cfad2', RED='#e54a5a', CYAN='#3daed3', BLUE='#3b779a', WHITE='#f6f8fa', DARK='#07131b';
  const registry = new Map();
  const data = {};
  window.__tcResearchVTK = {surfaces:registry,data};

  function mulberry32(seed){return()=>{seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
  function gaussian(random){const u=Math.max(1e-9,random()),v=Math.max(1e-9,random());return Math.sqrt(-2*Math.log(u))*Math.cos(Math.PI*2*v)}
  function percentile(values,q){const s=[...values].sort((a,b)=>a-b),p=(s.length-1)*q,l=Math.floor(p),u=Math.ceil(p);return l===u?s[l]:s[l]*(u-p)+s[u]*(p-l)}
  function standardize(values){const mean=values.reduce((a,b)=>a+b,0)/values.length,v=values.reduce((a,b)=>a+(b-mean)**2,0)/values.length,sd=Math.sqrt(v)||1;return values.map((x)=>(x-mean)/sd)}
  const signed=(value,dead=.08)=>value>dead?TEAL:value<-dead?RED:CYAN;
  function bindChoice(selector, rebuild){
    const buttons=[...document.querySelectorAll(selector)];
    buttons.forEach((button)=>button.addEventListener('click',()=>{
      buttons.forEach((candidate)=>candidate.setAttribute('aria-pressed',String(candidate===button)));
      rebuild();
    }));
  }

  function prepare(id, axisLabels){
    const base=document.getElementById(id); if(!base) return null;
    let wrapper=base.closest('.lab-canvas-stack');
    if(!wrapper){wrapper=document.createElement('div');wrapper.className=`lab-canvas-stack lab-vtk-stack lab-vtk-stack-${id.replace('-canvas','')}`;base.before(wrapper);wrapper.append(base)}
    const overlay=document.createElement('div');overlay.className='lab-vtk-overlay';overlay.setAttribute('aria-hidden','true');wrapper.append(overlay);
    base.style.opacity='0';base.style.pointerEvents='none';
    let scene=null;
    const fallback=()=>{scene?.dispose?.();scene=null;overlay.remove();base.style.opacity='';base.style.pointerEvents='';wrapper.dataset.vtk='fallback';registry.delete(id);document.documentElement.dataset.researchRenderer=registry.size===IDS.length?'vtk-webgl':'hybrid-fallback'};
    const render=(spec)=>{
      try{
        scene?.dispose?.();overlay.replaceChildren();
        scene=mountAnalytical3D(overlay,{axisLabels,azimuth:34,elevation:23,...spec});
        const canvas=overlay.querySelector('canvas');canvas?.addEventListener('webglcontextlost',(event)=>{event.preventDefault();fallback()},{once:true});
        wrapper.dataset.vtk='active';registry.set(id,{scene,render});document.documentElement.dataset.researchRenderer=registry.size===IDS.length?'vtk-webgl':'hybrid-fallback';
      }catch{fallback()}
      return scene;
    };
    return {base,wrapper,overlay,render,get scene(){return scene},fallback};
  }

  function mountUniverse(){
    const view=prepare('strategy-universe-canvas',['Dispersion','Drawdown severity','IS / OOS disagreement']);if(!view)return;
    const random=mulberry32(23863),source=Array.from({length:150},(_,index)=>{const dispersion=random(),drawdown=random(),disagreement=random();return{index,dispersion,drawdown,disagreement,evidence:.35+random()*.65,family:index%3,point:[dispersion*2-1,drawdown*2-1,disagreement*2-1]}});let selected=0;
    const rebuild=()=>{const groups=[0,1,2].map((family)=>({points:source.filter(x=>x.family===family).map(x=>x.point),color:[TEAL,RED,CYAN][family],pointSize:7}));groups.push({points:[source[selected].point],color:WHITE,pointSize:15});view.render({points:groups});data.strategyUniverse={count:source.length,selected}};
    rebuild();document.querySelector('#universe-pause')?.setAttribute('hidden','');document.querySelector('#universe-reset')?.addEventListener('click',()=>{selected=0;rebuild();view.scene?.resetCamera()});document.querySelector('#candidate-prev')?.addEventListener('click',()=>{selected=(selected+source.length-1)%source.length;rebuild()});document.querySelector('#candidate-next')?.addEventListener('click',()=>{selected=(selected+1)%source.length;rebuild()});
  }

  function mountMonteCarlo(){
    const view=prepare('monte-carlo-canvas',['Synthetic step','Cumulative outcome','Path depth']);if(!view)return;let seed=1442953;
    const rebuild=()=>{const random=mulberry32(seed),paths=[];for(let p=0;p<64;p++){let value=0,path=[[0,0,(p/63-.5)*2]];for(let step=1;step<90;step++){value+=gaussian(random)*.12;path.push([step,value,(p/63-.5)*2])}paths.push(path)}const terminals=paths.map(x=>x.at(-1)[1]);view.render({normalizeAxes:true,lines:paths.map((points)=>({points,color:signed(points.at(-1)[1],.1),width:points===paths[32]?3:1}))});data.monteCarlo={seed,p10:percentile(terminals,.1),p50:percentile(terminals,.5),p90:percentile(terminals,.9)}};
    rebuild();document.querySelector('#mc-regenerate')?.addEventListener('click',()=>{seed+=97;rebuild()});
  }

  function robustnessValue(mode,u,v){const x=u-.5,y=v-.5;if(mode==='spike'){const d=(u-.58)**2+(v-.44)**2;return .12+.82*Math.exp(-62*d)}if(mode==='ridge'){const d=v-(.28+.42*u);return .15+.67*Math.exp(-32*d*d)*(.88+.08*Math.cos(u*Math.PI*4))}return .28+.52*Math.exp(-3.8*(x*x+y*y))+.035*Math.cos(u*Math.PI*4)*Math.cos(v*Math.PI*4)}
  function mountRobustness(){
    const view=prepare('robustness-canvas',['Parameter A','Parameter B','Response']);if(!view)return;const grid=Array.from({length:21},(_,i)=>i/20);
    const rebuild=()=>{const mode=document.querySelector('[data-surface-mode][aria-pressed="true"]')?.dataset.surfaceMode||'plateau',z=grid.map((v)=>grid.map((u)=>Math.max(0,Math.min(1,robustnessValue(mode,u,v)))));view.render({surface:{x:grid,y:grid,z,scalars:z,edges:false,palette:[[0,DARK],[.42,CYAN],[.72,TEAL],[1,WHITE]]}});data.robustness={mode,points:441,peak:Math.max(...z.flat())}};
    rebuild();bindChoice('[data-surface-mode]',rebuild);
  }

  function mountCorrelation(){
    const view=prepare('correlation-canvas',['Layout X','Layout Y','Layout Z']);if(!view)return;const source=[];for(let family=0;family<3;family++)for(let member=0;member<6;member++)source.push({family,member,label:`${String.fromCharCode(65+family)}${member+1}`});
    const pairNoise=(i,j)=>{const lo=Math.min(i,j)+1,hi=Math.max(i,j)+1,raw=Math.sin(lo*12.9898+hi*78.233)*43758.5453;return raw-Math.floor(raw)};const relation=(i,j)=>{if(i===j)return 1;const same=source[i].family===source[j].family,noise=pairNoise(i,j);if((i===5&&j===6)||(i===6&&j===5))return .74;return same?.64+noise*.31:-.28+noise*.68};
    const positions=source.map((node)=>{const angle=node.member/6*Math.PI*2+node.family*.33,r=1.2+node.family*.55;return[Math.cos(angle)*r,(node.family-1)*.72+Math.sin(angle*2)*.25,Math.sin(angle)*r]});let selected=0,focus=false;
    const rebuild=()=>{const points=[0,1,2].map((family)=>({points:positions.filter((_,i)=>source[i].family===family),color:[TEAL,RED,CYAN][family],pointSize:9}));points.push({points:[positions[selected]],color:WHITE,pointSize:16});const lines=[];for(let i=0;i<source.length;i++)for(let j=i+1;j<source.length;j++){const value=relation(i,j);if(Math.abs(value)<.62||focus&&(i!==selected&&j!==selected))continue;lines.push({points:[positions[i],positions[j]],color:value>=0?TEAL:RED,width:Math.abs(value)> .8?3:1})}view.render({points,lines});data.correlation={selected,focus,edges:lines.length}};
    rebuild();document.querySelector('#network-prev')?.addEventListener('click',()=>{selected=(selected+source.length-1)%source.length;rebuild()});document.querySelector('#network-next')?.addEventListener('click',()=>{selected=(selected+1)%source.length;rebuild()});document.querySelector('#network-focus')?.addEventListener('click',(event)=>{focus=!focus;event.currentTarget.setAttribute('aria-pressed',String(focus));rebuild()});
  }

  function distributionValues(mode){const random=mulberry32(mode==='symmetric'?5041:mode==='skewed'?9107:17713),values=[];for(let i=0;i<4000;i++){const z=gaussian(random);if(mode==='skewed'){const w=gaussian(random);values.push(.68*z+.33*(w*w-1))}else if(mode==='heavy')values.push(z*(random()<.075?3.2:1));else values.push(z)}return standardize(values)}
  function mountDistribution(){
    const view=prepare('distribution-canvas',['Standardized outcome','Count','Depth']);if(!view)return;const bins=34;
    const rebuild=()=>{const mode=document.querySelector('[data-distribution-mode][aria-pressed="true"]')?.dataset.distributionMode||'symmetric',values=distributionValues(mode),counts=new Array(bins).fill(0);for(const value of values){const i=Math.max(0,Math.min(bins-1,Math.floor((value+3.5)/7*bins)));counts[i]++}const threshold=Number(document.querySelector('#distribution-threshold')?.value??-1),max=Math.max(...counts,1);const lines=counts.map((count,i)=>{const x=-3.5+(i+.5)/bins*7;return{points:[[x,0,0],[x,count/max,0]],color:x<=threshold?RED:x>.5?TEAL:CYAN,width:5}});lines.push({points:[[threshold,0,.05],[threshold,1.05,.05]],color:WHITE,width:2});view.render({lines});data.distribution={mode,threshold,count:values.length}};
    rebuild();bindChoice('[data-distribution-mode]',rebuild);document.querySelector('#distribution-threshold')?.addEventListener('input',rebuild);
  }

  function mountRegime(){
    const view=prepare('regime-canvas',['Direction','Volatility','Liquidity stress']);if(!view)return;const random=mulberry32(90517),source=Array.from({length:96},(_,index)=>({index,direction:random()*2-1,volatility:random(),stress:random()}));let selected=0;
    const filtered=()=>{const mode=document.querySelector('[data-regime-filter][aria-pressed="true"]')?.dataset.regimeFilter||'all';return source.filter((p)=>mode==='low'?p.stress<.5:mode==='high'?p.stress>=.5:true)};
    const rebuild=()=>{const rows=filtered();if(!rows.some(x=>x.index===selected)&&rows.length)selected=rows[0].index;const groups=[{sign:'pos',color:TEAL,test:p=>p.direction>.25},{sign:'neg',color:RED,test:p=>p.direction<-.25},{sign:'neutral',color:CYAN,test:p=>Math.abs(p.direction)<=.25}].map(g=>({points:rows.filter(g.test).map(p=>[p.direction,p.volatility,p.stress]),color:g.color,pointSize:8}));const current=source[selected];groups.push({points:[[current.direction,current.volatility,current.stress]],color:WHITE,pointSize:15});view.render({points:groups});data.regime={selected,count:rows.length}};
    const move=(step)=>{const rows=filtered();if(!rows.length)return;let i=rows.findIndex(x=>x.index===selected);i=(Math.max(0,i)+step+rows.length)%rows.length;selected=rows[i].index;rebuild()};
    rebuild();bindChoice('[data-regime-filter]',rebuild);document.querySelector('#regime-prev')?.addEventListener('click',()=>move(-1));document.querySelector('#regime-next')?.addEventListener('click',()=>move(1));document.querySelector('#regime-rotate-left')?.addEventListener('click',()=>view.scene?.rotate(-18,0));document.querySelector('#regime-rotate-right')?.addEventListener('click',()=>view.scene?.rotate(18,0));
  }

  function mountWalkForward(){
    const view=prepare('walk-forward-canvas',['Synthetic time','Stage','Fold']);if(!view)return;let selected=3;
    const rebuild=()=>{const anchored=document.querySelector('[data-wf-mode][aria-pressed="true"]')?.dataset.wfMode==='anchored',lines=[];for(let i=0;i<7;i++){const trainStart=anchored?0:i*8,trainEnd=42+i*8,evalEnd=trainEnd+10,z=i;lines.push({points:[[trainStart,0,z],[trainEnd,0,z]],color:CYAN,width:i===selected?7:4});lines.push({points:[[trainEnd,.16,z],[evalEnd,.16,z]],color:TEAL,width:i===selected?9:5})}view.render({lines});data.walkForward={selected,anchored}};
    rebuild();bindChoice('[data-wf-mode]',rebuild);document.querySelector('#wf-prev')?.addEventListener('click',()=>{selected=(selected+6)%7;rebuild()});document.querySelector('#wf-next')?.addEventListener('click',()=>{selected=(selected+1)%7;rebuild()});
  }

  function mountOos(){
    const view=prepare('oos-canvas',['Process stage','Selection axis','Evidence depth']);if(!view)return;
    const rebuild=()=>{const repeated=document.querySelector('[data-oos-mode][aria-pressed="true"]')?.dataset.oosMode==='peek',random=mulberry32(44021),select=[0,0,0],lines=[];for(let i=0;i<36;i++){const y=-1+random()*2,z=-1+random()*2,bend=(random()-.5)*.7;lines.push({points:[[-3,y,z],[-1.2,y+bend,z*.45],select],color:i===11?TEAL:BLUE,width:i===11?4:1})}const evals=[[1,-.35,-.55],[1.65,.45,.25],[2.3,-.55,.65],[3,.12,-.15]];lines.push({points:[select,...evals],color:TEAL,width:4});if(repeated)evals.forEach((p,i)=>lines.push({points:[p,[-.2,(i-1.5)*.3,.2*(i-1.5)]],color:RED,width:3}));view.render({lines,points:[{points:[select],color:WHITE,pointSize:14}]});data.oos={mode:repeated?'peek':'clean',feedback:repeated?4:0}};
    rebuild();bindChoice('[data-oos-mode]',rebuild);
  }

  function drawdownPath(mode){return Array.from({length:120},(_,index)=>{const trend=100+index*.18,wave=1.8*Math.sin(index/7.5)+.9*Math.sin(index/3.9);let valley=0;if(mode==='long')valley=17*Math.exp(-(((index-64)/27)**2));else if(mode==='repeat')valley=13*Math.exp(-(((index-31)/8)**2))+16*Math.exp(-(((index-69)/10)**2))+12*Math.exp(-(((index-101)/8)**2));else valley=30*Math.exp(-(((index-61)/11)**2));return trend+wave-valley})}
  function mountDrawdown(){
    const view=prepare('drawdown-canvas',['Path step','Synthetic index','Drawdown depth']);if(!view)return;
    const rebuild=()=>{const mode=document.querySelector('[data-drawdown-mode][aria-pressed="true"]')?.dataset.drawdownMode||'deep',values=drawdownPath(mode),peaks=[];let peak=values[0];values.forEach(v=>{peak=Math.max(peak,v);peaks.push(peak)});const path=values.map((value,i)=>[i,value,-(peaks[i]-value)]),peakPath=peaks.map((value,i)=>[i,value,0]),lines=[{points:path,color:WHITE,width:3},{points:peakPath,color:TEAL,width:2}];for(let i=0;i<values.length;i+=3)if(peaks[i]-values[i]>.4)lines.push({points:[[i,values[i],-(peaks[i]-values[i])],[i,peaks[i],0]],color:RED,width:1});view.render({lines});data.drawdown={mode,max:Math.max(...values.map((v,i)=>(peaks[i]-v)/peaks[i]))}};
    rebuild();bindChoice('[data-drawdown-mode]',rebuild);
  }

  function mountSelection(){
    const view=prepare('selection-canvas',['Candidate scatter','Synthetic score','Selection stage']);if(!view)return;
    const rebuild=()=>{const exponent=Number(document.querySelector('#selection-family')?.value||6),familySize=2**exponent,random=mulberry32(91001+familySize*17),scores=Array.from({length:familySize},()=>gaussian(random)).sort((a,b)=>b-a),stages=[familySize,Math.max(1,Math.ceil(familySize*.25)),Math.max(1,Math.ceil(familySize*.05)),1],points=[];stages.forEach((count,stage)=>{const keep=scores.slice(0,count),visual=Math.min(keep.length,stage===0?160:stage===1?100:stage===2?60:1),r=mulberry32(familySize*97+stage*1301),rows=[];for(let i=0;i<visual;i++){const score=keep[visual===1?0:Math.floor(i*(keep.length-1)/Math.max(1,visual-1))];rows.push([(r()-.5)*2,score,stage])}points.push({points:rows,color:stage===3?WHITE:stage===2?TEAL:CYAN,pointSize:stage===3?16:7})});view.render({points});data.selection={familySize,observed:scores[0],stages}};
    rebuild();document.querySelector('#selection-family')?.addEventListener('input',rebuild);
  }

  mountUniverse();mountMonteCarlo();mountRobustness();mountCorrelation();mountDistribution();mountRegime();mountWalkForward();mountOos();mountDrawdown();mountSelection();
  document.documentElement.dataset.researchRenderer=registry.size===IDS.length?'vtk-webgl':'hybrid-fallback';
})();
