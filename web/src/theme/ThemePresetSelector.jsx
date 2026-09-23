import { Check } from 'lucide-react'
import { CUSTOM_PRESETS } from './themeConfig'
import { deriveAccent } from './themeUtils'

/**
 * ThemePresetSelector — color thumbnail cards for the theme presets.
 *
 * Each card shows the preset's background, primary (button) and accent colors,
 * so the user sees the palette before selecting. Selection also shows a check
 * mark (not color alone) for accessibility.
 */
export default function ThemePresetSelector({ primary, mode, onSelect }) {
  const current = (primary || '').toLowerCase()

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.6rem' }}>
      {CUSTOM_PRESETS.map((p) => {
        const active = current === p.primary.toLowerCase()
        const accent = deriveAccent(p.primary)
        const bg = p.mode === 'dark' ? '#0C0C0E' : '#FAFAF9'
        const surface = p.mode === 'dark' ? '#1A1A1D' : '#FFFFFF'

        return (
          <button
            key={p.id}
            onClick={() => onSelect(p)}
            aria-label={`主题预设：${p.name}`}
            style={{
              padding: '0.6rem', borderRadius: 'var(--radius-md)', cursor: 'pointer',
              textAlign: 'left',
              backgroundColor: active ? 'var(--accent-subtle)' : 'var(--surface)',
              border: active ? '2px solid var(--accent)' : '1px solid var(--border)',
              transition: 'all 0.15s ease',
            }}
          >
            {/* Thumbnail */}
            <div style={{
              height: 44, borderRadius: 'var(--radius-sm)',
              backgroundColor: bg, border: '1px solid rgba(0,0,0,0.08)',
              display: 'flex', alignItems: 'center', gap: '0.35rem',
              padding: '0 0.5rem', marginBottom: '0.5rem',
            }}>
              <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: p.primary }} />
              <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: accent }} />
              <div style={{ flex: 1, height: 8, borderRadius: 100, backgroundColor: p.primary, marginLeft: '0.1rem' }} />
            </div>

            {/* Name + check */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-primary)', fontSize: '0.75rem', fontWeight: 600 }}>{p.name}</span>
              {active && <Check size={14} style={{ color: 'var(--accent)' }} />}
            </div>
          </button>
        )
      })}
    </div>
  )
}
