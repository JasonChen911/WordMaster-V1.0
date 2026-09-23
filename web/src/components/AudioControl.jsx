import { useState, useCallback, useRef } from 'react'
import { Volume2 } from 'lucide-react'

/**
 * System TTS — Windows SpeechSynthesis, no network, no API.
 * Professional dictionary-style button: 🔊 US
 */

function getUSVoice() {
  if (!window.speechSynthesis) return null
  const voices = window.speechSynthesis.getVoices()
  // Prefer Microsoft English US voices
  const preferred = ['Microsoft Aria', 'Microsoft Zira', 'Microsoft David', 'Microsoft Mark']
  for (const name of preferred) {
    const v = voices.find(v => v.name.includes(name) && v.lang.startsWith('en'))
    if (v) return v
  }
  return voices.find(v => v.lang === 'en-US') || voices.find(v => v.lang.startsWith('en')) || null
}

export default function AudioControl({ word, size = 'md' }) {
  const [playing, setPlaying] = useState(false)
  const voiceRef = useRef(null)

  // Lazy init voice on first interaction
  const ensureVoice = () => {
    if (voiceRef.current) return voiceRef.current
    voiceRef.current = getUSVoice()
    if (!voiceRef.current) {
      const voices = window.speechSynthesis.getVoices()
      voiceRef.current = getUSVoice() || voices[0] || null
    }
    return voiceRef.current
  }

  const text = typeof word === 'string' ? word.trim() : ''

  const handleClick = useCallback((e) => {
    e.stopPropagation()
    if (!text || !window.speechSynthesis) return

    window.speechSynthesis.cancel()
    const voice = ensureVoice()

    const u = new SpeechSynthesisUtterance(text)
    u.lang = 'en-US'
    u.rate = 0.85
    u.pitch = 1.0
    if (voice) u.voice = voice
    u.onstart = () => setPlaying(true)
    u.onend = () => setPlaying(false)
    u.onerror = () => setPlaying(false)

    window.speechSynthesis.speak(u)
  }, [text])

  if (!text) return null

  return (
    <button
      onClick={handleClick}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 hover:scale-105 active:scale-95 select-none"
      style={{
        backgroundColor: playing ? 'var(--accent)' : 'var(--accent-subtle)',
        color: playing ? '#fff' : 'var(--accent)',
        border: playing ? 'none' : '1px solid color-mix(in srgb, var(--accent) 20%, transparent)',
        cursor: 'pointer',
      }}
      title="美式发音"
    >
      <Volume2 size={13} />
      <span>US</span>
    </button>
  )
}
