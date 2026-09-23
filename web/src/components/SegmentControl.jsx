import { useRef, useEffect, useState } from 'react'

/**
 * Apple-style Segmented Control — sliding indicator, glass texture, spring physics.
 *
 * The active pill measures the target button position and slides there
 * via CSS transition (left + width). No layout thrashing — the pill is
 * position:absolute so it floats above the button row.
 */
export default function SegmentControl({
  options,
  value,
  onChange,
  size = 'md',
  variant = 'default',
}) {
  const containerRef = useRef(null)
  const [pos, setPos] = useState({ left: 0, width: 0, ready: false })

  // Re-measure when value or options change
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const btns = el.querySelectorAll('[data-so]')
    const idx = options.indexOf(value)
    if (idx < 0 || idx >= btns.length) return
    const c = el.getBoundingClientRect()
    const b = btns[idx].getBoundingClientRect()
    const pad = parseFloat(getComputedStyle(el).paddingLeft) || 2
    setPos({ left: b.left - c.left - pad, width: b.width, ready: true })
  }, [value, options])

  const sz = { sm: { py: '0.3rem', px: '0.55rem', fs: '0.625rem' },
               md: { py: '0.4rem', px: '0',     fs: '0.6875rem' },
               lg: { py: '0.5rem', px: '0',     fs: '0.8125rem' } }[size] || {}

  const isGlass = variant === 'glass'

  return (
    <div ref={containerRef} style={{
      position: 'relative', display: 'inline-flex', alignItems: 'center',
      padding: '2.5px',
      borderRadius: 'var(--radius-sm)',
      backgroundColor: isGlass ? 'rgba(255,255,255,0.06)' : 'var(--surface)',
      border: isGlass ? '1px solid rgba(255,255,255,0.10)' : '1px solid var(--border)',
    }}>
      {/* Sliding pill */}
      <div style={{
        position: 'absolute', top: '2.5px',
        left: pos.left, width: pos.width || 1,
        height: 'calc(100% - 5px)',
        borderRadius: 'calc(var(--radius-sm) - 2px)',
        background: isGlass
          ? 'rgba(255,255,255,0.18)'
          : 'var(--accent)',
        boxShadow: isGlass
          ? '0 2px 12px rgba(255,255,255,0.08), inset 0 0.5px 0 rgba(255,255,255,0.15)'
          : '0 1px 4px color-mix(in srgb, var(--accent) 25%, transparent)',
        border: isGlass ? '1px solid rgba(255,255,255,0.18)' : 'none',
        opacity: pos.ready ? 1 : 0,
        transition: pos.ready
          ? 'left 0.3s cubic-bezier(0.22,1,0.36,1), width 0.3s cubic-bezier(0.22,1,0.36,1)'
          : 'none',
        pointerEvents: 'none',
      }} />

      {/* Buttons */}
      {options.map(opt => {
        const active = opt === value
        return (
          <button key={opt} data-so
            onClick={() => onChange(opt)}
            style={{
              position: 'relative', zIndex: 1,
              flex: options.length <= 6 ? 1 : undefined,
              paddingTop: sz.py, paddingBottom: sz.py,
              paddingLeft: sz.px, paddingRight: sz.px,
              border: 'none', borderRadius: 'calc(var(--radius-sm) - 2px)',
              backgroundColor: 'transparent',
              color: active ? '#fff' : 'var(--text-secondary)',
              fontSize: sz.fs, fontWeight: active ? 600 : 500,
              fontFamily: 'inherit', cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'color 0.2s ease, transform 0.12s ease, filter 0.15s ease',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.transform = 'translateY(-1px)'
              e.currentTarget.style.filter = 'brightness(1.1)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = 'none'
              e.currentTarget.style.filter = 'none'
            }}
            onMouseDown={e => { e.currentTarget.style.transform = 'scale(0.96)' }}
            onMouseUp={e => { e.currentTarget.style.transform = 'translateY(-1px)' }}>
            {opt}
          </button>
        )
      })}
    </div>
  )
}
