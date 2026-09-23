/**
 * Lightweight sound effects using Web Audio API.
 * No external audio files needed — pure synthesized sounds.
 * Toggle via localStorage 'wordmaster-sound-enabled'.
 */

const AudioCtx = window.AudioContext || window.webkitAudioContext

let _ctx = null
function getCtx() {
  if (!_ctx) _ctx = new AudioCtx()
  return _ctx
}

export function isSoundEnabled() {
  return localStorage.getItem('wordmaster-sound-enabled') !== 'false'
}

export function setSoundEnabled(enabled) {
  localStorage.setItem('wordmaster-sound-enabled', String(enabled))
}

/** Soft whoosh — rising filtered noise burst */
export function playWhoosh() {
  if (!isSoundEnabled()) return
  try {
    const ctx = getCtx()
    const duration = 0.6
    const sampleRate = ctx.sampleRate
    const length = Math.floor(duration * sampleRate)
    const buffer = ctx.createBuffer(1, length, sampleRate)
    const data = buffer.getChannelData(0)

    for (let i = 0; i < length; i++) {
      const t = i / sampleRate
      const envelope = Math.sin((t / duration) * Math.PI) // smooth fade in/out
      const noise = (Math.random() * 2 - 1) * 0.15
      // Frequency sweep: low → high
      const sweep = Math.sin(t * (200 + t * 2000) * Math.PI * 2) * 0.08
      data[i] = (noise + sweep) * envelope
    }

    const src = ctx.createBufferSource()
    src.buffer = buffer
    const filter = ctx.createBiquadFilter()
    filter.type = 'lowpass'
    filter.frequency.setValueAtTime(300, ctx.currentTime)
    filter.frequency.linearRampToValueAtTime(3000, ctx.currentTime + duration)

    const gain = ctx.createGain()
    gain.gain.setValueAtTime(0.25, ctx.currentTime)
    gain.gain.linearRampToValueAtTime(0, ctx.currentTime + duration)

    src.connect(filter)
    filter.connect(gain)
    gain.connect(ctx.destination)
    src.start()
  } catch (e) { /* audio not available */ }
}

/** Clean chime — two sine tones with gentle decay */
export function playChime() {
  if (!isSoundEnabled()) return
  try {
    const ctx = getCtx()
    const now = ctx.currentTime

    function tone(freq, start, dur, vol = 0.2) {
      const osc = ctx.createOscillator()
      osc.type = 'sine'
      osc.frequency.value = freq

      const gain = ctx.createGain()
      gain.gain.setValueAtTime(vol, now + start)
      gain.gain.exponentialRampToValueAtTime(0.001, now + start + dur)

      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(now + start)
      osc.stop(now + start + dur)
    }

    // Two-note chime: C5 → E5
    tone(523.25, 0, 0.5, 0.18)
    tone(659.25, 0.12, 0.6, 0.14)

    // Subtle harmonic
    const harm = ctx.createOscillator()
    harm.type = 'sine'
    harm.frequency.value = 1046.5
    const hGain = ctx.createGain()
    hGain.gain.setValueAtTime(0.06, now + 0.15)
    hGain.gain.exponentialRampToValueAtTime(0.001, now + 0.8)
    harm.connect(hGain)
    hGain.connect(ctx.destination)
    harm.start(now + 0.15)
    harm.stop(now + 0.8)
  } catch (e) { /* audio not available */ }
}

/** Tick sound for number counting */
export function playTick() {
  if (!isSoundEnabled()) return
  try {
    const ctx = getCtx()
    const now = ctx.currentTime
    const osc = ctx.createOscillator()
    osc.type = 'sine'
    osc.frequency.value = 800

    const gain = ctx.createGain()
    gain.gain.setValueAtTime(0.06, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05)

    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(now)
    osc.stop(now + 0.05)
  } catch (e) { /* audio not available */ }
}
