import { loadProductManifest } from '../../product-manifest.mjs';
import { activatePrelaunch, loadPrelaunchConfig } from '../../prelaunch-config.mjs';
const root = new URL('../../', import.meta.url);
const names = ['Core', 'Trader', 'Quant', 'ApolloPro'];
const $ = selector => document.querySelector(selector);

// The static links retain meaningful, existing destinations without JavaScript.
document.addEventListener('click', event => {
  const link = event.target.closest('a[data-journey]');
  if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  const next = link.dataset.journey;
  if (next === location.hash) window.dispatchEvent(new HashChangeEvent('hashchange'));
  else location.hash = next;
});
function revealAccess() {
  if (['#public-status','#development'].includes(location.hash)) $('#public-status-details').open = true;
}
window.addEventListener('hashchange', revealAccess);
revealAccess();

// Only this local JSON is the live commerce authority. No payment API is called.
function validCommerce(value) {
  return value?.schema === 'public-commerce/v1' && value.status === 'prelaunch' &&
    value.plan?.currency === 'USD' && value.checkout?.enabled === false && value.checkout.url === null &&
    Array.isArray(value.tiers) && value.tiers.length === names.length &&
    names.every((name,index) => value.tiers[index]?.name === name && value.tiers[index].interval === 'month' &&
      Number.isSafeInteger(value.tiers[index].unitAmount) && value.tiers[index].unitAmount > 0);
}
function showCommerce(value) {
  const accepted = validCommerce(value);
  document.documentElement.dataset.commerce = accepted ? 'verified' : 'unavailable';
  document.querySelectorAll('.price-grid article').forEach((article,index) => {
    const amount = accepted ? value.tiers[index].unitAmount : null;
    const node = article.querySelector('.price strong');
    if (node) node.textContent = amount === null ? 'Unavailable' : new Intl.NumberFormat('en-US', {
      style:'currency',currency:'USD',minimumFractionDigits:amount%100?2:0,maximumFractionDigits:2
    }).format(amount/100);
  });
  document.querySelectorAll('[data-checkout]').forEach(control => control.disabled = true);
  document.dispatchEvent(new CustomEvent('tc:commerce', {detail:accepted ? value : null}));
}
async function commerce() {
  try {
    const response = await fetch(new URL('commerce-public.v1.json',root), {cache:'no-store'});
    if (!response.ok) throw new Error('Commerce unavailable');
    showCommerce(await response.json());
  } catch { showCommerce(null); }
}
async function access() {
  let manifest;
  try {
    manifest = await loadProductManifest(new URL('product-manifest.v1.json',root));
    $('#product-state').textContent = manifest.status === 'unavailable' ? 'In development' : 'Status: ' + manifest.status;
    const descriptions = {unavailable:'The TraderCockpit Windows desktop app is in development. We’ll release it when it’s ready.',available:'Check the published release and access details. This page does not enable checkout.',waitlist:'The product is not available. See Updates for development status.'};
    $('#product-summary').textContent = manifest.product?.summary || descriptions[manifest.status];
    $('#manifest-detail').textContent = [(manifest.platforms || []).join(' · '), manifest.verifiedCapabilities.length ? 'Published capabilities below' : 'No product capabilities are published as available', 'Checkout is closed'].join(' · ');
    const note = document.querySelector('.hero-note');
    if (note) note.textContent = $('#product-summary').textContent;
    const caps = $('#manifest-capabilities');
    caps.replaceChildren();
    for (const item of manifest.verifiedCapabilities) {
      const row=document.createElement('p');row.textContent=item.label;caps.append(row);
    }
    caps.hidden = !manifest.verifiedCapabilities.length;
  } catch {
    $('#product-state').textContent = 'Status unavailable';
    const note = document.querySelector('.hero-note');
    if (note) note.textContent = 'Product availability could not be verified.';
    $('#product-summary').textContent = 'Access could not be verified. Check Updates before acting on availability.';
    $('#manifest-detail').textContent = 'Product availability could not be verified. The educational guides remain available; checkout is closed.';

  }
  try {
    const config = await loadPrelaunchConfig(new URL('prelaunch-config.v1.json',root));
    activatePrelaunch(config,manifest);
  } catch {
    document.documentElement.dataset.prelaunch = 'fallback';

  }
}
await Promise.all([commerce(),access()]);
