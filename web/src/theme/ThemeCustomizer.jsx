import { useState, useCallback } from 'react'
import { ArrowLeft, Check, Palette, Plus, Sparkles } from 'lucide-react'
import { useTheme } from './ThemeContext'
import { buildCustomTheme } from './themeConfig'
import ThemePreview from './ThemePreview'

/** Single RGB color row with color input + RGB fields + HEX display */
function ColorRow({ label, hex, onChange }) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)

  const updateFromRgb = (rr, gg, bb) => {
    const h = '#' + [rr, gg, bb].map(v =>
      Math.max(0, Math.min(255, parseInt(v) || 0)).toString(16).padStart(2, '0')
    ).join('')
    onChange(h)
  }

  return (
    <div style={{
      padding: '0.85rem 1rem',
      borderRadius: 'var(--radius-md)',
      backgroundColor: 'var(--surface-secondary)',
      border: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column', gap: '0.55rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <input type="color" value={hex}
          onChange={e => onChange(e.target.value)}
          style={{
            width: 28, height: 28, border: 'none', borderRadius: 'var(--radius-sm)',
            cursor: 'pointer', padding: 0, background: 'none',
          }} />
        <span className="text-[13px] font-semibold" style={{ color: 'var(--text-primary)' }}>{label}</span>
        <code className="text-[11px] font-mono ml-auto" style={{ color: 'var(--text-tertiary)' }}>
          {hex.toUpperCase()}
        </code>
      </div>
      <div style={{ display: 'flex', gap: '0.35rem' }}>
        {[
          { label: 'R', val: r },
          { label: 'G', val: g },
          { label: 'B', val: b },
        ].map(({ label, val }) => (
          <div key={label} style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <span className="text-[10px] font-bold" style={{ color: 'var(--text-tertiary)', width: 10 }}>{label}</span>
            <input
              type="number" min={0} max={255} value={val}
              onChange={e => {
                const v = e.target.value === '' ? 0 : parseInt(e.target.value)
                if (label === 'R') updateFromRgb(v, g, b)
                if (label === 'G') updateFromRgb(r, v, b)
                if (label === 'B') updateFromRgb(r, g, v)
              }}
              style={{
                flex: 1, padding: '0.25rem 0.35rem', borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
                color: 'var(--text-primary)', fontSize: '0.6875rem', fontFamily: 'monospace',
                outline: 'none', textAlign: 'center',
              }}
            />
          </div>
        ))}
        <code className="text-[11px] font-mono self-end pb-0.5"
          style={{ color: 'var(--text-tertiary)', minWidth: 55, textAlign: 'right' }}>
          rgb({r},{g},{b})
        </code>
      </div>
    </div>
  )
}

export default function ThemeCustomizer({ onBack }) {
  const { setCustomTheme, themeDef } = useTheme()
  const [name, setName] = useState('我的主题')
  const [primary, setPrimary] = useState('#6366F1')
  const [accent, setAccent] = useState('#60A5FA')
  const [bg, setBg] = useState('#FAFAF9')
  const [surface, setSurface] = useState('#FFFFFF')
  const [text, setText] = useState('#1A1A1C')
  const [bgType, setBgType] = useState('solid')
  const [gradFrom, setGradFrom] = useState('#ECFDF5')
  const [gradTo, setGradTo] = useState('#F0FDF4')
  const [gradDir, setGradDir] = useState('diagonal')
  const [particleCount, setParticleCount] = useState(30)
  const [particleColor, setParticleColor] = useState('#60A5FA')

  const config = { name, primary, accent, bg, surface, text, bgType }
  if (bgType === 'gradient') config.bgGradient = { from: gradFrom, to: gradTo, direction: gradDir }
  if (bgType === 'particles') config.particles = { count: particleCount, color: particleColor, opacity: 0.6 }
  const previewTheme = buildCustomTheme(config)

  const handleSave = () => {
    setCustomTheme(config)
    onBack?.()
  }

  return (
    <div className="page animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1.5rem' }}>
        <button onClick={onBack} className="ios-icon-button"><ArrowLeft size={19} /></button>
        <div>
          <h1 className="text-lg font-bold tracking-tight" style={{ color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            自定义主题
          </h1>
          <p className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>创建你的专属学习配色</p>
        </div>
        <button onClick={handleSave}
          className="ios-button ios-button-primary ml-auto"
          style={{ borderRadius: 'var(--radius-md)', padding: '0.5rem 1.25rem', fontSize: '0.8125rem' }}>
          <Check size={15} /> 保存
        </button>
      </div>

      {/* ── Preview ── */}
      <div style={{ marginBottom: '1.25rem' }}>
        <p className="text-[11px] font-semibold uppercase tracking-wider mb-2 px-1"
          style={{ color: 'var(--text-tertiary)' }}>实时预览</p>
        <ThemePreview theme={previewTheme} />
      </div>

      {/* ── Name ── */}
      <div style={{ marginBottom: '0.75rem' }}>
        <input
          type="text" value={name}
          onChange={e => setName(e.target.value)}
          placeholder="主题名称"
          className="input text-sm"
          style={{ borderRadius: 'var(--radius-md)' }}
        />
      </div>

      {/* ── Colors ── */}
      <p className="text-[11px] font-semibold uppercase tracking-wider mb-2 px-1"
        style={{ color: 'var(--text-tertiary)' }}>颜色设置</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.25rem' }}>
        <ColorRow label="Primary 主色" hex={primary} onChange={setPrimary} />
        <ColorRow label="Accent 强调色" hex={accent} onChange={setAccent} />
        <ColorRow label="Background 背景色" hex={bg} onChange={setBg} />
        <ColorRow label="Surface 卡片色" hex={surface} onChange={setSurface} />
        <ColorRow label="Text 文字色" hex={text} onChange={setText} />
      </div>

      {/* ── Background Type ── */}
      <p className="text-[11px] font-semibold uppercase tracking-wider mb-2 px-1"
        style={{ color: 'var(--text-tertiary)' }}>背景类型</p>
      <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '1rem' }}>
        {[
          { key: 'solid', label: '纯色', icon: Palette },
          { key: 'gradient', label: '渐变', icon: null },
          { key: 'particles', label: '星光', icon: Sparkles },
        ].map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setBgType(key)}
            style={{
              flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.3rem',
              padding: '0.5rem', borderRadius: 'var(--radius-sm)',
              backgroundColor: bgType === key ? 'var(--accent-subtle)' : 'var(--surface-tertiary)',
              border: bgType === key ? '1.5px solid var(--accent)' : '1.5px solid transparent',
              color: bgType === key ? 'var(--accent)' : 'var(--text-secondary)',
              cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600,
              transition: 'all 0.2s ease',
            }}>
            {Icon && <Icon size={13} />}
            {label}
          </button>
        ))}
      </div>

      {/* Gradient settings */}
      {bgType === 'gradient' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <div style={{ flex: 1 }}>
              <span className="text-[10px] font-semibold" style={{ color: 'var(--text-tertiary)' }}>起始色</span>
              <input type="color" value={gradFrom} onChange={e => setGradFrom(e.target.value)}
                style={{ width: '100%', height: 32, border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer', marginTop: 2 }} />
            </div>
            <div style={{ flex: 1 }}>
              <span className="text-[10px] font-semibold" style={{ color: 'var(--text-tertiary)' }}>结束色</span>
              <input type="color" value={gradTo} onChange={e => setGradTo(e.target.value)}
                style={{ width: '100%', height: 32, border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer', marginTop: 2 }} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.4rem' }}>
            {['horizontal', 'vertical', 'diagonal'].map(d => (
              <button key={d} onClick={() => setGradDir(d)}
                style={{
                  flex: 1, padding: '0.35rem', borderRadius: 'var(--radius-sm)',
                  backgroundColor: gradDir === d ? 'var(--accent-subtle)' : 'var(--surface-tertiary)',
                  border: gradDir === d ? '1.5px solid var(--accent)' : '1.5px solid transparent',
                  color: gradDir === d ? 'var(--accent)' : 'var(--text-secondary)',
                  cursor: 'pointer', fontSize: '0.6875rem', fontWeight: 600,
                  textTransform: 'capitalize',
                }}>
                {d === 'horizontal' ? '水平' : d === 'vertical' ? '垂直' : '对角'}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Particle settings */}
      {bgType === 'particles' && (
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
          <div style={{ flex: 1 }}>
            <span className="text-[10px] font-semibold" style={{ color: 'var(--text-tertiary)' }}>数量 (1-50)</span>
            <input type="range" min={1} max={50} value={particleCount}
              onChange={e => setParticleCount(parseInt(e.target.value))}
              style={{ width: '100%', marginTop: 2, accentColor: 'var(--accent)' }} />
            <span className="text-[10px]" style={{ color: 'var(--text-tertiary)' }}>{particleCount}</span>
          </div>
          <div>
            <span className="text-[10px] font-semibold" style={{ color: 'var(--text-tertiary)' }}>颜色</span>
            <input type="color" value={particleColor} onChange={e => setParticleColor(e.target.value)}
              style={{ width: 36, height: 28, border: 'none', borderRadius: 'var(--radius-sm)', cursor: 'pointer', display: 'block', marginTop: 2 }} />
          </div>
        </div>
      )}
    </div>
  )
}
