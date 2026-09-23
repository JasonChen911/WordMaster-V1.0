import { Check } from 'lucide-react'
import { COMMON_COLORS } from './themeConfig'

/**
 * ColorPalette — a short row of common-color swatches. Clicking one applies it
 * immediately (the swatches are actual colors, not just names).
 */
export default function ColorPalette({ value, onChange }) {
  const current = (value || '').toLowerCase()

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
      {COMMON_COLORS.map((c) => {
        const active = current === c
        return (
          <button
            key={c}
            onClick={() => onChange(c)}
            aria-label={`选择颜色 ${c}`}
            title={c}
            style={{
              width: 28, height: 28, borderRadius: '50%',
              backgroundColor: c,
              border: active ? '2px solid var(--text-primary)' : '1px solid var(--border)',
              cursor: 'pointer', padding: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'transform 0.15s ease',
              boxShadow: active ? '0 0 0 2px var(--surface)' : 'none',
            }}
          >
            {active && <Check size={13} style={{ color: '#fff' }} />}
          </button>
        )
      })}
    </div>
  )
}
