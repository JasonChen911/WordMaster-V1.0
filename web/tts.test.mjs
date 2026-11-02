import { test } from 'node:test'
import assert from 'node:assert/strict'
globalThis.localStorage = { getItem: () => null }
const spoken = [], players = []
globalThis.window = { speechSynthesis: { cancel() {}, getVoices: () => [], speak: u => spoken.push(u.text) } }
globalThis.SpeechSynthesisUtterance = class { constructor(text) { this.text = text } }
globalThis.Audio = class {
  constructor() { players.push(this) }
  pause() {}
  load() {}
  removeAttribute() {}
  play() { return new Promise((resolve, reject) => { this.reject = reject }) }
}
const tts = await import('./src/tts.js')
test('error event plus rejected play falls back only once', async () => {
  tts.speak('telegram')
  const a = players[0]
  a.onerror()
  a.reject(new Error('offline'))
  await Promise.resolve()
  assert.deepEqual(spoken, ['telegram'])
})
test('stop invalidates pending fallback', async () => {
  spoken.length = 0
  tts.speak('abandon')
  tts.stop()
  players[0].reject(new Error('aborted'))
  await Promise.resolve()
  assert.deepEqual(spoken, [])
})
test('word interface rejects URL, objects, JSON, definitions and sentences', () => {
  assert.equal(typeof tts.speakWord, 'function')
  for (const value of [{word:'telegram'}, 'telegram https://a', 'www.a', 'a.mp3', '{"word":"telegram"}', 'telegram 电报', 'This is telegram.', '/tel/']) {
    assert.equal(tts.speakWord(value), false)
  }
})
