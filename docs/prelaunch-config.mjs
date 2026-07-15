const SERVICE_STATUSES = new Set(['pending_operator_account', 'active'])
const SOURCES = new Set(['youtube', 'instagram', 'facebook', 'tiktok', 'direct'])

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
  const waitlist = {
    provider: text(value.waitlist?.provider, 'waitlist.provider'),
    status: status(value.waitlist?.status, 'waitlist.status'),
    username: typeof value.waitlist?.username === 'string' ? value.waitlist.username.trim() : '',
    allowedSources: value.waitlist?.allowedSources,
  }
  if (waitlist.provider !== 'buttondown') throw new TypeError('waitlist.provider must be buttondown')
  if (!Array.isArray(waitlist.allowedSources) || !waitlist.allowedSources.length ||
      waitlist.allowedSources.some((source) => !SOURCES.has(source))) {
    throw new TypeError('waitlist.allowedSources contains an unsupported source')
  }
  if (waitlist.status === 'active' && !/^[a-zA-Z0-9_-]+$/.test(waitlist.username)) {
    throw new TypeError('an active Buttondown waitlist requires a valid username')
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
  return { schema: value.schema, waitlist, analytics }
}

export async function loadPrelaunchConfig(url = 'prelaunch-config.v1.json') {
  const response = await fetch(url, { cache: 'no-store' })
  if (!response.ok) throw new Error(`prelaunch config HTTP ${response.status}`)
  return validatePrelaunchConfig(await response.json())
}

function sourceFromLocation(allowedSources) {
  const candidate = new URLSearchParams(globalThis.location?.search ?? '').get('utm_source')
  return allowedSources.includes(candidate) ? candidate : 'direct'
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
  for (const [id, event] of [
    ['waitlist-form', 'Waitlist+Submit'],
    ['youtube-cta', 'YouTube+Click'],
    ['product-cta', 'Product+CTA'],
  ]) document.getElementById(id)?.classList.add(`plausible-event-name=${event}`)
}

export function activatePrelaunch(config, productManifest) {
  enableAnalytics(config.analytics)
  document.documentElement.dataset.prelaunch = 'configured'
  if (productManifest.status === 'available' || config.waitlist.status !== 'active') return
  const source = sourceFromLocation(config.waitlist.allowedSources)
  const form = document.getElementById('waitlist-form')
  form.action = `https://buttondown.com/api/emails/embed-subscribe/${config.waitlist.username}`
  form.hidden = false
  document.getElementById('product-cta').hidden = true
  document.getElementById('waitlist-source').value = `source-${source}`
  document.getElementById('waitlist-utm-source').value = source
  for (const key of ['utm_medium', 'utm_campaign']) {
    document.getElementById(`waitlist-${key.replace('_', '-')}`).value =
      new URLSearchParams(globalThis.location.search).get(key) ?? ''
  }
  document.documentElement.dataset.prelaunch = 'waitlist-active'
}

export function trackConfirmedSignup(config) {
  enableAnalytics(config.analytics)
  if (config.analytics.status === 'active') globalThis.plausible('Confirmed Signup')
}
