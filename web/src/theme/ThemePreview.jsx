/**
 * ThemePreview — live preview card showing WordMaster UI elements
 * with the currently-selected theme colors applied.
 */
export default function ThemePreview({ theme }) {
  if (!theme) return null
  const v = theme.light

  return (
    <div style={{
      borderRadius: 'var(--radius-lg)',
      backgroundColor: v['--background'],
      border: '1px solid ' + v['--border'],
      padding: '1rem',
      transition: 'var(--theme-transition)',
      overflow: 'hidden',
    }}>
      {/* Logo + brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.85rem' }}>
        <div style={{
          width: 28, height: 28, borderRadius: 'var(--radius-sm)',
          backgroundColor: v['--primary'],
          color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.75rem', fontWeight: 700,
        }}>W</div>
        <span style={{ color: v['--text-primary'], fontWeight: 700, fontSize: '0.8125rem' }}>WordMaster</span>
        <span style={{ color: v['--text-tertiary'], fontSize: '0.625rem', marginLeft: 'auto' }}>预览</span>
      </div>

      {/* Word card preview */}
      <div style={{
        borderRadius: 'var(--radius-lg)',
        backgroundColor: v['--surface'],
        border: '1px solid ' + v['--border'],
        padding: '0.85rem 1rem',
        marginBottom: '0.65rem',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem',
      }}>
        <span style={{ color: v['--text-primary'], fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.03em' }}>
          vocabulary
        </span>
        <span style={{ color: v['--text-tertiary'], fontSize: '0.6875rem' }}>/vəˈkæbjəleri/</span>
        <span style={{ color: v['--text-primary'], fontSize: '0.9375rem', fontWeight: 600 }}>n. 词汇，词汇量</span>
      </div>

      {/* Buttons preview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.35rem', marginBottom: '0.65rem' }}>
        {[
          { label: '已掌握', bg: v['--primary'], color: '#fff' },
          { label: '认识', bg: v['--success'], color: '#fff' },
          { label: '模糊', bg: v['--warning'], color: '#fff' },
          { label: '不会', bg: v['--danger'], color: '#fff' },
        ].map((btn, i) => (
          <div key={i} style={{
            padding: '0.35rem 0',
            borderRadius: 'var(--radius-md)',
            backgroundColor: btn.bg,
            color: btn.color,
            textAlign: 'center', fontSize: '0.625rem', fontWeight: 600,
          }}>{btn.label}</div>
        ))}
      </div>

      {/* Stats mini */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.35rem',
      }}>
        {[
          { label: '待复习', value: '12', accent: v['--warning'] },
          { label: '已学习', value: '104', accent: v['--primary'] },
        ].map((s, i) => (
          <div key={i} style={{
            padding: '0.45rem 0.65rem',
            borderRadius: 'var(--radius-md)',
            backgroundColor: v['--surface'],
            border: '1px solid ' + v['--border'],
            borderLeft: `3px solid ${s.accent}`,
          }}>
            <span style={{ color: v['--text-tertiary'], fontSize: '0.5625rem', fontWeight: 600, textTransform: 'uppercase' }}>
              {s.label}
            </span>
            <div style={{ color: v['--text-primary'], fontSize: '0.9375rem', fontWeight: 700 }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Color chips */}
      <div style={{ display: 'flex', gap: '0.3rem', marginTop: '0.65rem', justifyContent: 'center' }}>
        {[v['--primary'], v['--accent'], v['--background'], v['--surface'], v['--text-primary']].map((c, i) => (
          <div key={i} title={c} style={{
            width: 14, height: 14, borderRadius: '50%', backgroundColor: c,
            border: '1px solid ' + v['--border'],
          }} />
        ))}
      </div>
    </div>
  )
}
