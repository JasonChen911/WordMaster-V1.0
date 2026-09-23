import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ChevronRight, Volume2, VolumeX, Sparkles, FileText, User, Moon, Sun, Palette, Plus } from 'lucide-react'
import { isSoundEnabled, setSoundEnabled } from '../useSound'
import { useTheme } from '../theme/ThemeContext'
import ThemeCustomizer from '../theme/ThemeCustomizer'
import { getAccent, setAccent as persistAccent, getSpeed, setSpeed as persistSpeed, getAutoPlay, setAutoPlay as persistAutoPlay } from '../tts'

function Section({ title, children }) {
  return (
    <div className="mb-6">
      <h3 className="text-[11px] font-semibold uppercase tracking-wider mb-2 px-1"
        style={{ color: 'var(--text-tertiary)' }}>{title}</h3>
      <div className="rounded-2xl overflow-hidden"
        style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)' }}>
        {children}
      </div>
    </div>
  )
}

function Row({ icon: Icon, label, detail, onClick, right, last }) {
  return (
    <button onClick={onClick}
      className="w-full flex items-center gap-3 px-4 py-3.5 transition-all duration-200 hover:bg-[var(--surface-tertiary)] active:bg-[var(--surface-tertiary)]"
      style={{ borderBottom: last ? 'none' : '1px solid var(--border)' }}>
      {Icon && (
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: 'var(--surface-tertiary)' }}>
          <Icon size={15} style={{ color: 'var(--accent)' }} />
        </div>
      )}
      <span className="text-sm flex-1 text-left" style={{ color: 'var(--text-primary)' }}>{label}</span>
      {detail && <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{detail}</span>}
      {right}
      {onClick && <ChevronRight size={14} style={{ color: 'var(--text-tertiary)' }} />}
    </button>
  )
}

function ToggleRow({ icon: Icon, label, detail, checked, onChange, last }) {
  return (
    <div className="w-full flex items-center gap-3 px-4 py-3.5"
      style={{ borderBottom: last ? 'none' : '1px solid var(--border)' }}>
      {Icon && (
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: checked ? 'var(--accent-subtle)' : 'var(--surface-tertiary)' }}>
          <Icon size={15} style={{ color: checked ? 'var(--accent)' : 'var(--text-tertiary)' }} />
        </div>
      )}
      <div className="flex-1">
        <span className="text-sm" style={{ color: 'var(--text-primary)' }}>{label}</span>
        {detail && <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>{detail}</p>}
      </div>
      <button onClick={onChange}
        className="relative inline-flex h-7 w-12 items-center rounded-full transition-colors duration-200"
        style={{ backgroundColor: checked ? 'var(--accent)' : 'var(--surface-tertiary)' }}>
        <span className="inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform duration-200"
          style={{ transform: checked ? 'translateX(24px)' : 'translateX(4px)' }} />
      </button>
    </div>
  )
}

function ChoiceRow({ label, value, onChange, options, last }) {
  return (
    <div className="w-full flex items-center gap-3 px-4 py-3.5"
      style={{ borderBottom: last ? 'none' : '1px solid var(--border)' }}>
      <span className="text-sm flex-1" style={{ color: 'var(--text-primary)' }}>{label}</span>
      <div style={{ display: 'flex', gap: '0.25rem', padding: '0.15rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--surface-tertiary)' }}>
        {options.map((o) => (
          <button key={o.value} onClick={() => onChange(o.value)}
            style={{
              padding: '0.25rem 0.75rem', borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer',
              fontSize: '0.75rem', fontWeight: 600,
              backgroundColor: value === o.value ? 'var(--surface)' : 'transparent',
              color: value === o.value ? 'var(--text-primary)' : 'var(--text-tertiary)',
            }}>
            {o.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export default function Settings() {
  const navigate = useNavigate()
  const [soundOn, setSoundOn] = useState(() => isSoundEnabled())
  const [showCustomizer, setShowCustomizer] = useState(false)
  const { mode, toggleMode, themeName, setTheme, themes } = useTheme()
  const [accent, setAccent] = useState(() => getAccent())
  const [speed, setSpeed] = useState(() => getSpeed())
  const [autoPlay, setAutoPlay] = useState(() => getAutoPlay())

  const handleAccent = (v) => { setAccent(v); persistAccent(v) }
  const handleSpeed = (v) => { setSpeed(v); persistSpeed(v) }
  const handleAutoPlay = (v) => { setAutoPlay(v); persistAutoPlay(v) }

  if (showCustomizer) {
    return <ThemeCustomizer onBack={() => setShowCustomizer(false)} />
  }

  return (
    <div className="page page-transition">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <button onClick={() => navigate('/')} className="ios-icon-button"><ArrowLeft size={20} /></button>
        <h1 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>设置</h1>
      </div>

      {/* ── Appearance ── */}
      <Section title="外观">
        {/* Dark/Light toggle */}
        <ToggleRow
          icon={mode === 'dark' ? Moon : Sun}
          label={mode === 'dark' ? '深色模式' : '浅色模式'}
          detail={mode === 'dark' ? '已开启 · 点击切换浅色' : '已关闭 · 点击切换深色'}
          checked={mode === 'dark'}
          onChange={toggleMode}
        />

        {/* Theme selector — 6 official */}
        <div style={{ padding: '0.65rem 1rem', borderBottom: '1px solid var(--border)' }}>
          <span className="text-[11px] font-semibold uppercase tracking-wider"
            style={{ color: 'var(--text-tertiary)' }}>官方主题</span>
        </div>
        <div style={{ padding: '0.35rem 0.65rem', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.4rem' }}>
          {Object.entries(themes).map(([key, t]) => {
            const isActive = themeName === key
            const prime = t.light['--primary']
            const bg = t.light['--background']
            const text = t.light['--text-primary']
            return (
              <button
                key={key}
                onClick={() => setTheme(key)}
                style={{
                  padding: '0.6rem 0.5rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isActive ? 'var(--accent-subtle)' : bg,
                  border: isActive ? '1.5px solid var(--accent)' : `1px solid ${t.light['--border']}`,
                  cursor: 'pointer',
                  transition: 'all 0.25s ease',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.3rem',
                }}>
                <div style={{
                  width: 20, height: 20, borderRadius: '50%',
                  backgroundColor: prime,
                  boxShadow: isActive ? `0 0 8px color-mix(in srgb, ${prime} 40%, transparent)` : 'none',
                }} />
                <span className="text-[11px] font-semibold"
                  style={{ color: isActive ? 'var(--accent)' : text }}>{t.name.split(' ')[0]}</span>
              </button>
            )
          })}
        </div>

        {/* Custom theme entry */}
        <Row
          icon={Palette}
          label="自定义主题"
          detail={themeName === 'custom' ? '已自定义' : '创建你自己的主题'}
          onClick={() => setShowCustomizer(true)}
          right={themeName === 'custom' && (
            <span style={{
              width: 8, height: 8, borderRadius: '50%',
              backgroundColor: 'var(--accent)',
              display: 'inline-block',
            }} />
          )}
          last
        />
      </Section>

      {/* ── Learning ── */}
      <Section title="学习设置">
        <ToggleRow icon={Volume2} label="学习音效"
          detail={soundOn ? '完成学习时播放音效' : '已关闭音效'}
          checked={soundOn}
          onChange={() => { const n = !soundOn; setSoundOn(n); setSoundEnabled(n) }}
          last />
      </Section>

      {/* ── 发音 ── */}
      <Section title="发音">
        <ChoiceRow label="口音" value={accent} onChange={handleAccent}
          options={[{ value: 'us', label: '美式英语' }, { value: 'uk', label: '英式英语' }]} />
        <ChoiceRow label="语速" value={speed} onChange={handleSpeed}
          options={[{ value: 'normal', label: '正常' }, { value: 'slow', label: '慢速' }]} />
        <ToggleRow icon={Volume2} label="自动发音"
          detail={autoPlay ? '进入新单词时自动朗读' : '仅点击发音按钮时朗读'}
          checked={autoPlay}
          onChange={() => handleAutoPlay(!autoPlay)}
          last />
      </Section>

      {/* ── AI ── */}
      <Section title="AI 服务">
        <Row icon={Sparkles} label="AI 服务设置" detail="DeepSeek API"
          onClick={() => navigate('/settings/ai')} last />
      </Section>

      {/* ── About ── */}
      <Section title="关于">
        <Row icon={FileText} label="软件使用协议" onClick={() => navigate('/agreement')} />
        <Row icon={User} label="制作人信息" onClick={() => navigate('/about')} last />
      </Section>

      <div className="mt-8 text-center">
        <span className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>
          WordMaster v0.1.0 Beta
        </span>
      </div>
    </div>
  )
}
