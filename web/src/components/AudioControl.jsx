import { useState, useRef, useCallback } from 'react'
import { Volume2 } from 'lucide-react'
import { speak, getAccent } from '../tts'

/**
 * Unified pronunciation button — Neural TTS (edge-tts) with offline fallback.
 * Debounces rapid clicks and shows immediate visual feedback while playing.
 */
export default function AudioControl({ word, size = 'md' }) {
  const [playing, setPlaying] = useState(false)
  const lastPlayRef = useRef(0)

  const text = typeof word === 'string' ? word.trim() : ''
  const accent = getAccent()

  const handleClick = useCallback((e) => {
    e.stopPropagation()
    if (!text) return
    // Debounce: ignore rapid spam clicks within 250ms (no overlapping audio).
    const now = Date.now()
    if (now - lastPlayRef.current < 250) return
    lastPlayRef.current = now

    setPlaying(true)
    speak(text, { onEnd: () => setPlaying(false) })
  }, [text])

  if (!text) return null

  const dims = size === 'sm' ? { px: '0.4rem', py: '0.25rem', gap: '0.25rem' } : { px: '0.75rem', py: '0.4rem', gap: '0.35rem' }

  return (
    <button
      onClick={handleClick}
      aria-label={`朗读 ${text}`}
      className="inline-flex items-center rounded-xl text-xs font-semibold select-none transition-colors duration-150 active:scale-95"
      style={{
        padding: `${dims.py} ${dims.px}`,
        gap: dims.gap,
        backgroundColor: playing ? 'var(--accent)' : 'var(--accent-subtle)',
        color: playing ? '#fff' : 'var(--accent)',
        border: playing ? 'none' : '1px solid color-mix(in srgb, var(--accent) 20%, transparent)',
        cursor: 'pointer',
      }}
      title={accent === 'uk' ? '英式发音' : '美式发音'}
    >
      <Volume2 size={size === 'sm' ? 12 : 13} className={playing ? 'animate-pulse' : ''} />
      <span>{accent === 'uk' ? 'UK' : 'US'}</span>
    </button>
  )
}
