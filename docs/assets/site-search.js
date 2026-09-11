(() => {
  'use strict';

  const script = document.currentScript;
  if (!script?.src) return;

  const rootUrl = new URL('../', new URL(script.src, document.baseURI));
  const indexUrl = new URL('search-index.v1.json', rootUrl);
  const MAX_INITIAL_QUERY_LENGTH = 120;
  let entriesPromise;

  function initialSearchQuery() {
    const hash = window.location.hash.startsWith('#') ? window.location.hash.slice(1) : '';
    const hashParams = new URLSearchParams(hash);
    const urlParams = new URLSearchParams(window.location.search);
    const raw = hashParams.get('search') ?? urlParams.get('q') ?? '';
    const query = String(raw).trim();
    return query && query.length <= MAX_INITIAL_QUERY_LENGTH ? query : '';
  }

  function normalize(value) {
    return String(value || '')
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, ' ')
      .trim();
  }

  function loadEntries() {
    if (!entriesPromise) {
      entriesPromise = fetch(indexUrl, { credentials: 'same-origin', cache: 'force-cache' })
        .then((response) => {
          if (!response.ok) throw new Error(`Search index HTTP ${response.status}`);
          return response.json();
        })
        .then((payload) => {
          if (payload?.schema !== 'site-search/v1' || !Array.isArray(payload.entries)) throw new Error('Unsupported search index');
          return payload.entries;
        });    }
    return entriesPromise;
  }

  function scoreEntry(entry, query) {
    const phrase = normalize(query);
    if (!phrase) return 0;
    const tokens = phrase.split(/\s+/).filter(Boolean);
    const title = normalize(entry.title);
    const summary = normalize(entry.summary);
    const terms = normalize((entry.terms || []).join(' '));
    const kind = normalize(entry.kind);
    const haystack = `${title} ${summary} ${terms} ${kind}`;
    if (!tokens.every((token) => haystack.includes(token))) return 0;

    let score = 1;
    if (title === phrase) score += 40;
    else if (title.startsWith(phrase)) score += 24;
    else if (title.includes(phrase)) score += 16;
    if (terms.includes(phrase)) score += 8;
    for (const token of tokens) {
      if (title.split(' ').includes(token)) score += 5;
      else if (title.includes(token)) score += 3;
      if (terms.includes(token)) score += 2;
      if (summary.includes(token)) score += 1;
    }
    return score;
  }
  function buildDialog() {
    const dialog = document.createElement('dialog');
    dialog.className = 'site-search-dialog';
    dialog.setAttribute('aria-labelledby', 'site-search-title');

    const form = document.createElement('form');
    form.className = 'site-search-shell';
    form.method = 'dialog';
    form.addEventListener('submit', (event) => event.preventDefault());

    const header = document.createElement('div');
    header.className = 'site-search-head';
    const headingWrap = document.createElement('div');
    const kicker = document.createElement('span');
    kicker.className = 'kicker';
    kicker.textContent = 'Local documentation search';
    const title = document.createElement('h2');
    title.id = 'site-search-title';
    title.textContent = 'Search public TraderCockpit knowledge';
    headingWrap.append(kicker, title);

    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'control-btn';
    close.textContent = 'Close';
    header.append(headingWrap, close);
    const label = document.createElement('label');
    label.className = 'site-search-label';
    label.htmlFor = 'site-search-input';
    label.textContent = 'Search concepts, methods, How-Tos, and public Docs';

    const input = document.createElement('input');
    input.id = 'site-search-input';
    input.className = 'site-search-input';
    input.type = 'search';
    input.autocomplete = 'off';
    input.spellcheck = false;
    input.placeholder = 'Try “Monte Carlo”, “drawdown”, or “what is this”';

    const status = document.createElement('p');
    status.className = 'micro site-search-status';
    status.setAttribute('aria-live', 'polite');
    status.textContent = 'Search runs locally in this page. Queries are not sent to a search provider.';

    const results = document.createElement('div');
    results.className = 'site-search-results';
    results.setAttribute('role', 'list');

    form.append(header, label, input, status, results);
    dialog.append(form);
    document.body.append(dialog);

    let previousFocus = null;
    function closeDialog() {
      if (dialog.open && typeof dialog.close === 'function') dialog.close();
      else dialog.removeAttribute('open');
      previousFocus?.focus?.();
    }

    function openDialog() {
      previousFocus = document.activeElement;
      if (typeof dialog.showModal === 'function') dialog.showModal();
      else dialog.setAttribute('open', '');
      window.setTimeout(() => input.focus(), 0);
    }

    close.addEventListener('click', closeDialog);

    function render(items, query) {
      results.replaceChildren();
      if (!query.trim()) {
        status.textContent = 'Search runs locally in this page. Queries are not sent to a search provider.';
        return;
      }
      if (!items.length) {
        status.textContent = `No public pages matched “${query.trim()}”.`;
        return;
      }
      status.textContent = `${items.length} public result${items.length === 1 ? '' : 's'} matched.`;
      for (const { entry } of items.slice(0, 8)) {
        const link = document.createElement('a');
        link.className = 'site-search-result';
        link.setAttribute('role', 'listitem');
        link.href = new URL(entry.path, rootUrl).href;

        const meta = document.createElement('span');
        meta.className = 'site-search-result-meta';
        meta.textContent = entry.kind || 'page';

        const name = document.createElement('strong');
        name.textContent = entry.title;

        const summary = document.createElement('span');
        summary.textContent = entry.summary || '';

        link.append(meta, name, summary);
        results.append(link);
      }
    }

    async function search(query) {
      const trimmed = query.trim();
      if (!trimmed) {
        render([], '');
        return;
      }
      try {
        const entries = await loadEntries();
        const scored = entries
          .map((entry) => ({ entry, score: scoreEntry(entry, trimmed) }))
          .filter((item) => item.score > 0)
          .sort((a, b) => b.score - a.score || a.entry.title.localeCompare(b.entry.title));
        render(scored, trimmed);
      } catch (error) {
        console.error('Local site search failed', error);
        status.textContent = 'Search is temporarily unavailable. Navigation and direct links still work.';
      }
    }

    input.addEventListener('input', () => search(input.value));
    dialog.addEventListener('cancel', (event) => {
      event.preventDefault();
      closeDialog();
    });
    dialog.addEventListener('click', (event) => {
      if (event.target === dialog) closeDialog();
    });

    return { dialog, input, openDialog, search };
  }

  function depthSceneKind() {
    const path = window.location.pathname.toLowerCase();
    if (path.includes('correlation')) return 'network';
    if (path.includes('distribution')) return 'distribution';
    if (path.includes('drawdown')) return 'drawdown';
    if (path.includes('monte-carlo')) return 'paths';
    if (/(out-of-sample|walk-forward|validation|selection|holdout)/.test(path)) return 'validation';
    if (path.includes('parameter-robustness')) return 'surface';
    if (path.includes('regime')) return 'regime';
    if (/(chart-evidence|replay-boundary)/.test(path)) return 'chart';
    if (path.includes('result-metrics')) return 'metrics';
    if (path.includes('/pricing/')) return 'pricing';
    if (/(support|help\.html|404\.html)/.test(path)) return 'network';
    if (/(trust|privacy|refund-policy)/.test(path)) return 'boundary';
    if (path.includes('/updates/')) return 'timeline';
    if (/(glossary|start-here|videos)/.test(path)) return 'knowledge';
    return 'orbit';
  }

  function addSvg(parent, tag, attrs = {}) {
    const node = document.createElementNS('http:' + '//www.w3.org/2000/svg', tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
    parent.append(node);
    return node;
  }

  function buildDepthGraphic(svg, kind) {
    const cyan = '#3de8ff', green = '#49ef9a', red = '#ff526e', blue = '#5aa7ff';
    const line = (x1,y1,x2,y2,stroke=cyan,opacity=.45,width=1) => addSvg(svg,'line',{x1,y1,x2,y2,stroke,'stroke-opacity':opacity,'stroke-width':width});
    const circle = (cx,cy,r,fill=cyan,opacity=.72) => addSvg(svg,'circle',{cx,cy,r,fill,'fill-opacity':opacity});
    const rect = (x,y,width,height,fill='none',stroke=cyan,opacity=.45,rx=8) => addSvg(svg,'rect',{x,y,width,height,rx,fill,stroke,'stroke-opacity':opacity,'fill-opacity':fill==='none'?0:opacity});
    if (kind === 'network' || kind === 'knowledge') {
      const pts=[[92,92],[184,54],[280,110],[394,70],[144,205],[262,190],[402,212],[318,270]];
      [[0,1],[1,2],[2,3],[0,4],[2,5],[3,6],[4,5],[5,6],[5,7],[6,7]].forEach(([a,b])=>line(...pts[a],...pts[b],a%2?green:cyan,.34,1.2));
      pts.forEach(([x,y],i)=>circle(x,y,i%3===0?7:5,i%4===0?green:i%4===1?red:cyan,.82));
    } else if (kind === 'distribution') {
      const heights=[22,34,58,92,132,166,186,172,134,94,58,32,20];
      heights.forEach((h,i)=>rect(58+i*30,275-h,18,h,i<3?red:i>9?green:cyan,'none',.62,3));
      addSvg(svg,'path',{d:'M54 267 C120 260 140 185 202 132 C248 92 284 76 324 111 C366 148 390 225 446 265',fill:'none',stroke:cyan,'stroke-width':3,'stroke-opacity':.72});
    } else if (kind === 'drawdown') {
      addSvg(svg,'path',{d:'M48 115 L95 92 L142 108 L188 76 L236 92 L278 170 L326 228 L370 194 L414 132 L468 88',fill:'none',stroke:green,'stroke-width':3,'stroke-opacity':.88});
      addSvg(svg,'path',{d:'M48 115 L95 92 L142 108 L188 76 L236 92 L278 170 L326 228 L370 194 L414 132 L468 88 L468 286 L48 286 Z',fill:red,'fill-opacity':.08});
      line(48,76,468,76,cyan,.34,1.2); line(236,92,236,286,red,.28,1); line(326,228,326,286,red,.48,1.3);
    } else if (kind === 'paths') {
      const paths=['M45 180 C105 110 145 238 214 154 S344 90 472 158','M45 186 C120 160 160 108 220 180 S344 246 472 128','M45 175 C112 240 156 136 230 170 S360 116 472 202','M45 184 C100 96 168 188 236 140 S380 232 472 172','M45 179 C104 210 174 218 238 156 S374 96 472 146','M45 181 C120 128 168 252 248 194 S370 160 472 94'];
      paths.forEach((d,i)=>addSvg(svg,'path',{d,fill:'none',stroke:i%3===0?green:i%3===1?red:cyan,'stroke-width':i===0?2.4:1.2,'stroke-opacity':i===0?.8:.38}));
      line(44,180,474,180,blue,.22,1);
    } else if (kind === 'validation') {
      for(let i=0;i<4;i++){const y=72+i*56;rect(70+i*14,y,210-i*8,24,blue,'none',.34,5);rect(294+i*14,y,72,24,green,'none',.68,5);}
      line(288,46,288,286,red,.58,1.5); addSvg(svg,'path',{d:'M364 92 C414 112 412 174 338 204',fill:'none',stroke:red,'stroke-width':2,'stroke-dasharray':'6 6','stroke-opacity':.62});
    } else if (kind === 'surface' || kind === 'regime') {
      for(let i=0;i<7;i++){line(80+i*48,260,160+i*35,84,cyan,.2,1);line(72,250-i*27,430,250-i*27,blue,.17,1);}
      const pts=[[120,210],[168,178],[212,158],[258,128],[306,148],[354,112],[404,170],[240,212],[330,224]];
      pts.forEach(([x,y],i)=>circle(x,y,i%3===0?7:5,i%3===0?green:i%3===1?red:cyan,.82));
    } else if (kind === 'chart') {
      const vals=[[-22,34],[18,54],[-12,42],[24,66],[15,48],[-28,58],[30,72],[12,52],[-18,44],[34,80],[26,62],[-20,52],[18,68],[28,74]];
      vals.forEach(([d,h],i)=>{const x=58+i*29,y=190-d;line(x,y-h*.7,x,y+h*.4,d>=0?green:red,.8,1.4);rect(x-5,y-h*.25,10,h*.42,d>=0?green:red,'none',.72,2);});
      addSvg(svg,'path',{d:'M50 226 C118 212 134 176 190 186 S280 164 328 140 S408 112 468 92',fill:'none',stroke:cyan,'stroke-width':2.4,'stroke-opacity':.72});
    } else if (kind === 'metrics') {
      [150,260,370].forEach((x,i)=>{addSvg(svg,'circle',{cx:x,cy:168,r:54,fill:'none',stroke:cyan,'stroke-width':8,'stroke-opacity':.14});addSvg(svg,'circle',{cx:x,cy:168,r:54,fill:'none',stroke:i===1?red:green,'stroke-width':8,'stroke-dasharray':`${180-i*34} 360`,'stroke-linecap':'round','stroke-opacity':.76,transform:`rotate(-90 ${x} 168)`});});
    } else if (kind === 'pricing') {
      [70,205,340].forEach((x,i)=>{rect(x,82,112,174,i===0?'#082b2b':'#06131f',i===0?green:cyan,i===0?.75:.24,12);line(x+18,128,x+94,128,i===0?green:cyan,.35,2);line(x+18,152,x+80,152,cyan,.18,1);line(x+18,176,x+88,176,cyan,.18,1);line(x+18,226,x+94,226,i===0?green:cyan,.42,2);});
    } else if (kind === 'boundary') {
      line(264,56,264,286,red,.58,1.5); for(let i=0;i<6;i++){circle(96+i*20,92+i*26,4,cyan,.66);line(110+i*20,92+i*26,244,92+i*26,cyan,.24,1);} line(286,112,446,112,green,.42,2); line(286,168,420,168,green,.28,1); line(286,224,458,224,green,.22,1);
    } else if (kind === 'timeline') {
      for(let i=0;i<4;i++){const y=72+i*54;rect(92+i*18,y,300-i*26,34,'#061927',i===3?green:cyan,i===3?.6:.28,6);line(70,y+17,92+i*18,y+17,i===3?green:cyan,.5,1.4);}
    } else {
      addSvg(svg,'ellipse',{cx:260,cy:168,rx:176,ry:64,fill:'none',stroke:green,'stroke-opacity':.38,'stroke-width':1.4,transform:'rotate(-12 260 168)'});addSvg(svg,'ellipse',{cx:260,cy:168,rx:132,ry:48,fill:'none',stroke:cyan,'stroke-opacity':.3,'stroke-width':1.2,transform:'rotate(18 260 168)'});circle(260,168,64,cyan,.12);
    }
  }

  function initArticleDepthScene() {
    const hero = document.querySelector('.article-hero');
    const inner = hero?.querySelector('.article-hero-inner');
    if (!hero || !inner || inner.querySelector('.article-depth-scene')) return;
    const kind = depthSceneKind();
    const scene = document.createElement('div');
    scene.className = `article-depth-scene depth-scene-${kind}`;
    scene.setAttribute('aria-hidden', 'true');
    const label = document.createElement('span');
    label.className = 'article-depth-label';
    label.textContent = `${kind.replace('-', ' ')} research scene`;
    const svg = addSvg(scene, 'svg', { viewBox: '0 0 520 340', preserveAspectRatio: 'xMidYMid meet' });
    buildDepthGraphic(svg, kind);
    scene.append(label);
    inner.append(scene);
  }

  function init() {
    const nav = document.querySelector('.nav-links');
    if (!nav) return;
    const searchUi = buildDialog();
    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'site-search-trigger';
    trigger.textContent = 'Search';
    trigger.setAttribute('aria-haspopup', 'dialog');
    trigger.setAttribute('aria-label', 'Search public TraderCockpit knowledge');
    trigger.addEventListener('click', searchUi.openDialog);
    nav.append(trigger);

    const initialQuery = initialSearchQuery();
    if (initialQuery) {
      searchUi.input.value = initialQuery;
      searchUi.openDialog();
      void searchUi.search(initialQuery);
    }

    document.addEventListener('keydown', (event) => {
      const target = event.target;
      const isTyping = target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target?.isContentEditable;
      if (event.key === '/' && !isTyping && !searchUi.dialog.open) {
        event.preventDefault();
        searchUi.openDialog();
      }
    });
  }

  initArticleDepthScene();
  init();
})();
