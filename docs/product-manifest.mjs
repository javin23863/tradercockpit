const STATUSES = new Set(['unavailable', 'waitlist', 'available'])
const ASSISTANT_STATUSES = new Set(['concept', 'available'])

function text(value, field) {
  if (typeof value !== 'string' || !value.trim()) throw new TypeError(`${field} must be a non-empty string`)
  return value.trim()
}

function link(value, field) {
  if (!value || typeof value !== 'object') throw new TypeError(`${field} must be an object`)
  const url = new URL(text(value.url, `${field}.url`), globalThis.location?.href ?? 'https://example.invalid/')
  if (!['https:', 'mailto:'].includes(url.protocol)) throw new TypeError(`${field}.url must use https or mailto`)
  return { label: text(value.label, `${field}.label`), url: value.url }
}

/** Validate and copy only fields TraderCockpit is allowed to render. */
export function validateProductManifest(value) {
  if (!value || typeof value !== 'object' || value.schema !== 'product-manifest/v1') {
    throw new TypeError('unsupported product manifest schema')
  }
  if (!STATUSES.has(value.status)) throw new TypeError('unsupported product status')
  const out = { schema: value.schema, status: value.status }

  if (value.generatedAt !== undefined) {
    if (typeof value.generatedAt !== 'string' || !Number.isFinite(Date.parse(value.generatedAt))) {
      throw new TypeError('generatedAt must be an ISO date')
    }
    out.generatedAt = value.generatedAt
  }
  if (value.product !== undefined) {
    out.product = {
      name: text(value.product?.name, 'product.name'),
      summary: text(value.product?.summary, 'product.summary'),
    }
  }
  if (value.assistant !== undefined) {
    if (!ASSISTANT_STATUSES.has(value.assistant?.status)) throw new TypeError('unsupported assistant status')
    out.assistant = { name: text(value.assistant.name, 'assistant.name'), status: value.assistant.status }
  }
  if (!Array.isArray(value.verifiedCapabilities)) throw new TypeError('verifiedCapabilities must be an array')
  out.verifiedCapabilities = value.verifiedCapabilities.map((capability, index) => ({
    id: text(capability?.id, `verifiedCapabilities[${index}].id`),
    label: text(capability?.label, `verifiedCapabilities[${index}].label`),
    summary: capability?.summary === undefined ? undefined : text(capability.summary, `verifiedCapabilities[${index}].summary`),
  }))
  if (value.platforms !== undefined) {
    if (!Array.isArray(value.platforms)) throw new TypeError('platforms must be an array')
    out.platforms = value.platforms.map((platform, index) => text(platform, `platforms[${index}]`))
  }
  for (const field of ['cta', 'checkout', 'support', 'refund']) {
    if (value[field] !== undefined) out[field] = link(value[field], field)
  }
  if (value.offer !== undefined) out.offer = { display: text(value.offer?.display, 'offer.display') }
  return out
}

export async function loadProductManifest(url = 'product-manifest.v1.json') {
  const response = await fetch(url, { cache: 'no-store' })
  if (!response.ok) throw new Error(`product manifest HTTP ${response.status}`)
  return validateProductManifest(await response.json())
}
