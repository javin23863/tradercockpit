(() => {
  'use strict';

  const script = document.currentScript;
  const status = document.querySelector('#help-status');
  const direct = document.querySelector('#help-direct');
  if (!script?.src || !status || !direct) return;

  const siteRoot = new URL('../', new URL(script.src, document.baseURI));
  const registryUrl = new URL('help-registry.v1.json', siteRoot);
  const id = new URLSearchParams(window.location.search).get('id') || '';
  const validId = /^[a-z0-9][a-z0-9.-]{0,79}$/.test(id);

  function fail(message) {
    status.textContent = message;
    direct.textContent = 'Browse public Docs →';
    direct.href = new URL('docs/', siteRoot).href;
  }

  if (!validId) {
    fail(id ? 'That help ID is not a valid public knowledge ID.' : 'No public help ID was supplied.');
    return;
  }

  fetch(registryUrl, { credentials: 'same-origin', cache: 'force-cache' })
    .then((response) => {
      if (!response.ok) throw new Error(`Help registry HTTP ${response.status}`);
      return response.json();
    })
    .then((registry) => {
      if (registry?.schema !== 'help-registry/v1' || !Array.isArray(registry.entries)) {
        throw new Error('Unsupported help registry');
      }
      const entry = registry.entries.find((candidate) => candidate.id === id && candidate.status === 'public');
      if (!entry) {
        fail(`No public help topic is currently registered for “${id}”.`);
        return;
      }

      const target = new URL(entry.path, siteRoot);
      if (target.origin !== window.location.origin || !target.href.startsWith(siteRoot.href)) {
        throw new Error('Help target escaped the public site boundary');
      }

      status.textContent = `Resolved “${entry.title}”. Opening the current public page.`;
      direct.textContent = `Open ${entry.title} →`;
      direct.href = target.href;
      window.location.replace(target.href);
    })
    .catch((error) => {
      console.error('Public help resolver failed', error);
      fail('The public help registry could not be resolved. Use Docs or search instead.');
    });
})();
