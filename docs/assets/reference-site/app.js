(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  document.querySelectorAll('.screen-layer').forEach(image => image.addEventListener('error', () => { image.hidden = true; }));
  const detail = $('#detail-dialog'), body = $('#dialog-body');
  let returnFocus = null;
  function openDialog(dialog) {
    if (dialog.open) return;
    returnFocus = document.activeElement;
    if (typeof dialog.showModal !== 'function') return;
    dialog.showModal();
  }
  function closeDialog(dialog) { dialog.close(); }
  document.querySelectorAll('dialog').forEach(dialog => {
    dialog.querySelector('.close-dialog').addEventListener('click', () => closeDialog(dialog));
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const r = dialog.getBoundingClientRect();
      if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) closeDialog(dialog);
    });
    // Search inputs consume Escape in some browsers; close the modal explicitly.
    dialog.addEventListener('keydown', event => {
      if (event.key !== 'Escape') return;
      event.preventDefault(); event.stopPropagation(); closeDialog(dialog);
    });
    dialog.addEventListener('close', () => {
      dialog.querySelectorAll('iframe').forEach(frame => frame.remove());
      if (returnFocus instanceof HTMLElement && returnFocus.isConnected) returnFocus.focus();
    });
  });
  function show(title, kicker, html, wide = false) {
    detail.classList.toggle("capture-dialog", wide);
    $('#dialog-title').textContent = title;
    $('#dialog-kicker').textContent = kicker;
    // All markup is from the fixed, local strings below. No untrusted HTML enters here.
    body.innerHTML = html;
    openDialog(detail);
  }
  const features = Object.freeze({
    builder:['Strategy Builder','A development-build capture of the Builder Setup: where the search starts and its options. The app is in development and not yet released.'],
    charts:['Charts','Development capture, not an available capability. Inspect price, studies and volume. This development build shows Coinbase BTC/USD 15-minute historical bars, not a live market or a trading result.'],
    models:['Apollo beside Charts','Development capture, not an available capability. Apollo, the research assistant, sits beside the chart and sends what is on screen only when you press Ask. Historical bars, not a trading result.'],
    research:['Quant Models','A development-build capture of a Models study comparing exposure policies on a synthetic sample. It is not a trading result, and a fitted model is not a promise of future performance.']
  });
  // Capture details are fixed local metadata. No network request is made.
  const captures = Object.freeze({
    charts: {title:'Charts — development build', date:'8 October 2026',
      src:'assets/reference-site/product-charts.webp', width:480, height:285,
      path:'assets/reference-site/original-charts.png',
      hash:'e0d15fd681f288beaa9465c02b0834d6d9ff015a4c1601c6dcff103ea9d3cde0',
      note:'Coinbase BTC/USD 15-minute historical bars in a development build. The room display shows a crop of this chart workspace; this inspector shows the entire capture. It is not a trading result or a live market.'},
    models: {title:'Apollo beside Charts — development build', date:'8 October 2026',
      src:'assets/reference-site/product-models.webp', width:480, height:285,
      path:'assets/reference-site/original-models.png',
      hash:'ead9665eb3bc3996945bcd32ace49e8139ce0c353dc5ac64d571988b55b0870e',
      note:'The same historical BTC/USD bars with the Apollo panel open in a development build. Apollo receives the on-screen summary only when you press Ask. It is not a trading result or a live market.'}
  });
  function inspectCapture(key, switching = false) {
    const preview = captures[key];
    if (!preview) return;
    const supplied = window.TRADERCOCKPIT_CAPTURE_OVERRIDES?.[key];
    const expectedSize = [1600,950];
    const hasOriginal = supplied?.src === `assets/reference-site/original-${key}.png` &&
      supplied.hash === preview.hash && supplied.width===expectedSize[0] && supplied.height===expectedSize[1];
    const record = hasOriginal ? {...preview,src:supplied.src,width:supplied.width,height:supplied.height} : preview;
    const sizeDescription = hasOriginal ? `${record.width} × ${record.height} · full-size capture` : `${preview.width}-pixel preview · original not installed locally`;
    const origin = ''; // Full-size captures are served from this site.
    const tabs = Object.keys(captures).map(k => `<button class="capture-choice" data-capture-choice="${k}" aria-pressed="${k===key}">${k==='charts'?'Charts':'Apollo'}</button>`).join('');
    show(record.title, 'Development build / historical market bars',
      `<div class="capture-switch" aria-label="Choose capture">${tabs}</div>
       <div class="capture-scale" aria-label="Image scale"><button class="capture-choice" data-capture-scale="fit" aria-pressed="true">Fit screen</button><button class="capture-choice" data-capture-scale="native" aria-pressed="false">100% size</button></div>
       <figure class="capture-evidence" tabindex="0" aria-label="Product capture; scroll horizontally at 100 percent size"><img class="detail-media capture-media" src="${record.src}" width="${record.width}" height="${record.height}" alt="${record.title}"><figcaption>${record.date} · ${sizeDescription}</figcaption></figure>
       <p>${record.note}</p><a class="button glass" href="#/platform/${key}">Read this screen guide →</a><a class="button glass" href="${origin+record.path}" target="_blank" rel="noopener noreferrer">Full-size capture ↗</a><p class="capture-limit">The surrounding room is illustrative artwork. The screens are captures of a development build, not a live application or release approval. A reduced preview is used only if the full-size capture cannot be loaded.</p>`, true);
    const frame=body.querySelector('.capture-evidence'),image=body.querySelector('.capture-media');
    body.querySelectorAll('[data-capture-scale]').forEach(button=>button.addEventListener('click',()=>{
      const native=button.dataset.captureScale==='native';
      frame.classList.toggle('native-scale',native);
      image.style.width=native ? `${image.naturalWidth||record.width}px` : '';
      body.querySelectorAll('[data-capture-scale]').forEach(x=>x.setAttribute('aria-pressed',String(x===button)));
    }));
    image.addEventListener('error',()=>{
      if(!hasOriginal || image.dataset.fallback) return;
      image.dataset.fallback='true'; image.src=preview.src;
      image.width=preview.width;image.height=preview.height;image.style.width='';
      frame.classList.remove('native-scale');
      frame.querySelector('figcaption').textContent=`${record.date} · original unavailable; ${preview.width}-pixel preview`;
      body.querySelectorAll('[data-capture-scale]').forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.captureScale==='fit')));
    });
    body.querySelectorAll('[data-capture-choice]').forEach(button => button.addEventListener('click', () => inspectCapture(button.dataset.captureChoice, true)));
    if (switching) body.querySelector(`[data-capture-choice="${key}"]`).focus();
  }
  document.addEventListener('click', event => { const button=event.target.closest('[data-capture]'); if(button) inspectCapture(button.dataset.capture); });
  document.querySelectorAll('[data-feature]').forEach(b => b.addEventListener('click', () => {
    const key = b.dataset.feature, entry = features[key];
    if (!entry) return;
    if (Object.hasOwn(captures, key)) { inspectCapture(key); return; }
    show(entry[0], 'Platform overview', `<img class="detail-media" src="assets/reference-site/${key}.webp" alt="Development-build capture" width="450" height="232"><p>${entry[1]}</p><a class="button glass" href="docs/">Read product documentation ↗</a>`);
  }));
  document.addEventListener('click', event => {
    if (!event.target.closest('[data-video]')) return;
    show('Monte Carlo block bootstrap', 'Research explainer', '<p>This existing explainer discusses plausible historical paths. It is not a demonstration of every product feature.</p><div class="video-box"><button class="button gold" id="load-video">Load video from YouTube</button></div><p>Loading the video connects to YouTube. No video request is made before you press the button.</p>');
    $('#load-video').addEventListener('click', () => {
      const frame = document.createElement('iframe');
      frame.title = 'Monte Carlo block bootstrap explainer';
      frame.src = 'https://www.youtube-nocookie.com/embed/BgDFFr6o64Q?rel=0';
      frame.referrerPolicy = 'strict-origin-when-cross-origin';
      frame.allow = 'encrypted-media; picture-in-picture';
      frame.allowFullscreen = true;
      $('.video-box').replaceChildren(frame);
    });
  });
  document.querySelectorAll('[data-provenance]').forEach(b => b.addEventListener('click', () => show('About this page', 'Where the pictures come from', '<p>The room, mountains, furniture and laptop are illustrative artwork.</p><p>The screens on the monitor and the laptop are <strong>captures of a TraderCockpit development build</strong> showing historical Coinbase BTC/USD bars. They are not live feeds or evidence of trading performance.</p><p>Use the screen inspectors to view each complete capture.</p><p>Scene motion is decorative, can be paused, and respects reduced-motion preferences.</p><p>The Windows app is in development. We’ll release it when it’s ready. Checkout is closed.</p>')));
  const menu = $('.menu-toggle'), mobileNav = $('#mobile-nav');
  function closeMenu() { mobileNav.hidden = true; menu.setAttribute('aria-expanded','false'); menu.setAttribute('aria-label','Open navigation'); }
  menu.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open));
    menu.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    mobileNav.hidden = !open;
  });
  mobileNav.querySelectorAll('a').forEach(a => a.addEventListener('click', closeMenu));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') { closeMenu(); menu.focus(); }
  });
  const searchItems = [
    ['Platform','#platform','environment workflow'],['Features','#features','capabilities'],['Pricing','#pricing','plans core trader quant apollopro'],['Learning','#/learn','guides methods library'],
    ['Monte Carlo uncertainty','#/learn/monte-carlo','methods resampling assumptions simulation'],['Research checklist','#/learn/checklist','notes evidence questions source'],['Development status','#public-status','development release status'],['Read Charts','#/platform/charts','capture guide price studies'],['Read Apollo','#/platform/models','assistant capture guide on screen'],
    ...Object.entries(features).map(([key,entry]) => [entry[0],`#${key}`,entry[1]])
  ];
  function search() {
    const q = $('#search-input').value.trim().toLowerCase();
    const matches = searchItems.filter(item => `${item[0]} ${item[2]}`.toLowerCase().includes(q));
    $('#search-status').textContent = `${matches.length} ${matches.length === 1 ? 'result' : 'results'}`;
    const result = $('#search-results'); result.replaceChildren();
    matches.forEach(([label,href]) => {
      const link = document.createElement('a'); link.href=href; link.textContent=label+' →';
      link.addEventListener('click', () => closeDialog($('#search-dialog'))); result.append(link);
    });
  }
  document.querySelectorAll('[data-search]').forEach(button => button.addEventListener('click', () => { const fromMobile = !!button.closest('.mobile-nav'); closeMenu(); openDialog($('#search-dialog')); if (fromMobile) returnFocus = menu; search(); $('#search-input').focus(); }));
  $('#search-input').addEventListener('input', search);
  const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
  const motionToggle = document.querySelector('[data-motion-toggle]');
  const scenes = [...document.querySelectorAll('.scene-stack')];
  const finePointer = matchMedia('(hover: hover) and (pointer: fine)');
  let motionRequested = true, frameId = 0;
  let pointerX = 0, pointerY = 0, pointerScene = null;
  function motionAllowed() { return motionRequested && !motionPreference.matches && !document.hidden; }
  function resetScenes() { scenes.forEach(scene => { scene.style.transform = ''; }); }
  function renderMotion() {
    frameId = 0;
    if (!motionAllowed()) { resetScenes(); return; }
    // Read all geometry first; write the paired screen and artwork as ONE layer.
    const boxes = scenes.map(scene => scene.parentElement.getBoundingClientRect());
    const states = boxes.map((box, i) => {
      if (box.bottom < 0 || box.top > innerHeight) return '';
      const progress = Math.max(0, Math.min(1, scrollY / Math.max(1, innerHeight)));
      const dy = -progress * 3 + (pointerScene === scenes[i] ? pointerY * 3 : 0);
      const dx = pointerScene === scenes[i] ? pointerX * 4 : 0;
      if (Math.abs(dx) + Math.abs(dy) < .01) return '';
      return `translate3d(${dx.toFixed(3)}px,${dy.toFixed(3)}px,0) scale(1.016)`;
    });
    scenes.forEach((scene, i) => { scene.style.transform = states[i]; });
  }
  function scheduleMotion() { if (!frameId) frameId = requestAnimationFrame(renderMotion); }
  function updateMotionControl() {
    const active = motionRequested && !motionPreference.matches;
    motionToggle.hidden = false;
    motionToggle.disabled = motionPreference.matches;
    motionToggle.setAttribute('aria-pressed', String(active));
    motionToggle.textContent = motionPreference.matches ? 'Reduced motion' : active ? 'Motion on' : 'Motion off';
    if (!active) { if (frameId) cancelAnimationFrame(frameId); frameId=0; resetScenes(); }
  }
  motionToggle.addEventListener('click', () => { motionRequested = !motionRequested; updateMotionControl(); if (motionRequested) scheduleMotion(); });
  scenes.forEach(scene => {
    const region = scene.closest('.hero, .platform-scene');
    region.addEventListener('pointermove', event => {
      if (!motionAllowed() || !finePointer.matches) return;
      const box = region.getBoundingClientRect();
      pointerX = Math.max(-.5, Math.min(.5, (event.clientX-box.left)/box.width-.5));
      pointerY = Math.max(-.5, Math.min(.5, (event.clientY-box.top)/box.height-.5));
      pointerScene=scene; scheduleMotion();
    }, {passive:true});
    region.addEventListener('pointerleave', () => { pointerX=pointerY=0; pointerScene=null; scheduleMotion(); }, {passive:true});
  });
  addEventListener('scroll', scheduleMotion, {passive:true});
  addEventListener('resize', scheduleMotion, {passive:true});
  document.addEventListener('visibilitychange', () => { if (document.hidden) { if(frameId) cancelAnimationFrame(frameId); frameId=0; resetScenes(); } else scheduleMotion(); });
  motionPreference.addEventListener('change', () => { updateMotionControl(); scheduleMotion(); });
  updateMotionControl();
})();
