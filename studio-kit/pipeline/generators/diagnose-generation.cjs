const fs=require('fs');
const path=require('path');
const { callLLM, llmConfigured, notConfiguredMessage } = require('./llm.cjs');
const SKILLS=path.join(__dirname,'..','skills');
const OUT=path.join(__dirname,'output');
const SYSTEM='You are a world-class AI-video director diagnosing a failed generation. Follow the instructions exactly and output ONLY the requested markdown — no preamble.';

function argVal(argv,name,dflt){
  const flag='--'+name;
  for(let i=0;i<argv.length;i++){
    const a=argv[i];
    if(a===flag){ if(i+1<argv.length) return argv[i+1]; }
    else if(a.indexOf(flag+'=')===0){ return a.slice(flag.length+1); }
  }
  return dflt;
}

function nowIso(){ return new Date().toISOString(); }

function loadCraft(){
  let files=[];
  try{ files=fs.readdirSync(SKILLS).filter(f=>/\.md$/i.test(f)&&!/^00-/.test(f)).sort(); }
  catch(_){ files=[]; }
  if(!files.length) return null;
  return files.map(f=>{
    let body='';
    try{ body=fs.readFileSync(path.join(SKILLS,f),'utf8'); }catch(_){ body=''; }
    const name=f.replace(/\.md$/i,'');
    return '=== SKILL: '+name+' ===\n'+String(body).slice(0,1400);
  }).join('\n\n');
}

function loadEngineAdapter(engine){
  try{
    const p=path.join(__dirname,'engine-adapters.json');
    const data=JSON.parse(fs.readFileSync(p,'utf8'));
    if(!data||typeof data!=='object') return '';
    const table=(data.engines&&typeof data.engines==='object')?data.engines:data;
    const key=String(engine||'').toLowerCase();
    let e=table[engine]||table[key]||null;
    if(!e){
      for(const k of Object.keys(table)){
        if(String(k).toLowerCase()===key){ e=table[k]; break; }
      }
    }
    if(!e) return '';
    const body=(typeof e==='string')?e:JSON.stringify(e,null,2);
    return 'ENGINE ADAPTER ('+engine+') — obey these engine-specific rules:\n'+body;
  }catch(_){ return ''; }
}

function slugify(s){
  const u=String(s||'').toLowerCase()
    .replace(/[^a-z0-9]+/g,'-')
    .replace(/^-+|-+$/g,'')
    .slice(0,60);
  return u||'diagnosis';
}

async function main(){
  const issue=argVal(process.argv,'issue','');
  const prompt=argVal(process.argv,'prompt','');
  const engine=argVal(process.argv,'engine','seedance');
  const mode=argVal(process.argv,'mode','shots');

  if(String(issue).trim().length<6){
    console.error('Usage: node diagnose-generation.cjs --issue="<what looks wrong>" [--prompt="<the prompt that was used>"] [--engine=seedance] [--mode=shots|frames|pic|character]');
    process.exit(1);
  }

  const craft=loadCraft();
  if(!craft){
    console.error('No skills found in '+SKILLS+'. The kit ships them in pipeline/skills/, or run `node build-video-skills.cjs` first.');
    process.exit(2);
  }

  const adapter=loadEngineAdapter(engine);

  const taxonomy=[
    'plasticky-texture',
    'extra/invented-doors',
    'face/character-drift',
    'spatial-awareness (wrong camera placement / character entering from outside)',
    'lighting (plopped-in / too-bright / flat)',
    'composition/framing',
    'motion-not-landing',
    'prop-drift',
    'audio (music bleed)',
    'FPS/stutter'
  ].join(' · ');

  const diagPrompt=[
    'You are a world-class AI-video director diagnosing a FAILED AI generation and prescribing the exact prompt fix.',
    '',
    'DIAGNOSIS TARGET',
    'ISSUE (what looks wrong): '+issue,
    prompt?('PROMPT USED:\n"""\n'+prompt+'\n"""'):'PROMPT USED: (none provided)',
    'ENGINE: '+engine,
    'MODE: '+mode,
    '',
    'TAXONOMY (use these category names verbatim — pick one or more):',
    taxonomy,
    '',
    'YOUR JOB, IN ORDER:',
    '(a) NAME — pick the slop category/categories from the taxonomy above. State the name(s) first, in caps.',
    '(b) WHY — explain the root cause (not just the symptom). Tie it to a specific failure mode of the engine/model.',
    '(c) EXACT PROMPT FIX — give concrete text to ADD and to REMOVE. For each, cite which skill rule applies (by skill name and rule). End with a corrected prompt snippet, ready to paste.',
    '(d) BATCH / ITERATION MOVE — the one-line next move (e.g. "regenerate from scratch to lock", "camera further in", "add haze+grain+crush blacks", "drop to 1 subject").',
    '',
    'Be specific and decisive. No hedging. Every fix must cite a skill.',
    '',
    'REFERENCE — STUDIO SKILLS (compounded craft):',
    craft,
    adapter?('\n\nREFERENCE — '+adapter):''
  ].join('\n');

  const slug=slugify(issue);
  const fp=path.join(OUT,'diagnosis-'+slug+'.md');
  fs.mkdirSync(OUT,{recursive:true});

  // If an LLM is configured, run the diagnosis. Otherwise PASTE-MODE: save the ready-to-run diagnostic prompt.
  if(!llmConfigured()){
    const body=[
      '# Diagnosis (READY-TO-RUN PROMPT) — '+nowIso(),
      '',
      '**Issue:** '+issue,
      '',
      '**Engine:** '+engine+'  ·  **Mode:** '+mode,
      prompt?('**Prompt used:**\n```\n'+prompt+'\n```'):'',
      '',
      'Paste everything below into ChatGPT / Claude / any LLM to get the diagnosis + fix.',
      '',
      '---',
      '',
      diagPrompt
    ].filter(Boolean).join('\n');
    fs.writeFileSync(fp,body,'utf8');
    console.log(notConfiguredMessage(fp));
    return;
  }

  let out='';
  try{ out=await callLLM(SYSTEM,diagPrompt,{temperature:0.4,timeoutMs:200000}); }
  catch(e){ console.error('LLM call failed ('+((e&&e.message)||e)+').'); }

  const body=[
    '# Diagnosis — '+nowIso(),
    '',
    '**Issue:** '+issue,
    '',
    '**Engine:** '+engine+'  ·  **Mode:** '+mode,
    prompt?('**Prompt used:**\n```\n'+prompt+'\n```'):'',
    '',
    '---',
    '',
    (out&&out.trim())||'(no output — the LLM returned empty; try again)'
  ].filter(Boolean).join('\n');

  let wrote=true;
  try{
    fs.writeFileSync(fp,body,'utf8');
  }catch(e){
    wrote=false;
    console.error('write failed ('+((e&&e.message)||e)+') — printing diagnosis instead:');
    console.log(body);
  }
  if(wrote) console.log(fp);
}

main().catch(e=>{
  console.error('diagnose-generation failed:',(e&&e.message)?e.message:e);
  process.exit(1);
});
