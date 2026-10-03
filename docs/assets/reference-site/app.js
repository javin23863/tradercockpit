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
    builder:['Builder','Generate strategies from the building blocks and rules you choose, test them on historical data and review every result: trades, equity curve, statistics and robustness checks. Progress, Full settings and Results keep a run and its exact settings together.'],
    charts:['Charts','Chart your own market data with studies, drawing tools, multi-chart layouts and bar replay. Order-flow views use the data your connected broker provides; if a broker does not supply a data type, TraderCockpit tells you instead of estimating it. The image shows the Charts workspace with sample data.'],
    models:['Models','Run statistical and machine-learning studies on a saved copy of your data, such as feature structure, forecasts and diagnostics. Each result stays tied to the data it used. A fitted model is not a promise of future performance. The image shows the Models workspace with sample data.'],
    apollo:['Apollo','Apollo is the research assistant built into TraderCockpit. Ask it to explain a result, help set up your next test or draft research notes. It uses the same controls you do, asks before it runs anything, and tells you before any of your material leaves your computer. Apollo uses the usage credit included in your plan.'],
    data:['Data organization','Import price files, connect MetaTrader 5, or download Kraken and Coinbase spot market data, then find everything in one searchable library. Saved history stays on your computer and remains available offline.'],
    projects:['Custom projects','Chain tasks such as build, retest, optimization and walk-forward into a workflow you can run again. Each task keeps its own settings, and results stay with the project.']
  });
  const images = Object.freeze({charts:['assets/reference-site/product-charts.webp',480,349], models:['assets/reference-site/product-models.webp',480,333]});
  document.querySelectorAll('[data-feature]').forEach(b => b.addEventListener('click', () => {
    const key = b.dataset.feature, entry = features[key];
    if (!entry) return;
    const [src,width,height] = images[key] || [`assets/reference-site/${key}.webp`,450,230];
    const alt = images[key] ? `${entry[0]} workspace shown with sample data` : '';
    show(entry[0], 'TraderCockpit desktop', `<img class="detail-media" src="${src}" alt="${alt}" width="${width}" height="${height}"><p>${entry[1]}</p><a class="button glass" href="docs/#workspaces">Read the product guide →</a>`);
  }));
  document.addEventListener('click', event => {
    if (!event.target.closest('[data-video]')) return;
    show('Monte Carlo block bootstrap', 'Research explainer', '<p>A short TraderCockpit explainer on resampling a strategy\'s trade sequence to see how much the result depends on one particular path.</p><div class="video-box"><button class="button gold" id="load-video">Load video from YouTube</button></div><p>The video loads from YouTube only after you press the button.</p>');
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
  document.querySelectorAll('[data-provenance]').forEach(b => b.addEventListener('click', () => show('About the images', 'TraderCockpit', '<p>The room, mountains, furniture and laptop are illustrative artwork.</p><p>The Charts and Models screens are taken from the TraderCockpit desktop app running on synthetic sample data. They are not live markets, real accounts or trading results.</p><p>Scene motion is decorative. You can pause it, and it stays off if your system prefers reduced motion.</p>')));
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
    ['Platform','#platform','environment workflow'],['Features','#features','capabilities'],['Pricing','#pricing','plans core trader quant apollo pro price subscription'],['Learn','#/learn','guides methods library learning'],['Join the waitlist','#public-status','waitlist email access signup'],
    ['Monte Carlo uncertainty','#/learn/monte-carlo','methods resampling assumptions simulation'],['Research checklist','#/learn/checklist','notes evidence questions source'],['Plans and access','#/access','plans checkout pricing'],['Charts overview','#/platform/charts','price studies indicators replay'],['Models overview','#/platform/models','models machine learning diagnostics'],['Product guide','docs/','documentation help guide workspaces'],
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
