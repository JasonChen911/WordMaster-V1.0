/**
 * WordMaster Theme System — Crystalline Literacy
 *
 * Each theme defines a complete set of CSS custom properties.
 * Light + dark variants are defined per theme for proper mode switching.
 *
 * Custom themes are stored in localStorage and merged at runtime.
 */

// ═══════════════════════════════════════════════════════════════
// Shared token generators
// ═══════════════════════════════════════════════════════════════

const rad = { sm: '8px', md: '12px', lg: '16px', xl: '20px', '2xl': '24px' }

const shadowLight = '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)'
const shadowDark  = '0 1px 3px rgba(0,0,0,0.2)'

function makeTheme(vars) {
  return {
    name: vars._name,
    description: vars._desc || '',
    backgroundType: vars._bgType || 'solid',
    backgroundGradient: vars._bgGradient || null,
    particles: vars._particles || null,
    light: {
      '--primary':           vars._primary,
      '--accent':            vars._accent,
      '--background':        vars._bg,
      '--surface':           vars._surface,
      '--surface-secondary': vars._surfaceSecondary || vars._surface,
      '--surface-tertiary':  vars._surfaceTertiary,
      '--text-primary':      vars._textPrimary,
      '--text-secondary':    vars._textSecondary,
      '--text-tertiary':     vars._textTertiary,
      '--text-inverse':      vars._textInverse,
      '--border':            vars._border,
      '--border-strong':     vars._borderStrong,
      '--danger':            vars._danger || '#ef4444',
      '--danger-subtle':     vars._dangerSubtle || 'rgba(239,68,68,0.08)',
      '--warning':           vars._warning || '#f59e0b',
      '--warning-subtle':    vars._warningSubtle || 'rgba(245,158,11,0.08)',
      '--success':           vars._success || '#10b981',
      '--success-subtle':    vars._successSubtle || 'rgba(16,185,129,0.08)',
      '--accent-subtle':     `color-mix(in srgb, ${vars._accent} 8%, transparent)`,
      '--accent-hover':      vars._accentHover || vars._accent,
      '--glass-bg':          `color-mix(in srgb, ${vars._surface} 72%, transparent)`,
      '--glass-border':      `color-mix(in srgb, ${vars._surface} 50%, transparent)`,
      '--glass-shadow':      shadowLight,
      '--radius-sm':         rad.sm,
      '--radius-md':         rad.md,
      '--radius-lg':         rad.lg,
      '--radius-xl':         rad.xl,
      '--radius-2xl':        rad['2xl'],
    },
    dark: {
      '--primary':           vars._primaryDark || vars._primary,
      '--accent':            vars._accentDark || vars._accent,
      '--background':        vars._bgDark,
      '--surface':           vars._surfaceDark || vars._bgDark,
      '--surface-secondary': vars._surfaceSecondaryDark || vars._surfaceDark || vars._bgDark,
      '--surface-tertiary':  vars._surfaceTertiaryDark,
      '--text-primary':      vars._textPrimaryDark,
      '--text-secondary':    vars._textSecondaryDark,
      '--text-tertiary':     vars._textTertiaryDark,
      '--text-inverse':      vars._textInverseDark || vars._textPrimary,
      '--border':            vars._borderDark,
      '--border-strong':     vars._borderStrongDark,
      '--danger':            vars._dangerDark || '#f87171',
      '--danger-subtle':     vars._dangerSubtleDark || 'rgba(248,113,113,0.10)',
      '--warning':           vars._warningDark || '#fbbf24',
      '--warning-subtle':    vars._warningSubtleDark || 'rgba(251,191,36,0.10)',
      '--success':           vars._successDark || '#34d399',
      '--success-subtle':    vars._successSubtleDark || 'rgba(52,211,153,0.10)',
      '--accent-subtle':     `color-mix(in srgb, ${vars._accentDark || vars._accent} 12%, transparent)`,
      '--accent-hover':      vars._accentHoverDark || vars._accentDark || vars._accent,
      '--glass-bg':          `color-mix(in srgb, ${vars._surfaceDark || vars._bgDark} 75%, transparent)`,
      '--glass-border':      `color-mix(in srgb, ${vars._surfaceDark || vars._bgDark} 60%, transparent)`,
      '--glass-shadow':      shadowDark,
    },
  }
}

// ═══════════════════════════════════════════════════════════════
// Official Themes
// ═══════════════════════════════════════════════════════════════

export const THEMES = {

  crystalline: makeTheme({
    _name: 'Crystalline 水晶',
    _desc: '暖白背景 · 靛紫主色 · 水晶玻璃感',
    _primary:    '#6366F1',
    _accent:     '#60A5FA',
    _bg:         '#FAFAF9',
    _surface:    '#FFFFFF',
    _surfaceTertiary: '#F0F0EE',
    _textPrimary:   '#1A1A1C',
    _textSecondary: '#6B6B70',
    _textTertiary:  '#A0A0A6',
    _textInverse:   '#FFFFFF',
    _border:        'rgba(0,0,0,0.06)',
    _borderStrong:  'rgba(0,0,0,0.12)',
    // Dark
    _primaryDark:   '#818CF8',
    _accentDark:    '#60A5FA',
    _bgDark:        '#0C0C0E',
    _surfaceDark:   '#1A1A1D',
    _surfaceTertiaryDark: '#26262A',
    _textPrimaryDark:   '#F4F4F6',
    _textSecondaryDark: '#9D9DA4',
    _textTertiaryDark:  '#5E5E66',
    _borderDark:        'rgba(255,255,255,0.07)',
    _borderStrongDark:  'rgba(255,255,255,0.11)',
  }),

  starlight: makeTheme({
    _name: 'Starlight 星光',
    _desc: '深空星辰 · 专注学习 · 星光闪烁',
    _bgType: 'particles',
    _particles: { count: 60, color: '#94A3B8', opacity: 0.7 },
    _primary:    '#818CF8',
    _accent:     '#A78BFA',
    _bg:         '#020617',
    _surface:    'rgba(15,23,42,0.75)',
    _surfaceTertiary: 'rgba(30,41,59,0.60)',
    _textPrimary:   '#E2E8F0',
    _textSecondary: '#94A3B8',
    _textTertiary:  '#64748B',
    _textInverse:   '#020617',
    _border:        'rgba(148,163,184,0.10)',
    _borderStrong:  'rgba(148,163,184,0.18)',
    // Dark (Starlight is inherently dark)
    _primaryDark:   '#A5B4FC',
    _accentDark:    '#C4B5FD',
    _bgDark:        '#020617',
    _surfaceDark:   'rgba(15,23,42,0.75)',
    _surfaceTertiaryDark: 'rgba(30,41,59,0.60)',
    _textPrimaryDark:   '#E2E8F0',
    _textSecondaryDark: '#94A3B8',
    _textTertiaryDark:  '#64748B',
    _borderDark:        'rgba(148,163,184,0.10)',
    _borderStrongDark:  'rgba(148,163,184,0.18)',
    // Glass surface
    _surfaceSecondary: 'rgba(15,23,42,0.85)',
    _surfaceSecondaryDark: 'rgba(15,23,42,0.85)',
  }),

  ocean: makeTheme({
    _name: 'Ocean 深海',
    _desc: '深海蓝绿 · 安静专注 · 沉浸学习',
    _primary:    '#0EA5E9',
    _accent:     '#06B6D4',
    _bg:         '#0A1628',
    _surface:    '#112240',
    _surfaceTertiary: '#1D3461',
    _textPrimary:   '#E2E8F0',
    _textSecondary: '#94A3B8',
    _textTertiary:  '#546E8A',
    _textInverse:   '#0A1628',
    _border:        'rgba(14,165,233,0.10)',
    _borderStrong:  'rgba(14,165,233,0.18)',
    _success:       '#06B6D4',
    _danger:        '#F43F5E',
    _warning:       '#F59E0B',
    // Dark (Ocean is deep)
    _primaryDark:   '#38BDF8',
    _accentDark:    '#22D3EE',
    _bgDark:        '#0A1628',
    _surfaceDark:   '#112240',
    _surfaceTertiaryDark: '#1D3461',
    _textPrimaryDark:   '#E2E8F0',
    _textSecondaryDark: '#94A3B8',
    _textTertiaryDark:  '#546E8A',
    _borderDark:        'rgba(14,165,233,0.10)',
    _borderStrongDark:  'rgba(14,165,233,0.18)',
  }),

  aurora: makeTheme({
    _name: 'Aurora 极光',
    _desc: '北境极光 · 流动光带 · 沉浸学习',
    _bgType: 'aurora',
    _primary:    '#22D3EE',
    _accent:     '#A78BFA',
    _bg:         '#061826',
    _surface:    'rgba(255,255,255,0.08)',
    _surfaceTertiary: 'rgba(255,255,255,0.05)',
    _textPrimary:   '#E2E8F0',
    _textSecondary: '#94A3B8',
    _textTertiary:  '#64748B',
    _textInverse:   '#061826',
    _border:        'rgba(34,211,238,0.10)',
    _borderStrong:  'rgba(34,211,238,0.18)',
    _success:       '#34D399',
    _danger:        '#F87171',
    _warning:       '#FBBF24',
    // Dark (Aurora is night-native)
    _primaryDark:   '#22D3EE',
    _accentDark:    '#A78BFA',
    _bgDark:        '#061826',
    _surfaceDark:   'rgba(255,255,255,0.08)',
    _surfaceTertiaryDark: 'rgba(255,255,255,0.05)',
    _textPrimaryDark:   '#E2E8F0',
    _textSecondaryDark: '#94A3B8',
    _textTertiaryDark:  '#64748B',
    _borderDark:        'rgba(34,211,238,0.10)',
    _borderStrongDark:  'rgba(34,211,238,0.18)',
    // Glass card surface
    _surfaceSecondary: 'rgba(255,255,255,0.08)',
    _surfaceSecondaryDark: 'rgba(255,255,255,0.08)',
  }),

  galaxy: makeTheme({
    _name: 'Galaxy 紫夜',
    _desc: '深紫渐变 · 宇宙探索 · 高级暗色',
    _bgType: 'gradient',
    _bgGradient: { from: '#0F0722', to: '#1A0A2E', direction: 'diagonal' },
    _primary:    '#8B5CF6',
    _accent:     '#EC4899',
    _bg:         '#0D0618',
    _surface:    '#1A0F2E',
    _surfaceTertiary: '#2A1A44',
    _textPrimary:   '#F0E6FF',
    _textSecondary: '#B8A0D8',
    _textTertiary:  '#6B5090',
    _textInverse:   '#0D0618',
    _border:        'rgba(139,92,246,0.12)',
    _borderStrong:  'rgba(139,92,246,0.22)',
    _success:       '#A78BFA',
    _danger:        '#FB7185',
    _warning:       '#FBBF24',
    // Dark (Galaxy is dark-native)
    _primaryDark:   '#A78BFA',
    _accentDark:    '#F472B6',
    _bgDark:        '#0D0618',
    _surfaceDark:   '#1A0F2E',
    _surfaceTertiaryDark: '#2A1A44',
    _textPrimaryDark:   '#F0E6FF',
    _textSecondaryDark: '#B8A0D8',
    _textTertiaryDark:  '#6B5090',
    _borderDark:        'rgba(139,92,246,0.12)',
    _borderStrongDark:  'rgba(139,92,246,0.22)',
  }),

  mono: makeTheme({
    _name: 'Mono 极简黑白',
    _desc: '纯黑白灰 · 极致专注 · 零干扰',
    _primary:    '#000000',
    _accent:     '#6B7280',
    _bg:         '#FFFFFF',
    _surface:    '#FAFAFA',
    _surfaceTertiary: '#F3F3F3',
    _textPrimary:   '#000000',
    _textSecondary: '#4B4B4B',
    _textTertiary:  '#9CA3AF',
    _textInverse:   '#FFFFFF',
    _border:        'rgba(0,0,0,0.08)',
    _borderStrong:  'rgba(0,0,0,0.16)',
    _success:       '#6B7280',
    _danger:        '#374151',
    _warning:       '#4B5563',
    // Dark
    _primaryDark:   '#FFFFFF',
    _accentDark:    '#9CA3AF',
    _bgDark:        '#0A0A0A',
    _surfaceDark:   '#141414',
    _surfaceTertiaryDark: '#1F1F1F',
    _textPrimaryDark:   '#FAFAFA',
    _textSecondaryDark: '#A3A3A3',
    _textTertiaryDark:  '#525252',
    _borderDark:        'rgba(255,255,255,0.08)',
    _borderStrongDark:  'rgba(255,255,255,0.14)',
  }),
}

export const THEME_NAMES = Object.keys(THEMES)
export const DEFAULT_THEME = 'crystalline'

/** Generate a custom theme from user RGB values */
export function buildCustomTheme(config) {
  const p = (v) => (typeof v === 'number' ? `rgb(${v})` : v)
  const hexToRgbStr = (hex) => {
    const r = parseInt(hex.slice(1,3), 16)
    const g = parseInt(hex.slice(3,5), 16)
    const b = parseInt(hex.slice(5,7), 16)
    return `${r},${g},${b}`
  }

  const primary = config.primary || '#6366F1'
  const accent  = config.accent  || '#60A5FA'
  const bg      = config.bg      || '#FAFAF9'
  const surface = config.surface || '#FFFFFF'
  const text    = config.text    || '#1A1A1C'

  return makeTheme({
    _name: config.name || 'Custom',
    _desc: '自定义主题',
    _bgType: config.bgType || 'solid',
    _bgGradient: config.bgGradient || null,
    _particles: config.particles || null,
    _primary:    primary,
    _accent:     accent,
    _bg:         bg,
    _surface:    surface,
    _surfaceTertiary: `color-mix(in srgb, ${bg} 92%, ${text})`,
    _textPrimary:   text,
    _textSecondary: `color-mix(in srgb, ${text} 55%, ${bg})`,
    _textTertiary:  `color-mix(in srgb, ${text} 35%, ${bg})`,
    _textInverse:   bg,
    _border:        `color-mix(in srgb, ${text} 8%, transparent)`,
    _borderStrong:  `color-mix(in srgb, ${text} 15%, transparent)`,
    _primaryDark:   primary,
    _accentDark:    accent,
    _bgDark:        `color-mix(in srgb, ${bg} 5%, ${text})`,
    _surfaceDark:   `color-mix(in srgb, ${bg} 10%, ${text})`,
    _surfaceTertiaryDark: `color-mix(in srgb, ${bg} 16%, ${text})`,
    _textPrimaryDark:   bg,
    _textSecondaryDark: `color-mix(in srgb, ${bg} 65%, ${text})`,
    _textTertiaryDark:  `color-mix(in srgb, ${bg} 38%, ${text})`,
    _borderDark:        `color-mix(in srgb, ${bg} 10%, transparent)`,
    _borderStrongDark:  `color-mix(in srgb, ${bg} 16%, transparent)`,
  })
}
