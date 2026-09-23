/**
 * ThemePreview — a live, self-contained mockup of the WordMaster homepage.
 *
 * It renders from the given theme's colors directly (inline styles), NOT from
 * the global CSS variables, so tweaking a color updates only this card until
 * the user actually applies the theme.
 */
import { textColorOn } from './themeUtils'
export default function ThemePreview({ theme, mode = 'light' }) {
  if (!theme) return null
  const v = theme[mode === 'dark' ? 'dark' : 'light'] || theme.light
  const onPrimary = textColorOn(v['--primary'])

  return (
    <div style={{
      borderRadius: 'var(--radius-lg)',
      backgroundColor: v['--background'],
      border: '1px solid ' + v['--border'],
      padding: '1rem',
      overflow: 'hidden',
      transition: 'background-color 0.2s ease, color 0.2s ease',
    }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.85rem' }}>
        <div style={{
          width: 26, height: 26, borderRadius: 'var(--radius-sm)',
          backgroundColor: v['--primary'], color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.7rem', fontWeight: 700,
        }}>W</div>
        <span style={{ color: v['--text-primary'], fontWeight: 700, fontSize: '0.8125rem' }}>WordMaster</span>
      </div>

      {/* Today's study card */}
      <div style={{
        borderRadius: 'var(--radius-lg)',
        backgroundColor: v['--surface'],
        border: '1px solid ' + v['--border'],
        padding: '0.85rem 1rem',
        marginBottom: '0.65rem',
      }}>
        <div style={{ color: v['--text-tertiary'], fontSize: '0.5625rem', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.3rem' }}>
          今日学习
        </div>
        <div style={{ color: v['--text-primary'], fontSize: '0.9375rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
          今天还有 18 个词
        </div>
        <div style={{
          marginTop: '0.6rem',
          borderRadius: 'var(--radius-md)',
          backgroundColor: v['--primary'],
          color: onPrimary,
          textAlign: 'center',
          padding: '0.4rem 0',
          fontSize: '0.6875rem',
          fontWeight: 600,
        }}>
          开始学习
        </div>
      </div>

      {/* Stat + insight */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: '0.4rem' }}>
        <div style={{
          padding: '0.5rem 0.7rem', borderRadius: 'var(--radius-md)',
          backgroundColor: v['--surface'], border: '1px solid ' + v['--border'],
          borderLeft: '3px solid ' + v['--accent'],
        }}>
          <div style={{ color: v['--text-tertiary'], fontSize: '0.5625rem', fontWeight: 600, textTransform: 'uppercase' }}>待复习</div>
          <div style={{ color: v['--text-primary'], fontSize: '1rem', fontWeight: 700 }}>12</div>
        </div>
        <div style={{
          padding: '0.5rem 0.7rem', borderRadius: 'var(--radius-md)',
          backgroundColor: v['--surface'], border: '1px solid ' + v['--border'],
        }}>
          <div style={{ color: v['--text-tertiary'], fontSize: '0.5625rem', fontWeight: 600, textTransform: 'uppercase' }}>AI 学习洞察</div>
          <div style={{ color: v['--text-secondary'], fontSize: '0.625rem', marginTop: '0.15rem' }}>最近你的易混词错误较多</div>
        </div>
      </div>
    </div>
  )
}
