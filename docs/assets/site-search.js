(() => {
  'use strict';

  const script = document.currentScript;
  if (!script?.src) return;

  const rootUrl = new URL('../', new URL(script.src, document.baseURI));
  const indexUrl = new URL('search-index.v1.json', rootUrl);
  let entriesPromise;

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

    return { dialog, input, openDialog };
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

  init();
})();
