import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { THEMES, THEME_NAMES, DEFAULT_THEME, buildCustomTheme, buildThemeFromPrimary } from './themeConfig'

const CTX = createContext()

const STORAGE_KEY_MODE   = 'wordmaster-theme-mode'
const STORAGE_KEY_NAME   = 'wordmaster-theme-name'
const STORAGE_KEY_CUSTOM = 'wordmaster-theme-custom'

/** Apply a CSS variable map to :root */
function applyVars(vars) {
  const root = document.documentElement
  Object.entries(vars).forEach(([key, val]) => {
    if (val != null) root.style.setProperty(key, val)
  })
}

function loadPersisted() {
  try {
    return {
      mode:   localStorage.getItem(STORAGE_KEY_MODE)   || 'light',
      name:   localStorage.getItem(STORAGE_KEY_NAME)   || DEFAULT_THEME,
      custom: JSON.parse(localStorage.getItem(STORAGE_KEY_CUSTOM) || 'null'),
    }
  } catch { return { mode: 'light', name: DEFAULT_THEME, custom: null } }
}

function persist(mode, name, custom) {
  localStorage.setItem(STORAGE_KEY_MODE, mode)
  localStorage.setItem(STORAGE_KEY_NAME, name)
  if (custom) localStorage.setItem(STORAGE_KEY_CUSTOM, JSON.stringify(custom))
  else localStorage.removeItem(STORAGE_KEY_CUSTOM)
}

/**
 * Resolve a persisted custom config to a theme object, keeping backward
 * compatibility: the new simplified config is a single `{ primary }`; the
 * legacy config carried `accent/bg/surface/text` (and an RGB-less hex).
 */
function resolveCustomTheme(custom) {
  if (!custom) return buildThemeFromPrimary(undefined)
  if (custom.primary && !custom.accent && !custom.bg && !custom.surface && !custom.text) {
    return buildThemeFromPrimary(custom.primary, custom.name)
  }
  return buildCustomTheme(custom)
}

export function ThemeProvider({ children }) {
  const [state, setState] = useState(loadPersisted)

  // Resolve active theme object
  const themeDef = state.name === 'custom' && state.custom
    ? resolveCustomTheme(state.custom)
    : THEMES[state.name] || THEMES[DEFAULT_THEME]

  const mode = state.mode
  const isDark = mode === 'dark'

  // Apply CSS variables whenever theme or mode changes
  useEffect(() => {
    const vars = isDark ? themeDef.dark : themeDef.light
    const root = document.documentElement

    // Disable transitions during initial load to prevent flash
    if (!root.classList.contains('theme-ready')) {
      root.style.setProperty('--theme-transition', 'none')
    }

    applyVars(vars)

    // Dark class for Tailwind
    if (isDark) root.classList.add('dark')
    else root.classList.remove('dark')

    // Re-enable smooth transitions after first paint
    if (!root.classList.contains('theme-ready')) {
      root.classList.add('theme-ready')
      requestAnimationFrame(() => {
        root.style.setProperty('--theme-transition',
          'background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease')
      })
    }
  }, [state.name, state.mode, state.custom])

  // Persist
  useEffect(() => {
    persist(state.mode, state.name, state.custom)
  }, [state.mode, state.name, state.custom])

  // ── Actions ──
  const setMode = useCallback((m) => setState(s => ({ ...s, mode: m })), [])
  const toggleMode = useCallback(() => setState(s => ({ ...s, mode: s.mode === 'dark' ? 'light' : 'dark' })), [])
  const setTheme = useCallback((name) => setState(s => ({ ...s, name, custom: name === 'custom' ? s.custom : null })), [])
  const setCustomTheme = useCallback((config) => setState(s => ({ ...s, name: 'custom', custom: config })), [])

  return (
    <CTX.Provider value={{
      mode, isDark, toggleMode, setMode,
      themeName: state.name, setTheme,
      customTheme: state.custom, setCustomTheme,
      themeDef,
      themes: THEMES,
      themeNames: THEME_NAMES,
    }}>
      {children}
    </CTX.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(CTX)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
