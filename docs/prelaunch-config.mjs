const SERVICE_STATUSES = new Set(['pending_operator_account', 'active'])

function text(value, field) {
  if (typeof value !== 'string' || !value.trim()) throw new TypeError(`${field} must be a non-empty string`)
  return value.trim()
}

function status(value, field) {
  if (!SERVICE_STATUSES.has(value)) throw new TypeError(`${field} is unsupported`)
  return value
}

export function validatePrelaunchConfig(value) {
  if (!value || typeof value !== 'object' || value.schema !== 'prelaunch-config/v1') {
    throw new TypeError('unsupported prelaunch config schema')
  }
  const analytics = {
    provider: text(value.analytics?.provider, 'analytics.provider'),
    status: status(value.analytics?.status, 'analytics.status'),
    domain: typeof value.analytics?.domain === 'string' ? value.analytics.domain.trim() : '',
    scriptSrc: typeof value.analytics?.scriptSrc === 'string' ? value.analytics.scriptSrc.trim() : '',
  }
  if (analytics.provider !== 'plausible') throw new TypeError('analytics.provider must be plausible')
  if (analytics.status === 'active') {
    if (!analytics.domain) throw new TypeError('active Plausible analytics requires a domain')
    const script = new URL(analytics.scriptSrc)
    if (script.protocol !== 'https:' ||
        (script.hostname !== 'plausible.io' && !script.hostname.endsWith('.plausible.io'))) {
      throw new TypeError('analytics.scriptSrc must be the HTTPS snippet supplied by Plausible')
    }
  }
  return { schema: value.schema, analytics }
}

export async function loadPrelaunchConfig(url = 'prelaunch-config.v1.json') {
  const response = await fetch(url, { cache: 'no-store' })
  if (!response.ok) throw new Error(`prelaunch config HTTP ${response.status}`)
  return validatePrelaunchConfig(await response.json())
}

function enableAnalytics(analytics) {
  if (analytics.status !== 'active') return
  globalThis.plausible = globalThis.plausible || function plausible() {
    ;(globalThis.plausible.q = globalThis.plausible.q || []).push(arguments)
  }
  const script = document.createElement('script')
  script.defer = true
  script.src = analytics.scriptSrc
  script.dataset.domain = analytics.domain
  document.head.appendChild(script)
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]')
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
    const target = new URL(link.href)
    if (target.origin !== location.origin || target.pathname === location.pathname) return
    if (/\/(learn|methods|how-to|examples)\//.test(target.pathname) || target.pathname.endsWith('/strategy-claim-audit-checklist.html')) {
      globalThis.plausible('Guide Click', {props: {destination: target.pathname}})
    }
  })
  window.addEventListener('hashchange', event => {
    if (!event.oldURL || !event.newURL || !document.querySelector('#journey-main')) return
    const target = new URL(event.newURL)
    const route = target.hash.split('?')[0]
    if (route === new URL(event.oldURL).hash.split('?')[0]) return
    if (['#/learn', '#/learn/monte-carlo', '#/learn/checklist'].includes(route)) {
      globalThis.plausible('Guide Click', {props: {destination: target.pathname + route}})
    }
  })
}

export function activatePrelaunch(config) {
  enableAnalytics(config.analytics)
  document.documentElement.dataset.prelaunch = 'configured'
}
