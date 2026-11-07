import assert from 'node:assert/strict'
import { bindEarlyAccess } from '../../docs/assets/early-access.mjs'
globalThis.FormData = class { constructor () { return [['email_address', 'a@example.invalid']] } }
const run = async (fetchImpl) => {
  let submit; let went = null
  const button = { disabled: false }
  const form = { action: 'https://kit.invalid/', addEventListener: (_, fn) => { submit = fn }, querySelector: () => button }
  const note = { textContent: '' }
  bindEarlyAccess(form, note, fetchImpl, (url) => { went = url })
  await submit({ preventDefault () {} })
  return { went, note: note.textContent, disabled: button.disabled }
}
const ok = await run(async () => ({ ok: true, json: async () => ({ status: 'success' }) }))
assert.equal(ok.went, 'thanks.html')
for (const bad of [async () => ({ ok: true, json: async () => ({ status: 'failed' }) }), async () => ({ ok: false, json: async () => ({}) }), async () => { throw new Error('offline') }]) {
  const r = await run(bad)
  assert.equal(r.went, null); assert.equal(r.disabled, false); assert.match(r.note, /didn’t go through/)
}
console.log('EARLY ACCESS: PASS')
