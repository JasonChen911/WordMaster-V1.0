import { useState, useEffect } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { hexToRgb, normalizeHex } from './themeUtils'

/**
 * AdvancedColorInput — precise HEX/RGB entry, collapsed behind a disclosure.
 *
 * HEX/RGB is deliberately NOT the primary interaction; it's only for users who
 * want exact values. Invalid input shows a friendly hint and never crashes.
 */
export default function AdvancedColorInput({ value, onChange }) {
  const [open, setOpen] = useState(false)
  const [hexDraft, setHexDraft] = useState(value)
  const [error, setError] = useState(null)

  const rgb = hexToRgb(value) || { r: 0, g: 0, b: 0 }

  // Keep the draft in sync when the picker changes the color elsewhere.
  useEffect(() => {
    setHexDraft(value)
    setError(null)
  }, [value])

  const commitHex = (raw) => {
    setHexDraft(raw)
    const hex = normalizeHex(raw)
    if (hex) {
      setError(null)
      onChange(hex)
    } else {
      setError('请输入合法的 HEX，例如 #6EA8FE')
    }
  }

  const commitRgbChannel = (ch, raw) => {
    const n = raw === '' ? 0 : parseInt(raw, 10)
    if (isNaN(n) || n < 0 || n > 255) {
      setError('RGB 值需在 0-255 之间')
      return
    }
    setError(null)
    const next = { ...rgb, [ch]: n }
    onChange(`#${[next.r, next.g, next.b].map((v) => v.toString(16).padStart(2, '0')).join('')}`)
  }

  return (
    <div style={{
      borderRadius: 'var(--radius-md)', border: '1px solid var(--border)',
      backgroundColor: 'var(--surface)', overflow: 'hidden',
    }}>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0.7rem 0.9rem', background: 'none', border: 'none', cursor: 'pointer',
        }}
      >
        <span className="text-[12px] font-semibold" style={{ color: 'var(--text-primary)' }}>高级设置</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="text-[11px] font-mono" style={{ color: 'var(--text-tertiary)' }}>{value.toUpperCase()}</span>
          {open ? <ChevronUp size={15} style={{ color: 'var(--text-tertiary)' }} /> : <ChevronDown size={15} style={{ color: 'var(--text-tertiary)' }} />}
        </span>
      </button>

      {open && (
        <div style={{ padding: '0 0.9rem 0.9rem', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          {/* HEX */}
          <div>
            <label className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>HEX</label>
            <input
              type="text"
              value={hexDraft}
              onChange={(e) => commitHex(e.target.value)}
              onBlur={() => { const h = normalizeHex(hexDraft); if (h) { setHexDraft(h); } else setHexDraft(value) }}
              spellCheck={false}
              style={{
                width: '100%', marginTop: 2, padding: '0.4rem 0.6rem', borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
                color: 'var(--text-primary)', fontSize: '0.8125rem', fontFamily: 'monospace', outline: 'none',
              }}
            />
          </div>

          {/* RGB */}
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
            {[['R', 'r'], ['G', 'g'], ['B', 'b']].map(([label, ch]) => (
              <div key={ch} style={{ flex: 1 }}>
                <label className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>{label}</label>
                <input
                  type="number" min={0} max={255} value={rgb[ch]}
                  onChange={(e) => commitRgbChannel(ch, e.target.value)}
                  style={{
                    width: '100%', marginTop: 2, padding: '0.4rem 0.4rem', borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
                    color: 'var(--text-primary)', fontSize: '0.8125rem', fontFamily: 'monospace',
                    outline: 'none', textAlign: 'center',
                  }}
                />
              </div>
            ))}
          </div>

          {error && (
            <p className="text-[11px]" style={{ color: 'var(--danger)' }}>{error}</p>
          )}
        </div>
      )}
    </div>
  )
}
