/**
 * Unified TTS service.
 *
 * Priority:
 *   1. Neural TTS  — backend Microsoft Edge Neural TTS (edge-tts) via /api/audio.
 *   2. System TTS  — browser speechSynthesis (offline fallback).
 *
 * A single shared <audio> element guarantees only one voice plays at a time
 * (no overlap when flipping words or spam-clicking). The backend caches MP3s
 * keyed by word+voice+speed, so repeat plays are instant.
 */

const K_ACCENT = 'wordmaster-tts-accent'
const K_SPEED = 'wordmaster-tts-speed'
const K_AUTOPLAY = 'wordmaster-tts-autoplay'

export function getAccent() { return localStorage.getItem(K_ACCENT) || 'us' }
export function getSpeed() { return localStorage.getItem(K_SPEED) || 'normal' }
export function getAutoPlay() { return localStorage.getItem(K_AUTOPLAY) !== 'off' }
export function setAccent(v) { localStorage.setItem(K_ACCENT, v) }
export function setSpeed(v) { localStorage.setItem(K_SPEED, v) }
export function setAutoPlay(on) { localStorage.setItem(K_AUTOPLAY, on ? 'on' : 'off') }

// Backend speed param for each user-facing speed label.
const SPEED_VALUES = { slow: 0.75, normal: 1.0 }

let _audio = null
function getAudio() {
  if (!_audio) {
    _audio = new Audio()
    _audio.preload = 'auto'
  }
  return _audio
}

// Monotonic id so stale audio callbacks are ignored after a newer play.
let _playId = 0

// URL / audio-ref patterns that must NEVER be spoken as text.
const URL_PATTERN = /^(https?:\/\/|ftp:\/\/|www\.)/i
const AUDIO_EXT_PATTERN = /\.(mp3|wav|ogg|m4a|spx|aac|flac)(\?.*)?$/i
const SOUND_REF_PATTERN = /^(sound|dict|mdx|mdict):\/\//i

function isUrlLike(text) {
  const t = String(text).trim()
  return URL_PATTERN.test(t) || AUDIO_EXT_PATTERN.test(t) || SOUND_REF_PATTERN.test(t)
}

function _backendUrl(text, accent, speed) {
  const voice = accent === 'uk' ? 'uk' : 'us'
  const s = SPEED_VALUES[speed] ?? 1.0
  return `/api/audio/${encodeURIComponent(text)}?voice=${voice}&speed=${s}`
}

function _systemVoice() {
  if (!window.speechSynthesis) return null
  const voices = window.speechSynthesis.getVoices()
  const preferred = ['Microsoft Aria', 'Microsoft Jenny', 'Microsoft Zira', 'Microsoft Guy', 'Microsoft David', 'Google US English', 'Samantha']
  for (const name of preferred) {
    const v = voices.find((v) => v.name.includes(name) && v.lang.startsWith('en'))
    if (v) return v
  }
  return voices.find((v) => v.lang === 'en-US') || voices.find((v) => v.lang.startsWith('en')) || null
}

function _systemSpeak(text, accent, speed, onEnd) {
  if (!window.speechSynthesis) { onEnd?.(); return }
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(text)
  u.lang = accent === 'uk' ? 'en-GB' : 'en-US'
  u.rate = speed === 'slow' ? 0.75 : 0.95
  u.pitch = 1.0
  const voice = _systemVoice()
  if (voice) u.voice = voice
  u.onend = () => onEnd?.()
  u.onerror = () => onEnd?.()
  window.speechSynthesis.speak(u)
}

/** Stop whatever is currently playing. */
export function stop() {
  const a = getAudio()
  a.pause()
  a.onended = null
  a.onerror = null
  a.removeAttribute('src')
  a.load()
  if (window.speechSynthesis) window.speechSynthesis.cancel()
}

/**
 * Play text via Neural TTS, falling back to system TTS when the request fails.
 * `onEnd` is called once playback finishes (either path).
 *
 * Strictly rejects non-string and URL-like input — a word pronunciation must be
 * exactly the word, never a URL / audio address / dictionary link.
 */
export function speak(text, opts = {}) {
  const accent = opts.accent || getAccent()
  const speed = opts.speed || getSpeed()
  const onEnd = opts.onEnd

  if (typeof text !== 'string') {
    console.error('[TTS] refuse non-string input:', text)
    onEnd?.(); return
  }
  const clean = text.trim()
  if (!clean) { onEnd?.(); return }
  if (isUrlLike(clean)) {
    console.error('[TTS] refuse URL-like text:', clean)
    onEnd?.(); return
  }
  if (import.meta.env?.DEV) console.debug('[TTS WORD]', clean)

  const id = ++_playId
  stop()

  const a = getAudio()
  a.onended = () => { if (id === _playId) onEnd?.() }
  a.onerror = () => {
    if (id !== _playId) return
    _systemSpeak(clean, accent, speed, onEnd)
  }
  a.src = _backendUrl(clean, accent, speed)
  a.play().catch(() => {
    if (id === _playId) _systemSpeak(clean, accent, speed, onEnd)
  })
}

/**
 * Play an audio-file URL directly (NOT through TTS). Used when an API returns an
 * ``audio_url`` field — that URL must go to the <audio> player, never to speak().
 */
export function playAudioUrl(url) {
  if (typeof url !== 'string' || !URL_PATTERN.test(url.trim())) {
    console.error('[TTS] playAudioUrl requires an http(s) URL, got:', url)
    return
  }
  const id = ++_playId
  stop()
  const a = getAudio()
  a.onended = null
  a.onerror = null
  a.src = url.trim()
  a.play().catch(() => { if (id === _playId) { /* play failed */ } })
}

/**
 * Warm the backend cache for upcoming text without playing it. Called for the
 * next 1–2 words while the current word is being studied.
 */
export function preload(text, opts = {}) {
  const accent = opts.accent || getAccent()
  const speed = opts.speed || getSpeed()
  if (!text) return
  const a = new Audio()
  a.preload = 'auto'
  a.src = _backendUrl(text, accent, speed)
  a.load()
}

/** Preload several texts (e.g. current + next words). */
export function preloadQueue(texts, opts = {}) {
  ;(texts || []).slice(0, 3).forEach((t) => t && preload(t, opts))
}
