// Kit's own success redirect lands on a Kit 404, so we submit with fetch and own the outcome.
export function bindEarlyAccess(form, note, fetchImpl = globalThis.fetch, go = (url) => globalThis.location.assign(url)) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault()
    const button = form.querySelector('button[type="submit"]')
    if (button) button.disabled = true
    note.textContent = 'Sending…'
    try {
      const response = await fetchImpl(form.action, {
        method: 'POST',
        headers: { Accept: 'application/json' },
        body: new URLSearchParams([...new FormData(form)]),
      })
      const result = await response.json()
      if (!response.ok || result.status !== 'success') throw new Error('rejected')
      go('thanks.html')
    } catch {
      if (button) button.disabled = false
      note.textContent = 'That didn’t go through. Check the address and try again. Nothing was sent.'
    }
  })
}
