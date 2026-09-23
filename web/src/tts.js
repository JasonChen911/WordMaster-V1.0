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
 */
export function speak(text, opts = {}) {
  const accent = opts.accent || getAccent()
  const speed = opts.speed || getSpeed()
  const onEnd = opts.onEnd
  if (!text) { onEnd?.(); return }

  const id = ++_playId
  stop()

  const a = getAudio()
  a.onended = () => { if (id === _playId) onEnd?.() }
  a.onerror = () => {
    if (id !== _playId) return
    _systemSpeak(text, accent, speed, onEnd)
  }
  a.src = _backendUrl(text, accent, speed)
  a.play().catch(() => {
    if (id === _playId) _systemSpeak(text, accent, speed, onEnd)
  })
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
