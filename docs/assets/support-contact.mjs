// Shared support contact. The address lives in one place: "support.email" in
// prelaunch-config.v1.json. Until it is replaced, an address ending in .invalid
// is treated as unset and each page keeps its static "coming soon" text.
const CONFIG_URL = new URL('../prelaunch-config.v1.json', import.meta.url)
const EMAIL = /^[^\s@<>"]+@[^\s@<>"]+\.[a-z]{2,}$/i

export function supportEmail(config) {
  const email = typeof config?.support?.email === 'string' ? config.support.email.trim() : ''
  return EMAIL.test(email) && !/\.invalid$/i.test(email) ? email : null
}

export async function renderSupportContact(root = document, url = CONFIG_URL) {
  const slots = [...(root.querySelectorAll?.('[data-support-contact]') ?? [])]
  if (!slots.length) return false
  try {
    const response = await fetch(url, { credentials: 'same-origin', cache: 'no-cache' })
    if (!response.ok) return false
    const email = supportEmail(await response.json())
    if (!email) return false
    for (const slot of slots) {
      const link = document.createElement('a')
      link.href = `mailto:${email}`
      link.textContent = email
      slot.replaceChildren(link)
    }
    return true
  } catch {
    return false
  }
}

renderSupportContact()
