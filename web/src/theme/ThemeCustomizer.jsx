import { useState, useMemo } from 'react'
import { ArrowLeft, RotateCcw, Check } from 'lucide-react'
import { useTheme } from './ThemeContext'
import { buildThemeFromPrimary, DEFAULT_CUSTOM_PRIMARY } from './themeConfig'
import { toHex } from './themeUtils'
import ThemePresetSelector from './ThemePresetSelector'
import ColorPicker from './ColorPicker'
import ColorPalette from './ColorPalette'
import AdvancedColorInput from './AdvancedColorInput'
import ThemePreview from './ThemePreview'

/**
 * ThemeCustomizer — visual theme customization.
 *
 * The user picks a preset or a color, sees a live preview, and only *applies*
 * the theme when they confirm. Draft state is local, so backing out restores
 * the previously saved theme.
 */
export default function ThemeCustomizer({ onBack }) {
  const { setCustomTheme, setMode, customTheme, themeName, themeDef, mode } = useTheme()

  const [primary, setPrimary] = useState(() => {
    if (themeName === 'custom' && customTheme) {
      const h = toHex(customTheme.primary)
      if (h) return h
    }
    return toHex(themeDef?.light?.['--primary']) || DEFAULT_CUSTOM_PRIMARY
  })
  const [draftMode, setDraftMode] = useState(mode === 'dark' ? 'dark' : 'light')

  const previewTheme = useMemo(() => buildThemeFromPrimary(primary), [primary])

  const selectPreset = (preset) => {
    setPrimary(preset.primary)
    setDraftMode(preset.mode)
  }

  const restoreDefault = () => {
    setPrimary(DEFAULT_CUSTOM_PRIMARY)
    setDraftMode('light')
  }

  const applyTheme = () => {
    setCustomTheme({ primary })
    setMode(draftMode)
    onBack?.()
  }

  return (
    <div className="page animate-fade-in" style={{ maxWidth: 680 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1.5rem' }}>
        <button onClick={onBack} className="ios-icon-button" aria-label="返回（取消）">
          <ArrowLeft size={19} />
        </button>
        <div>
          <h1 className="text-lg font-bold tracking-tight" style={{ color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>自定义主题</h1>
          <p className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>先看颜色，再选颜色</p>
        </div>
      </div>

      {/* ── 主题预设 ── */}
      <SectionLabel>主题预设</SectionLabel>
      <div style={{ marginBottom: '1.25rem' }}>
        <ThemePresetSelector primary={primary} mode={draftMode} onSelect={selectPreset} />
      </div>

      {/* ── 强调色 / 颜色选择器 ── */}
      <SectionLabel>强调色</SectionLabel>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 280px', minWidth: 240 }}>
          <ColorPicker value={primary} onChange={setPrimary} />
        </div>

        {/* Current color */}
        <div style={{
          flex: '0 0 130px', display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', gap: '0.4rem',
          padding: '0.8rem', borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
        }}>
          <div style={{
            width: 44, height: 44, borderRadius: '50%',
            backgroundColor: primary, border: '1px solid var(--border)',
            boxShadow: '0 1px 4px rgba(0,0,0,0.15)',
          }} />
          <span className="text-[11px] font-semibold" style={{ color: 'var(--text-tertiary)' }}>当前颜色</span>
          <code className="text-[12px] font-mono font-semibold" style={{ color: 'var(--text-primary)' }}>
            {primary.toUpperCase()}
          </code>
        </div>
      </div>

      {/* ── 常用颜色 ── */}
      <SectionLabel>常用颜色</SectionLabel>
      <div style={{ marginBottom: '1.25rem' }}>
        <ColorPalette value={primary} onChange={setPrimary} />
      </div>

      {/* ── 实时预览 ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
        <SectionLabel>实时预览</SectionLabel>
        <div style={{ display: 'flex', gap: '0.25rem', padding: '0.15rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--surface-tertiary)' }}>
          {['light', 'dark'].map((m) => (
            <button key={m} onClick={() => setDraftMode(m)}
              style={{
                padding: '0.25rem 0.7rem', borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer',
                fontSize: '0.6875rem', fontWeight: 600,
                backgroundColor: draftMode === m ? 'var(--surface)' : 'transparent',
                color: draftMode === m ? 'var(--text-primary)' : 'var(--text-tertiary)',
              }}>
              {m === 'light' ? '浅色' : '深色'}
            </button>
          ))}
        </div>
      </div>
      <div style={{ marginBottom: '1.25rem' }}>
        <ThemePreview theme={previewTheme} mode={draftMode} />
      </div>

      {/* ── 高级设置 ── */}
      <div style={{ marginBottom: '1.25rem' }}>
        <AdvancedColorInput value={primary} onChange={setPrimary} />
      </div>

      {/* ── Actions ── */}
      <div style={{ display: 'flex', gap: '0.6rem', marginBottom: '1.5rem' }}>
        <button onClick={restoreDefault}
          className="ios-button ios-button-secondary flex-1"
          style={{ borderRadius: 'var(--radius-md)', justifyContent: 'center' }}>
          <RotateCcw size={15} /> 恢复默认
        </button>
        <button onClick={applyTheme}
          className="ios-button ios-button-primary flex-1"
          style={{ borderRadius: 'var(--radius-md)', justifyContent: 'center' }}>
          <Check size={15} /> 应用主题
        </button>
      </div>
    </div>
  )
}

function SectionLabel({ children }) {
  return (
    <p className="text-[11px] font-semibold uppercase tracking-wider mb-2 px-1" style={{ color: 'var(--text-tertiary)' }}>
      {children}
    </p>
  )
}
