/**
 * ReadingPlayer — long-form article reading with a reliable state machine.
 *
 *   IDLE → LOADING → PLAYING ⇄ PAUSED → STOPPED / FINISHED / ERROR
 *
 * Every call to play() opens an independent *session* with a unique
 * ``sessionId``. All async results (onended / onerror / play().then|catch /
 * watchdog) check ``sessionId`` before touching state, so a stale session can
 * never cancel or overwrite a newer one. There is no shared "gen" counter that
 * a stop() can leave flipped for the next play.
 *
 * The play loop is *sequential* (await each chunk), not a producer-consumer
 * queue — this removes the "audio arrives but player already checked an empty
 * queue" race class entirely. Each chunk is played on a single <audio> element;
 * the next chunk's MP3 is warmed in a separate prefetch element only.
 *
 * Every failure path terminates in ERROR or a fresh play — it can never stall
 * in LOADING (a watchdog bounds the first-chunk request) or leave the UI in a
 * "normal but silent" state.
 */

/** Strip anything that must never reach the TTS engine, keep the readable body. */
export function sanitizeReadingText(text) {
  if (typeof text !== 'string') return ''
  let t = text
  // Code fences and images/links first (keep the link text).
  t = t.replace(/```[\s\S]*?```/g, ' ')
  t = t.replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
  t = t.replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
  // URLs — never speak "https www".
  t = t.replace(/https?:\/\/\S+/gi, ' ')
  t = t.replace(/www\.\S+/gi, ' ')
  t = t.replace(/\b[\w.-]+\.(com|org|net|edu|gov|io|co|uk|cn)([/?#]\S*)?/gi, ' ')
  // HTML tags and entities.
  t = t.replace(/<[^>]+>/g, ' ')
  t = t.replace(/&[a-z#0-9]+;/gi, ' ')
  // Markdown heading/list/blockquote markers at line start.
  t = t.replace(/^\s*#{1,6}\s+/gm, ' ')
  t = t.replace(/^\s*[-*+]\s+/gm, ' ')
  t = t.replace(/^\s*>\s+/gm, ' ')
  // Stray markdown/formatting symbols (keeps hyphens, apostrophes and periods).
  t = t.replace(/[#*_~`|\[\](){}<>]/g, ' ')
  // Collapse whitespace.
  t = t.replace(/[ \t]+/g, ' ').replace(/\s*\n\s*/g, ' ').trim()
  return t
}

/** Split into sentences on terminal punctuation (keeps the punctuation). */
const _ABBREV = new Set([
  'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr', 'st', 'vs', 'etc',
  'e.g', 'i.e', 'fig', 'no', 'vol', 'approx', 'dept', 'inc', 'ltd',
  'co', 'u.s', 'a.m', 'p.m', 'vs', 'cf', 'al',
])

export function splitSentences(text) {
  const clean = (text || '').trim()
  if (!clean) return []
  // Protect decimal points ("3.5x", "1,200.50") so they never become a
  // sentence boundary; restore them after splitting.
  const t = clean.replace(/(\d)\.(?=\d)/g, '$1')
  const sentences = []
  const n = t.length
  let start = 0
  for (let i = 0; i < n; i++) {
    const ch = t[i]
    if (ch !== '.' && ch !== '!' && ch !== '?') continue
    // Include trailing closing quotes/parens in the sentence.
    let j = i + 1
    while (j < n && /["')\]]/.test(t[j])) j++
    // Find the next non-space character.
    let k = j
    while (k < n && /\s/.test(t[k])) k++
    const nextChar = k < n ? t[k] : ''
    const isEnd = k >= n
    const startsSentence = /[A-Z0-9(]/.test(nextChar)
    // Abbreviation guard: single-letter ("U.S.") or known ("e.g.") before the dot.
    const before = t.slice(start, i).trim()
    const lastWord = before.split(/\s+/).pop() || ''
    const isAbbrev = lastWord.length === 1 || _ABBREV.has(lastWord.toLowerCase().replace(/[^a-z.]/g, ''))
    if (isEnd || (startsSentence && !isAbbrev)) {
      sentences.push(t.slice(start, j))
      start = j
      i = j - 1
    }
  }
  if (start < n) sentences.push(t.slice(start))
  return sentences.map((s) => s.replace(//g, '.').trim()).filter(Boolean)
}

/**
 * Group sentences into chunks of at most `maxChars`, never splitting a
 * sentence (and therefore never splitting a word) mid-way.
 */
export function chunkText(text, maxChars = 200) {
  const sentences = splitSentences(text)
  const chunks = []
  let current = ''
  for (const s of sentences) {
    if (current && (current + ' ' + s).length > maxChars) {
      chunks.push(current.trim())
      current = s
    } else {
      current = current ? current + ' ' + s : s
    }
  }
  if (current.trim()) chunks.push(current.trim())
  return chunks
}

/** Diagnostic logger — errors surface as warnings, normal flow stays debug-only. */
function log(tag, data = {}) {
  const payload = { tag, ...data }
  if (tag === 'READ_ERROR' || tag === 'AUDIO_PLAY_FAILED') {
    // eslint-disable-next-line no-console
    console.warn('[WM_READ]', tag, payload)
  } else {
    // eslint-disable-next-line no-console
    console.debug('[WM_READ]', tag, payload)
  }
}

let _sessionCounter = 0

export class ReadingPlayer {
  constructor() {
    this.audio = this._newAudio()
    this._prefetcher = this._newAudio()

    this.chunks = []
    this.index = 0
    this.state = 'IDLE' // IDLE | LOADING | PLAYING | PAUSED | STOPPED | FINISHED | ERROR
    this.sessionId = 0  // 0 = no active session
    this.accent = 'us'
    this.speed = 'normal'
    this._listeners = new Set()

    // Releases a pending chunk await when stop()/a new play() interrupts it.
    this._playResolve = null
    this._watchdogTimer = null

    this.FIRST_CHUNK_TIMEOUT_MS = 15000
    this.MAX_RETRIES = 2
  }

  _newAudio() {
    const a = new Audio()
    a.preload = 'auto'
    return a
  }

  // ── public API ──────────────────────────────────────────────
  subscribe(fn) {
    this._listeners.add(fn)
    return () => { this._listeners.delete(fn) }
  }

  setVoice(accent) { this.accent = accent === 'uk' ? 'uk' : 'us' }
  setSpeed(speed) { this.speed = speed === 'slow' ? 'slow' : 'normal' }

  _emit() {
    const snapshot = { state: this.state, index: this.index, total: this.chunks.length }
    for (const fn of this._listeners) {
      try { fn(snapshot) } catch (_) { /* listener errors never break playback */ }
    }
  }

  _setState(s) { this.state = s; this._emit() }

  _url(text) {
    const voice = this.accent === 'uk' ? 'uk' : 'us'
    const rate = this.speed === 'slow' ? 0.75 : 1.0
    return `/api/audio/${encodeURIComponent(text)}?voice=${voice}&speed=${rate}&tts=v4`
  }

  // ── session lifecycle ───────────────────────────────────────
  play(text) {
    // Open a brand-new session; invalidate whatever was running and release
    // its pending chunk await so it cannot touch the new session.
    const sessionId = `${Date.now()}-${++_sessionCounter}`
    this.sessionId = sessionId
    this._releasePending('stopped')
    this._clearWatchdog()
    this._resetAudio()

    const rawLength = typeof text === 'string' ? text.length : 0
    const clean = sanitizeReadingText(text)
    this.chunks = chunkText(clean, 200)
    this.index = 0
    this._retries = 0

    log('READ_CLICK', { session_id: sessionId, state: this.state, raw_text_length: rawLength })
    log('SANITIZE_DONE', { session_id: sessionId, sanitized_length: clean.length })

    if (!this.chunks.length) {
      log('READ_ERROR', { session_id: sessionId, stage: 'sanitize_chunks', error: 'no_chunks', raw_text_length: rawLength, sanitized_length: clean.length })
      this._setState('ERROR')
      return
    }
    log('CHUNKS_READY', { session_id: sessionId, chunk_count: this.chunks.length })
    this._setState('LOADING')
    this._runLoop(sessionId)
  }

  replay(text) { this.play(text) }

  async _runLoop(sessionId) {
    while (this.sessionId === sessionId && this.index < this.chunks.length) {
      const i = this.index
      this._setState('PLAYING')
      const result = await this._playChunk(i, sessionId)
      if (this.sessionId !== sessionId) return // stopped / replayed

      if (result === 'ended') {
        this._retries = 0
        this.index++
        continue
      }
      // Failure: bounded retry (short backoff), then skip the chunk.
      if (this._retries < this.MAX_RETRIES) {
        this._retries++
        log('READ_ERROR', { session_id: sessionId, stage: 'chunk_retry', chunk_index: i, error: result, retry: this._retries })
        await new Promise((r) => setTimeout(r, 250))
        if (this.sessionId !== sessionId) return
        continue
      }
      log('READ_ERROR', { session_id: sessionId, stage: 'chunk_skip', chunk_index: i, error: result })
      this._retries = 0
      this.index++
    }
    if (this.sessionId === sessionId) {
      this._setState(this.index >= this.chunks.length ? 'FINISHED' : 'STOPPED')
    }
  }

  /**
   * Play a single chunk on the shared audio element, resolving with 'ended',
   * 'error', 'play_rejected' or 'timeout'. Never resolves more than once and
   * never leaves a handler attached after settling.
   */
  _playChunk(i, sessionId) {
    return new Promise((resolve) => {
      if (sessionId !== this.sessionId) return resolve('stale')
      const a = this.audio
      const url = this._url(this.chunks[i])
      let settled = false
      const finish = (result) => {
        // A stale session's late callback must never mutate a newer session.
        if (settled || sessionId !== this.sessionId) return
        settled = true
        this._clearWatchdog()
        a.onended = a.onerror = null
        if (this._playResolve === resolve) this._playResolve = null
        resolve(result)
      }

      this._playResolve = resolve
      log('TTS_REQUEST', { session_id: sessionId, chunk_index: i })
      this._prefetch(i + 1)

      a.onended = () => {
        if (sessionId !== this.sessionId) return
        log('AUDIO_ENDED', { session_id: sessionId, chunk_index: i })
        finish('ended')
      }
      a.onerror = () => {
        if (sessionId !== this.sessionId) return
        log('AUDIO_PLAY_FAILED', { session_id: sessionId, chunk_index: i, error: 'media_error' })
        finish('error')
      }

      a.src = url
      a.play().then(() => {
        if (sessionId !== this.sessionId) return
        log('AUDIO_PLAY_SUCCESS', { session_id: sessionId, chunk_index: i })
        this._clearWatchdog()
      }).catch((err) => {
        if (sessionId !== this.sessionId) return
        // Never swallow: record and route through the same failure path.
        log('AUDIO_PLAY_FAILED', { session_id: sessionId, chunk_index: i, error: err?.name || 'unknown', message: err?.message || '' })
        // A rejected play() usually means the element was mid-load from a stale
        // src; the loop retries with a fresh src on the same element.
        finish('play_rejected')
      })

      // Watchdog: a first chunk that never starts (backend hang / no response)
      // must not leave LOADING forever.
      if (i === 0) {
        this._setWatchdog(() => {
          log('READ_ERROR', { session_id: sessionId, stage: 'watchdog', chunk_index: i, error: 'first_chunk_timeout' })
          finish('timeout')
        })
      }
    })
  }

  pause() {
    if (this.state !== 'PLAYING' && this.state !== 'LOADING') return
    this._clearWatchdog()
    this.audio.pause()
    this._setState('PAUSED')
  }

  resume() {
    if (this.state !== 'PAUSED') return
    this._setState('PLAYING')
    this.audio.play().catch((err) => {
      // Resume failed — release the pending chunk so the loop can retry it.
      log('AUDIO_PLAY_FAILED', { session_id: this.sessionId, chunk_index: this.index, error: err?.name || 'unknown', message: err?.message || '', stage: 'resume' })
      if (this._playResolve) { const r = this._playResolve; this._playResolve = null; r('play_rejected') }
    })
  }

  stop() {
    this.sessionId = 0 // invalidate the active session
    this._clearWatchdog()
    this._releasePending('stopped')
    this._resetAudio()
    this.chunks = []
    this.index = 0
    this._retries = 0
    this._setState('STOPPED')
  }

  // ── internals ───────────────────────────────────────────────
  _releasePending(result) {
    if (this._playResolve) {
      const r = this._playResolve
      this._playResolve = null
      r(result)
    }
  }

  _resetAudio() {
    const a = this.audio
    a.pause()
    a.onended = a.onerror = null
    a.removeAttribute('src')
    try { a.load() } catch (_) { /* ignore */ }
  }

  _setWatchdog(fn) {
    this._clearWatchdog()
    this._watchdogTimer = setTimeout(() => {
      this._watchdogTimer = null
      fn()
    }, this.FIRST_CHUNK_TIMEOUT_MS)
  }

  _clearWatchdog() {
    if (this._watchdogTimer) {
      clearTimeout(this._watchdogTimer)
      this._watchdogTimer = null
    }
  }

  _prefetch(i) {
    if (i < this.chunks.length) {
      this._prefetcher.src = this._url(this.chunks[i])
      this._prefetcher.load()
    }
  }
}
