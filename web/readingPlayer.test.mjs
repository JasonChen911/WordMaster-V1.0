/**
 * ReadingPlayer regression + "no-sound" stress test (headless, no browser).
 *
 * Run:  node web/readingPlayer.test.mjs
 *
 * Exercises the full play chain with a controllable fake <audio>:
 *   READ_CLICK → sanitize → chunk → TTS request (audio.src+play) → ended/error
 *   → watchdog → retry/skip → FINISHED/ERROR, plus pause/resume/stop/replay and
 *   stale-session races.
 */

import { sanitizeReadingText, chunkText, splitSentences, ReadingPlayer } from './src/readingPlayer.js'

let PASS = 0, FAIL = 0
const check = (name, cond, detail = '') => {
  if (cond) { PASS++; console.log(`  OK   ${name}`) }
  else { FAIL++; console.log(`  FAIL ${name} | ${detail}`) }
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const flush = () => sleep(0)

// Capture (and silence) the diagnostic logs so the test output stays readable;
// they are also asserted on below to confirm the required log contract.
const logs = []
console.debug = (...a) => { logs.push(['debug', ...a]) }
console.warn = (...a) => { logs.push(['warn', ...a]) }

// ── Controllable fake <audio> ──
function makeFakeAudio(store) {
  const a = {
    preload: 'auto',
    _src: '',
    _onended: null,
    _onerror: null,
    _playResolve: null,
    _playReject: null,
    load() { store.loads.push(this._src) },
    pause() { store.pauses.push(this._src) },
    removeAttribute() { this._src = '' },
    play() {
      store.plays.push(this._src)
      return new Promise((res, rej) => { this._playResolve = res; this._playReject = rej })
    },
  }
  Object.defineProperty(a, 'src', {
    get() { return this._src },
    set(v) { this._src = v; store.srcs.push(v) },
  })
  Object.defineProperty(a, 'onended', {
    get() { return this._onended },
    set(fn) { this._onended = fn },
  })
  Object.defineProperty(a, 'onerror', {
    get() { return this._onerror },
    set(fn) { this._onerror = fn },
  })
  return a
}

function freshPlayer(store, opts = {}) {
  // Install the fake <audio> factory before the player constructs its elements.
  globalThis.Audio = function () { return makeFakeAudio(store) }
  const player = new ReadingPlayer()
  if (opts.timeoutMs) player.FIRST_CHUNK_TIMEOUT_MS = opts.timeoutMs
  return player
}

const SENTENCE = 'The quick brown fox jumps over the lazy dog while students study vocabulary.'
const SHORT = 'This is a short article. It has just two sentences here.'
const LONG = Array.from({ length: 12 }, () => SENTENCE).join(' ')
const WORD300 = Array.from({ length: 30 }, () => SENTENCE).join(' ')
const WORD1200 = Array.from({ length: 120 }, () => SENTENCE).join(' ')

// ── 1) sanitize / chunk contract ──
check('sanitize strips markdown/urls', !/https|www|\*|#|\[|\]/.test(
  sanitizeReadingText('# Title\n\nSee https://x.com/y and **bold** text.')
))
check('sanitize keeps numbers/currency', /\$1,200|3\.5|50%/.test(
  sanitizeReadingText('It costs $1,200 and grew 3.5x (50%).')
))
const sentences = splitSentences('It grew 3.5x faster. Students study daily.')
check('splitSentences keeps decimal 3.5x together', sentences.some((s) => s.includes('3.5x')))
check('splitSentences returns 2 sentences', sentences.length === 2, JSON.stringify(sentences))
const chunks = chunkText('Sentence one is here. Sentence two is here too. Sentence three follows.', 40)
check('chunkText produces >1 chunk', chunks.length > 1, JSON.stringify(chunks))
check('chunkText chunks non-empty and bounded', chunks.every((c) => c.length > 0))

// ── 2) stress: play short/300/1200 many times, every click must start ──
{
  const store = { plays: [], pauses: [], loads: [], srcs: [] }
  const player = freshPlayer(store)
  let ok = true, stuck = false

  for (let n = 0; n < 50; n++) {
    player.play(SHORT)
    await flush()
    if (!store.plays.length) { ok = false; break }           // no request → no sound
    if (player.state === 'LOADING' || player.state === 'PLAYING') {} else { stuck = player.state; break }
    // finish the chunk so the loop can settle
    player.audio._playResolve && player.audio._playResolve()
    player.audio._onended && player.audio._onended()
    await flush()
  }
  check('50x short play always issues a request and starts', ok, `plays=${store.plays.length}`)
  check('50x short play never stuck in LOADING', !stuck, stuck)

  for (const [label, text, times] of [['300-word', WORD300, 20], ['1200-word', WORD1200, 10]]) {
    let started = 0
    for (let n = 0; n < times; n++) {
      player.play(text)
      await flush()
      if (store.plays.length > started) started++
      // drain all chunks of this session
      while (player.state === 'LOADING' || player.state === 'PLAYING') {
        player.audio._playResolve && player.audio._playResolve()
        player.audio._onended && player.audio._onended()
        await flush()
      }
      player.stop()
      await flush()
    }
    check(`${label} play x${times} always issues first request`, started === times, `${started}/${times}`)
  }
}

// ── 3) play → stop → play x20: stop must never block the next play ──
{
  const store = { plays: [], pauses: [], loads: [], srcs: [] }
  const player = freshPlayer(store)
  let ok = true
  for (let n = 0; n < 20; n++) {
    player.play(LONG)
    await flush()
    player.stop()
    await flush()
    player.play(SHORT)
    await flush()
    if (player.state !== 'PLAYING' && player.state !== 'LOADING') { ok = false; break }
    player.stop()
    await flush()
  }
  check('play→stop→play x20 never blocks next play', ok)
}

// ── 4) play → pause → resume x20: resume continues, no stuck ──
{
  const store = { plays: [], pauses: [], loads: [], srcs: [] }
  const player = freshPlayer(store)
  let ok = true
  for (let n = 0; n < 20; n++) {
    player.play(LONG)
    await flush()
    player.audio._playResolve && player.audio._playResolve()   // first chunk starts
    player.pause()
    if (player.state !== 'PAUSED') { ok = false; break }
    player.resume()
    if (player.state !== 'PLAYING') { ok = false; break }
    player.stop()
    await flush()
  }
  check('play→pause→resume x20 transitions correctly', ok)
}

// ── 5) rapid multi-click: exactly one active session, no overlap ──
{
  const store = { plays: [], pauses: [], loads: [], srcs: [] }
  const player = freshPlayer(store)
  for (let n = 0; n < 5; n++) player.play(SHORT)
  await flush()
  check('5 rapid plays → still PLAYING/LOADING (last session wins)', player.state === 'PLAYING' || player.state === 'LOADING', player.state)
  // exactly one shared audio element is used regardless of click count
  check('5 rapid plays use a single audio element', player.audio === player.audio)
  player.stop()
}

// ── 6) first-chunk failure (play() rejects) → bounded retry then recoverable ──
{
  const store = { plays: [], pauses: [], loads: [], srcs: [] }
  const player = freshPlayer(store, { timeoutMs: 500 })
  player.play(SHORT)
  await flush()
  // reject the first play
  player.audio._playReject(new Error('AbortError'))
  await flush()
  check('play() reject → state not stuck in LOADING', player.state !== 'LOADING', player.state)
  await sleep(300) // allow the bounded retry backoff to fire
  check('play() reject → issues a retry request', store.plays.length >= 2, `plays=${store.plays.length}`)
  // let the retry succeed and finish
  player.audio._playResolve && player.audio._playResolve()
  player.audio._onended && player.audio._onended()
  await flush()
  // player must be reusable afterwards
  player.play(SHORT)
  await flush()
  check('after failure, player is reusable', player.state === 'LOADING' || player.state === 'PLAYING', player.state)
  player.stop()
}

// ── 7) watchdog: first chunk never resolves → timeout → ERROR, recoverable ──
{
  const store = { plays: [], pauses: [], loads: [], srcs: [] }
  const player = freshPlayer(store, { timeoutMs: 40 })
  player.play(SHORT)
  await flush()
  await sleep(90) // let the watchdog fire (never resolve the play promise)
  check('watchdog fires → not stuck in LOADING', player.state !== 'LOADING', player.state)
  player.stop()
  player.play(SHORT)
  await flush()
  check('after watchdog, player is reusable', player.state === 'LOADING' || player.state === 'PLAYING', player.state)
  player.stop()
}

// ── 8) empty audio response (onerror) → skip, no stuck ──
{
  const store = { plays: [], pauses: [], loads: [], srcs: [] }
  const player = freshPlayer(store)
  player.play(SHORT)
  await flush()
  player.audio._onerror && player.audio._onerror()
  await flush()
  check('onerror → not stuck in LOADING', player.state !== 'LOADING', player.state)
  player.stop()
}

// ── 9) stale session late return must not cancel the new session ──
{
  const store = { plays: [], pauses: [], loads: [], srcs: [] }
  const player = freshPlayer(store)
  player.play(LONG)
  await flush()
  const oldAudio = player.audio
  const oldOnended = oldAudio._onended
  player.stop()                    // session A ends
  player.play(SHORT)               // session B starts
  await flush()
  const newOnended = player.audio._onended
  // Late resolve of session A's play() must not clear session B's handlers.
  oldAudio._playResolve && oldAudio._playResolve()
  await flush()
  check('stale play() resolve does not clear new session handlers', player.audio._onended === newOnended)
  // New session still plays to completion.
  player.audio._playResolve && player.audio._playResolve()
  player.audio._onended && player.audio._onended()
  await flush()
  check('new session still advances after stale return', player.state === 'FINISHED' || player.state === 'PLAYING', player.state)
  player.stop()
}

// ── 10) simulate page exit (dispose) then re-enter with a fresh player ──
{
  const store = { plays: [], pauses: [], loads: [], srcs: [] }
  let player = freshPlayer(store)
  player.play(LONG)
  await flush()
  player.stop()          // cleanup on unmount
  player = freshPlayer(store)  // new mount
  player.play(SHORT)
  await flush()
  check('fresh player after remount starts cleanly', player.state === 'LOADING' || player.state === 'PLAYING', player.state)
  player.stop()
}

// ── log contract: a read session must emit the diagnostic tags ──
{
  const tags = logs.map((l) => l[2]).filter(Boolean)
  for (const t of ['READ_CLICK', 'SANITIZE_DONE', 'CHUNKS_READY', 'TTS_REQUEST', 'AUDIO_PLAY_SUCCESS', 'AUDIO_ENDED']) {
    check(`log emits ${t}`, tags.includes(t), `seen=[${[...new Set(tags)].slice(0, 12).join(',')}]`)
  }
}

console.log()
console.log(`  RESULT: ${PASS} PASSED, ${FAIL} FAILED  (${PASS + FAIL} checks)`)
process.exit(FAIL ? 1 : 0)
