import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import vm from 'node:vm'
const script = readFileSync(new URL('./public/frontend-recovery.js', import.meta.url), 'utf8')
function runtime(storage = new Map(), blocked = false) {
  let reloads = 0
  const listeners = {}
  const window = { addEventListener: (name, cb) => { listeners[name] = cb }, dispatchEvent() {}, location: { href: 'http://localhost/study', replace: () => reloads++ } }
  const context = { window, URL, console, Event: class {}, setTimeout: cb => cb(),
    document: { querySelector: () => ({ content: 'build-a' }), getElementById: () => null },
    sessionStorage: { getItem: k => storage.get(k), setItem: (k,v) => { if (blocked) throw Error('disabled'); storage.set(k,v) } },
    fetch: async () => ({ json: async () => ({ build_id: 'build-a' }) }) }
  vm.runInNewContext(script, context)
  return { window, listeners, reloads: () => reloads }
}
test('one automatic reload per build across document reloads', async () => {
  const storage = new Map()
  const first = runtime(storage)
  assert.equal(first.window.wordmasterRecovery.recover(new Error('Failed to fetch dynamically imported module: http://localhost/assets/Page-abc.js?secret=hidden')), true)
  await new Promise(resolve => setImmediate(resolve))
  assert.equal(first.reloads(), 1)
  const second = runtime(storage)
  assert.equal(second.window.wordmasterRecovery.recover(new Error('ChunkLoadError')), false)
  assert.equal(second.reloads(), 0)
})
test('ordinary errors and disabled storage never loop', () => {
  assert.equal(runtime().window.wordmasterRecovery.recover(new Error('render failed')), false)
  assert.equal(runtime(new Map(), true).window.wordmasterRecovery.recover(new Error('Importing a module script failed')), false)
})
test('Vite CSS preload failure uses the same once-per-build recovery', () => {
  const storage = new Map()
  const first = runtime(storage)
  let prevented = false
  first.listeners['vite:preloadError']({ payload: new Error('Unable to preload CSS for /assets/Page-abc.css'), preventDefault() { prevented = true } })
  assert.equal(prevented, false)
  assert.equal(first.reloads(), 1)
  const second = runtime(storage)
  assert.equal(second.window.wordmasterRecovery.recover(new Error('Unable to preload CSS for /assets/Page-abc.css')), false)
  assert.equal(second.reloads(), 0)
})
