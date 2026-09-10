(() => {
  'use strict';

  function initVideoSlot(slot) {
    const button = slot.querySelector('[data-video-load]');
    const frameHost = slot.querySelector('[data-video-frame]');
    const videoId = slot.dataset.videoId;
    const title = slot.dataset.videoTitle || 'TraderCockpit video lesson';
    if (!button || !frameHost || !/^[A-Za-z0-9_-]{11}$/.test(videoId || '')) return;

    button.addEventListener('click', () => {
      if (frameHost.querySelector('iframe')) return;

      const iframe = document.createElement('iframe');
      iframe.title = title;
      iframe.loading = 'lazy';
      iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      iframe.referrerPolicy = 'strict-origin-when-cross-origin';
      iframe.allowFullscreen = true;
      iframe.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?rel=0`;

      frameHost.replaceChildren(iframe);
      slot.classList.add('is-loaded');
      button.disabled = true;
      button.textContent = 'Video loaded';
    }, { once: true });
  }

  document.querySelectorAll('[data-video-slot]').forEach(initVideoSlot);
})();