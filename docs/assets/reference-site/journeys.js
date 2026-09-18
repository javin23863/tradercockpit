/* Native, offline page journeys. Hash routes work in the portable HTML and on
   static hosts. They do not call account, payment, analytics, or trading APIs. */
(() => {
  'use strict';
  const home = document.querySelector('#main');
  const main = document.querySelector('#journey-main');
  let data = {}, validCommerce = false;
  const plans = ['Core', 'Trader', 'Quant', 'ApolloPro'];
  document.addEventListener('tc:commerce', event => {
    const value = event.detail;
    validCommerce = value?.schema === 'public-commerce/v1' && value.status === 'prelaunch' &&
      value.plan?.currency === 'USD' && value.checkout?.enabled === false && value.checkout.url === null &&
      Array.isArray(value.tiers) && value.tiers.length === plans.length && plans.every((name,index) =>
        value.tiers[index]?.name===name && value.tiers[index].interval==='month' &&
        Number.isSafeInteger(value.tiers[index].unitAmount) && value.tiers[index].unitAmount>0);
    data = validCommerce ? value : {};
    if (location.hash.startsWith('#/access')) render(false);
  });
  const price = name => {
    const item = validCommerce && data.tiers.find(t => t.name === name);
    return item ? new Intl.NumberFormat('en-US', {style:'currency', currency:'USD', maximumFractionDigits:2, minimumFractionDigits:item.unitAmount % 100 ? 2 : 0}).format(item.unitAmount/100) : 'Unavailable';
  };
  const checks = [
    ['question','Define the question before examining the result.','Write what you are testing and what would count against your idea.'],
    ['inputs','Identify the data and its limitations.','Record the source, time window, symbols and transformations.'],
    ['rules','Keep the rules and costs explicit.','Retain the settings used to produce the result, including cost assumptions.'],
    ['discovery','Separate discovery from confirmation.','Record what data has already influenced your choices. Reusing it does not make it unseen.'],
    ['trace','Trace the displayed result to a source.','Check that the chart, labels and numbers refer to the same retained record.'],
    ['limits','Record what the evidence cannot establish.','A completed checklist is not proof of a strategy, release readiness or future performance.']
  ];
  const freshNotes = () => ({schema:'tradercockpit.research-notes/v1', question:'', notes:'', checks:Object.fromEntries(checks.map(([id])=>[id,false]))});
  let notes = freshNotes(), storageMessage = '', dirty = false;
  const STORE = 'tc-proof-notes-v1';
  const validNotes = value => value?.schema === 'tradercockpit.research-notes/v1' &&
    typeof value.question === 'string' && value.question.length <= 500 &&
    typeof value.notes === 'string' && value.notes.length <= 8000 &&
    value.checks && checks.every(([id])=>typeof value.checks[id] === 'boolean');
  try {
    const stored = localStorage.getItem(STORE);
    if (stored) {
      try {
        const parsed=JSON.parse(stored);
        if(!validNotes(parsed)) throw new Error('Invalid saved notes');
        notes={schema:parsed.schema,question:parsed.question,notes:parsed.notes,
          checks:Object.fromEntries(checks.map(([id])=>[id,parsed.checks[id]]))};
        storageMessage='Loaded the saved copy from this browser. Nothing was sent to a server.';
      } catch {storageMessage='Saved notes could not be read. The stored copy has not been changed. Import an exported notes file to recover them.';}
    }
  } catch {storageMessage='Browser storage is not available here. Notes stay in this session; export notes to keep a file.';}


  const arrow = '<span aria-hidden="true">↗</span>';
  const crumb = label => `<nav class="j-breadcrumb" aria-label="Breadcrumb"><a href="#top">Home</a><span aria-hidden="true">/</span><a href="#/learn">Learning</a><span aria-hidden="true">/</span><span>${label}</span></nav>`;
  const sourceLink = (file,label='Read the source material') => `<a class="j-source" href="${file}">${label} ${arrow}</a>`;
  const header = (eyebrow,title,description,breadcrumb='') => `${breadcrumb}<header class="j-heading"><p class="eyebrow">${eyebrow}</p><h1 tabindex="-1">${title}</h1><p class="j-lede">${description}</p></header>`;
  const next = (href,title,description) => `<a class="j-next" href="${href}"><span><small>${description}</small><strong>${title}</strong></span>${arrow}</a>`;

  function learning() {
    return `${header('TraderCockpit / learning','A clearer view of your research.','Start with a question. Understand the evidence. Keep the limitations in view.')}
    <section class="j-library-feature" aria-labelledby="learning-feature-title">
      <div class="j-library-image"><img src="assets/reference-site/laptop-scene.webp" alt="Illustrative research workstation" width="1024" height="314"><img src="assets/reference-site/laptop-screen.webp" alt="" width="1024" height="314"><span>Models · synthetic development data</span></div>
      <div class="j-library-copy"><p class="eyebrow">Start here</p><h2 id="learning-feature-title">One result.<br>More questions.</h2><p>A convincing picture is not the same as traceable evidence. Use a short checklist to record what you know—and what is still missing.</p><a class="button gold" href="#/learn/checklist">Open research checklist ${arrow}</a></div>
    </section>
    <section class="j-library" aria-labelledby="resource-heading"><div class="j-section-line"><h2 id="resource-heading">Choose your next question</h2><span>Guides &amp; concepts</span></div>
      <a class="j-resource" href="#/platform/charts"><span class="j-resource-number">01</span><img src="assets/reference-site/product-charts.webp" width="480" height="349" alt=""><div><small>Charts / guided reading</small><h3>What am I actually looking at?</h3><p>Distinguish the price panel, studies and test-data context.</p></div>${arrow}</a>
      <a class="j-resource" href="#/platform/models"><span class="j-resource-number">02</span><img src="assets/reference-site/product-models.webp" width="480" height="333" alt=""><div><small>Models / guided reading</small><h3>What does this diagnostic describe?</h3><p>Read the selected record without turning a loading map into a forecast.</p></div>${arrow}</a>
      <a class="j-resource j-resource-text" href="#/learn/monte-carlo"><span class="j-resource-number">03</span><div class="j-type-art" aria-hidden="true">MC<span>Paths ≠ predictions</span></div><div><small>Methods / concept</small><h3>How much does the path matter?</h3><p>Understand what resampling can—and cannot—tell you.</p></div>${arrow}</a>
    </section><p class="j-footnote">The product images in these guides are retained development captures with synthetic test data. They are not live-market views or release approval.</p>`;
  }
  function monteCarlo() {
    return `${header('Methods / Monte Carlo','A path is not a prediction.','A different ordering of observations can tell a different story. The assumptions behind the resampling matter as much as the picture.',crumb('Monte Carlo'))}
    <div class="j-reading-layout"><aside class="j-page-guide" aria-label="On this page"><p class="eyebrow">In this guide</p><button data-scroll-to="mc-question">The question</button><button data-scroll-to="mc-assumptions">The assumptions</button><button data-scroll-to="mc-limits">The limitation</button><a href="#/learn/checklist">Open checklist ${arrow}</a></aside>
      <article class="j-article"><section id="mc-question"><span class="j-section-index">01 / THE QUESTION</span><h2>Would another path change the interpretation?</h2><p>Monte Carlo methods repeatedly generate alternative outcomes using a stated randomization or resampling rule. In research, the useful comparison is between a distribution of possible paths under those rules and the one historical path you started with.</p><p>Ask whether the result depends heavily on a particular ordering, and which assumptions produce the changes you see.</p></section>
      <section id="mc-assumptions"><span class="j-section-index">02 / THE ASSUMPTIONS</span><h2>Keep the experiment visible.</h2><dl class="j-definition-list"><div><dt>What was resampled?</dt><dd>Know the observation unit, source window and the rule used to select or reorder it.</dd></div><div><dt>What structure was kept?</dt><dd>Naive resampling can remove dependence between observations or patterns of changing volatility.</dd></div><div><dt>What are the percentiles describing?</dt><dd>They describe outcomes produced under the chosen assumptions, not an unconditional forecast of a market.</dd></div></dl></section>
      <section id="mc-limits"><span class="j-section-index">03 / THE LIMITATION</span><h2>More simulated paths do not remove a weak assumption.</h2><p>A simulation does not prove future profitability. Read its distribution together with its inputs, resampling choices and the limitations of the original evidence.</p><div class="j-callout"><strong>Keep the distinction.</strong><p>Simulation output is conditional on the experiment. It is not a promise about what happens next.</p></div></section>
      <section class="j-watch"><p class="eyebrow">Continue with the method</p><h2>Monte Carlo block bootstrap</h2><p>Watch the existing explainer. YouTube connects only after you explicitly load the video.</p><button class="button glass" data-video>Watch explainer ${arrow}</button></section>
      ${sourceLink('learn/concepts/monte-carlo.html')}
      ${next('#/learn/checklist','Record the assumptions.','Apply this reading')}
      </article></div>`;
  }
  function captureGuide(kind) {
    const charts = kind === 'charts';
    const title = charts ? 'Read the chart. Keep the context.' : 'Read the model. Keep the limits.';
    const date = charts ? '16 September 2026' : '9 September 2026';
    const regions = charts ? [
      ['Context','The workspace identifies a historical result and the TC_PROBE test symbol. It is not a live market.'],
      ['Price & overlays','The main panel combines the price series with study overlays. The legend identifies the displayed studies.'],
      ['Separate panes','The lower panes separate the oscillator studies from the price scale. Their scales and units must not be confused.']
    ] : [
      ['Selected record','The captured view shows a retained PCA feature-structure diagnostic. Keep that record identity with any interpretation.'],
      ['Loading map','The map describes component weights for the selected diagnostic. It is not a probability of a future trade outcome.'],
      ['Connection state','The capture states that the provider is not configured. A completed diagnostic does not establish a live data connection.']
    ];
    return `${header(`Platform / ${charts?'Charts':'Models'}`,title,'A guided reading of an actual development capture—not a substitute for running the product.',crumb(charts?'Charts':'Models'))}
      <figure class="j-product-capture"><img src="${charts?'assets/reference-site/product-charts.webp':'assets/reference-site/product-models.webp'}" width="480" height="${charts?349:333}" alt="${charts?'Charts workspace using synthetic TC_PROBE data':'Models workspace showing a retained PCA loading map'}"><figcaption><span>${date} · Synthetic development test data · 480-pixel image</span><button class="button glass" data-capture="${kind}">Inspect source ${arrow}</button></figcaption></figure>
      <section class="j-capture-reading" aria-label="How to read the capture">${regions.map(([name,text],i)=>`<article><span class="j-section-index">0${i+1}</span><h2>${name}</h2><p>${text}</p></article>`).join('')}</section>
      <div class="j-callout"><strong>Evidence boundary</strong><p>The captured software is real. The dataset is synthetic. The image does not establish current release approval, live connectivity or performance.</p></div>
      ${next('#/learn/checklist','Keep a record of what you found.','Your next step')}`;
  }
  function checklist() {
    return `${header('Research / working notes','Make the evidence traceable.','Record the question, the inputs and the gaps. Checking an item records your observation; it does not verify a strategy.',crumb('Research checklist'))}
      <div class="j-notebook"><div class="j-note-main"><label for="research-question">Your research question</label><input id="research-question" maxlength="500" type="text" autocomplete="off" placeholder="What does this evidence actually support?">
      <fieldset class="j-checks"><legend>Evidence to record</legend>${checks.map(([id,title,description],index)=>`<label class="j-check"><input type="checkbox" data-check="${id}"><span class="j-check-number">0${index+1}</span><span><strong>${title}</strong><small>${description}</small></span></label>`).join('')}</fieldset>
      <label for="research-notes">Notes, sources and unresolved questions</label><textarea id="research-notes" rows="7" maxlength="8000" placeholder="Record references and limitations here…"></textarea>
      <div class="j-note-actions"><button class="button gold" data-save-notes>Save on this device</button><button class="button glass" data-export-notes>Export notes</button><label class="button glass j-file-label">Import notes<input type="file" accept=".json,application/json" data-import-notes aria-label="Import research notes JSON"></label></div><p data-note-status role="status" aria-live="polite"></p></div>
      <aside class="j-notebook-side"><p class="eyebrow">Your record</p><p class="j-check-progress" data-check-progress aria-live="polite"></p><p>Notes stay in this session until you save or export them. Nothing is sent to a server.</p><p>Saving uses this browser’s local storage. Clearing browser data can remove it; an exported file is a separate copy.</p><button class="j-text-button" data-reset-notes>Reset this checklist</button><div data-reset-confirm hidden><p>Clear this checklist and its saved browser copy? Export anything you need first.</p><button class="button glass" data-confirm-reset>Clear notes</button><button class="j-text-button" data-cancel-reset>Keep notes</button></div>${sourceLink('strategy-claim-audit-checklist.html','Original evidence checklist')}</aside></div>`;
  }
  function access(search) {
    const requested = new URLSearchParams(search).get('plan');
    const selected = plans.includes(requested) ? requested : 'Core';
    const options = plans.map(name=>`<a class="j-plan" href="#/access?plan=${name}" ${name===selected?'aria-current="true"':''}><span>${name}</span><strong>${price(name)}</strong><small>USD / month</small></a>`).join('');
    return `${header('Pricing & access','A plan for your research.','Explore four monthly plans and find your starting point. Checkout is closed.',`<nav class="j-breadcrumb" aria-label="Breadcrumb"><a href="#top">Home</a><span aria-hidden="true">/</span><span>Access</span></nav>`)}
      <nav class="j-plans" aria-label="Choose a monthly plan">${options}</nav>
      <section class="j-access-summary" aria-labelledby="access-summary-title"><div class="j-access-selection"><p class="eyebrow">Selected plan</p><h2 id="access-summary-title" data-selected-plan>${selected}</h2><p class="j-selected-price"><strong data-selected-price>${price(selected)}</strong><span>USD / month</span></p><button class="button gold" data-checkout disabled aria-describedby="checkout-explanation">Checkout unavailable</button></div><div class="j-access-explanation"><span class="j-status">${validCommerce ? 'Prelaunch · Local record verified' : 'Availability unverified'}</span><h2>Explore now. Subscribe later.</h2><p id="checkout-explanation">You can explore TraderCockpit information without an account or payment. Choosing a plan here does not start a subscription.</p><p>Before subscribing, review the confirmed features for your chosen plan and check the official access page for current availability.</p><a class="button glass" href="#public-status">Open waitlist and availability ${arrow}</a><p class="j-footnote">The waitlist is separate from paid access. Review its email-submission notice before joining.</p></div></section>
      <section class="j-access-notes"><article><h2>Monthly pricing.</h2><p>Prices are shown in US dollars per month. This page does not offer an annual discount or take payments.</p></article><article><h2>Plan details.</h2><p>Check the confirmed features and limits before choosing a subscription. Plan names alone do not describe everything included.</p></article><article><h2>Access updates.</h2><p>Follow the official access page for availability and account information. Prices load from the local public commerce record. No payment service is enabled here.</p></article></section>
      ${!validCommerce?'<p role="alert" class="j-callout">The local commerce record could not be verified. All checkout controls remain disabled.</p>':''}
      ${sourceLink('commerce-public.v1.json','Inspect the pinned commerce record')}`;
  }
  function unknown() {return `${header('Navigation','Page not found.','We could not find the page at this address. Nothing has been submitted.')}<div class="j-recovery"><a class="button gold" href="#top">Return to homepage</a><a class="button glass" href="#/learn">Open learning library</a></div>`;}

  function notesBindings() {
    const question = main.querySelector('#research-question'), text = main.querySelector('#research-notes');
    if(!question) return;
    question.value=notes.question; text.value=notes.notes;
    main.querySelectorAll('[data-check]').forEach(x=>{x.checked=notes.checks[x.dataset.check];});
    const status = main.querySelector('[data-note-status]');
    status.textContent=storageMessage;
    function progress() {main.querySelector('[data-check-progress]').textContent=`${checks.filter(([id])=>notes.checks[id]).length} of 6 items recorded — not a verdict.`;}
    function update() { notes.question=question.value; notes.notes=text.value; main.querySelectorAll('[data-check]').forEach(x=>{notes.checks[x.dataset.check]=x.checked;}); dirty=true; storageMessage='Changes are in this session only. Save or export to keep a copy.'; status.textContent=storageMessage; progress(); }
    question.addEventListener('input',update);text.addEventListener('input',update);
    main.querySelectorAll('[data-check]').forEach(x=>x.addEventListener('change',update)); progress();
    main.querySelector('[data-save-notes]').addEventListener('click',()=>{
      try {localStorage.setItem(STORE,JSON.stringify(notes));dirty=false;storageMessage='Saved on this device. Nothing was sent to a server.';}
      catch {storageMessage='Browser storage is not available here. Export notes to keep a file; your current session is unchanged.';}
      status.textContent=storageMessage;
    });
    main.querySelector('[data-export-notes]').addEventListener('click',()=>{
      const blob=new Blob([JSON.stringify(notes,null,2)+'\n'],{type:'application/json'});
      const url=URL.createObjectURL(blob), link=document.createElement('a');
      link.href=url;link.download='TraderCockpit-research-notes.json';document.body.append(link);link.click();link.remove();
      setTimeout(()=>URL.revokeObjectURL(url),30000);
      status.textContent='Notes file prepared. Check your browser downloads. Nothing was uploaded.';
    });
    main.querySelector('[data-import-notes]').addEventListener('change',async event=>{
      const file=event.target.files[0];if(!file)return;
      try {if(file.size>256000)throw new Error('size');const value=JSON.parse(await file.text());if(!validNotes(value))throw new Error('schema');
        notes={schema:value.schema,question:value.question,notes:value.notes,checks:Object.fromEntries(checks.map(([id])=>[id,value.checks[id]]))};
        dirty=true; storageMessage='Imported into this session. Save on this device to keep a browser copy.'; render(false);
      } catch {status.textContent='This is not a supported notes file. Existing notes have not been changed.';event.target.value='';}
    });
    main.querySelector('[data-reset-notes]').addEventListener('click',()=>{main.querySelector('[data-reset-confirm]').hidden=false;main.querySelector('[data-cancel-reset]').focus();});
    main.querySelector('[data-cancel-reset]').addEventListener('click',()=>{main.querySelector('[data-reset-confirm]').hidden=true;main.querySelector('[data-reset-notes]').focus();});
    main.querySelector('[data-confirm-reset]').addEventListener('click',()=>{notes=freshNotes();dirty=false;storageMessage='Checklist reset. Nothing was sent.';try{localStorage.removeItem(STORE);}catch{storageMessage+=' Browser storage could not be changed.';}render(false);main.querySelector('#research-question').focus();});
  }
  let lastHash = null;
  function render(focus=true) {
    const hash=location.hash;
    const isJourney=hash.startsWith('#/');
    home.hidden=isJourney;main.hidden=!isJourney;
    document.body.classList.toggle('in-journey',isJourney);
    const skip=document.querySelector('.skip');skip.href=isJourney?'#journey-main':'#main';
    document.querySelectorAll('.desktop-nav a, .mobile-nav a').forEach(link=>{
      if(((link.dataset.journey || link.getAttribute('href'))==='#/learn' && (hash.startsWith('#/learn')||hash.startsWith('#/platform'))))link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');
    });
    document.querySelectorAll('dialog[open]').forEach(dialog=>dialog.close());
    const mobile=document.querySelector('#mobile-nav'), menu=document.querySelector('.menu-toggle');
    if(mobile){mobile.hidden=true;menu?.setAttribute('aria-expanded','false');menu?.setAttribute('aria-label','Open navigation');}
    if(!isJourney){
      document.title='TraderCockpit — Quant research environment';
      if(lastHash?.startsWith('#/'))requestAnimationFrame(()=>{document.querySelector(hash==='#main'?'#main':'#hero-title')?.focus({preventScroll:true}); if(hash==='#top'||!hash)scrollTo({top:0,behavior:'instant'});});
      lastHash=hash;return;
    }
    const [route,search='']=hash.slice(1).split('?');
    const pages={'/learn':learning,'/learn/monte-carlo':monteCarlo,'/learn/checklist':checklist,'/platform/charts':()=>captureGuide('charts'),'/platform/models':()=>captureGuide('models'),'/access':()=>access(search)};
    main.innerHTML=`<div class="j-shell">${(pages[route]||unknown)()}</div>`;
    const title=main.querySelector('h1');
    document.title=route==='/learn/monte-carlo'?'Monte Carlo — TraderCockpit Learn':`${title.textContent} — TraderCockpit`;
    notesBindings();
    if(focus)requestAnimationFrame(()=>{scrollTo({top:0,behavior:'instant'});title.focus({preventScroll:true});});
    lastHash=hash;
  }
  document.addEventListener('click',event=>{
    if(event.target.closest('.skip') && document.body.classList.contains('in-journey')) {event.preventDefault();main.focus();return;}
    const button=event.target.closest('[data-scroll-to]');
    if(button){const target=document.getElementById(button.dataset.scrollTo);target?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});}
    const link=event.target.closest('a[href^="#/"]');
    if(link && link.getAttribute('href')===location.hash){event.preventDefault();render();}
  });
  addEventListener('hashchange',()=>render());
  render(false);
})();
