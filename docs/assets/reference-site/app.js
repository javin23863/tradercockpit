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
    builder:['Strategy Builder','Construct strategy logic and research configurations. Keep the idea and the assumptions behind it explicit.'],
    charts:['Charts','Inspect price, studies, trades, and retained research results. This retained development capture uses synthetic TC_PROBE test data, not live markets.'],
    models:['Quant Models','Explore model diagnostics and retained analytical evidence. A fitted model is not a promise of future performance.'],
    apollo:['Apollo','Keep the guided research assistant close to the work it helps you understand.'],
    data:['Market Data','Organize the historical inputs used by your research. This page does not establish provider access or a live data connection.'],
    projects:['Custom Projects','Use reusable research workflows while keeping their settings and underlying evidence inspectable.']
  });
  // Provenance is fixed local metadata. No network request is made to GitHub.
  const captures = Object.freeze({
    charts: {title:'Charts — retained development capture', date:'16 September 2026',
      src:'assets/reference-site/product-charts.webp', width:480, height:349,
      path:'assets/reference-site/original-charts.png',
      hash:'bc2746d1fdda38c5cdcea0a74d9f82e78d0fb6cb9f98844023b4283f55aad9ae',
      note:'TC_PROBE is synthetic test data. The room display shows a crop of this chart workspace; this inspector preserves the entire capture. The screenshot is not a trading result or a live market.'},
    models: {title:'Models — retained PCA development capture', date:'9 September 2026',
      src:'assets/reference-site/product-models.webp', width:480, height:333,
      path:'assets/reference-site/original-models.png',
      hash:'3a63057265cb14c7640883cbba1144907c7dd2e2e5419b8f37fcb5ca14ff3bc6',
      note:'This development screenshot shows a PCA loading map from test data. The visible provider-not-configured and no-account states are preserved. It is not evidence of a live connection or current release approval.'}
  });
  function inspectCapture(key, switching = false) {
    const preview = captures[key];
    if (!preview) return;
    const supplied = window.TRADERCOCKPIT_CAPTURE_OVERRIDES?.[key];
    const expectedSize = key==='charts' ? [1220,886] : [1440,1000];
    const hasOriginal = supplied?.src === `assets/reference-site/original-${key}.png` &&
      supplied.hash === preview.hash && supplied.width===expectedSize[0] && supplied.height===expectedSize[1];
    const record = hasOriginal ? {...preview,src:supplied.src,width:supplied.width,height:supplied.height} : preview;
    const sizeDescription = hasOriginal ? `${record.width} × ${record.height} · verified repository original` : `${preview.width}-pixel preview · original not installed locally`;
    const origin = ''; // Original capture bytes are delivered from this site, not a private repository path.
    const tabs = Object.keys(captures).map(k => `<button class="capture-choice" data-capture-choice="${k}" aria-pressed="${k===key}">${k==='charts'?'Charts':'Models'}</button>`).join('');
    show(record.title, 'Actual software / synthetic development data',
      `<div class="capture-switch" aria-label="Choose retained capture">${tabs}</div>
       <div class="capture-scale" aria-label="Image scale"><button class="capture-choice" data-capture-scale="fit" aria-pressed="true">Fit screen</button><button class="capture-choice" data-capture-scale="native" aria-pressed="false">100% size</button></div>
       <figure class="capture-evidence" tabindex="0" aria-label="Product capture; scroll horizontally at 100 percent size"><img class="detail-media capture-media" src="${record.src}" width="${record.width}" height="${record.height}" alt="${record.title}"><figcaption>${record.date} · ${sizeDescription}</figcaption></figure>
       <p>${record.note}</p><a class="button glass" href="#/platform/${key}">Read this screen guide →</a><a class="button glass" href="${origin+record.path}" target="_blank" rel="noopener noreferrer">Full-resolution original ↗</a><p class="capture-limit">The surrounding room is illustrative artwork. Neither screen is the running application. The complete retained originals are served locally. A reduced preview is used only if the original cannot be loaded.</p>
       <details class="capture-provenance"><summary>Capture source and verification</summary><p>Repository: javin23863/tradercockpitsq<br>Commit: <code>71a4a60cb3fbf7daca8ba7fbbbb1b61ad7303fa4</code></p><p>Original SHA-256: <code>${record.hash}</code></p><a href="${origin+record.path}" target="_blank" rel="noopener noreferrer">Open retained original ↗</a></details>`, true);
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
    show(entry[0], 'Platform overview', `<img class="detail-media" src="assets/reference-site/${key}.webp" alt="Decorative illustration" width="450" height="230"><p>${entry[1]}</p><a class="button glass" href="docs/">Read product documentation ↗</a>`);
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
  document.querySelectorAll('[data-provenance]').forEach(b => b.addEventListener('click', () => show('About this homepage proof', 'Not a release candidate', '<p>The room, mountains, furniture and laptop are decorative artwork reused from the supplied <strong>TraderCockpit Quant Lab Landing Page</strong> mockup. The original fictional dashboards are masked out.</p><p>The screen overlays now use two <strong>actual retained development screenshots</strong> from the product repository. Both contain synthetic test data. They are not live feeds, proof of performance, or screenshots of a newly verified release.</p><p>Use the screen inspectors to view each whole capture and its exact source. Perspective, crop and letterboxing are recorded in the source package.</p><p>The page remains native HTML with local interactions. Scene motion responds only to scrolling or pointer movement; it has a pause control and respects reduced motion. This is not a 3D engine.</p><p>This implementation is under visual review. The illustrative setting and development captures are not release approval.</p>')));
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
    ['Monte Carlo uncertainty','#/learn/monte-carlo','methods resampling assumptions simulation'],['Research checklist','#/learn/checklist','notes evidence questions source'],['Access','#/access','waitlist plans checkout'],['Read Charts','#/platform/charts','capture guide price studies'],['Read Models','#/platform/models','PCA capture diagnostic guide'],
    ...Object.entries(features).map(([key,entry]) => [entry[0],`#${key}`,entry[1]])
  ];
  function search() {
    const q = $('#search-input').value.trim().toLowerCase();
    const matches = searchItems.filter(item => `${item[0]} ${item[2]}`.toLowerCase().includes(q));
    $('#search-status').textContent = `${matches.length} ${matches.length === 1 ? 'result' : 'results'} in this preview`;
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
