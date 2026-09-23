/**
 * themeUtils — color math for the theme system.
 *
 * Pure functions, no React. Handles HEX ↔ RGB ↔ HSL conversion, luminance /
 * contrast, and color derivation so the UI can be "see the color, then pick it"
 * instead of hand-editing RGB numbers.
 */

// ── HEX ↔ RGB ───────────────────────────────────────────────────

export function normalizeHex(hex) {
  if (typeof hex !== 'string') return null
  let h = hex.trim().replace('#', '')
  if (h.length === 3) h = h.split('').map((c) => c + c).join('')
  if (!/^[0-9a-fA-F]{6}$/.test(h)) return null
  return '#' + h.toLowerCase()
}

export function hexToRgb(hex) {
  const h = normalizeHex(hex)
  if (!h) return null
  const n = parseInt(h.slice(1), 16)
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 }
}

export function rgbToHex(r, g, b) {
  const c = (v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')
  return '#' + c(r) + c(g) + c(b)
}

/** Accept a hex string or a `{r,g,b}`-style object; return a hex or null. */
export function toHex(color) {
  if (typeof color === 'string') return normalizeHex(color)
  if (color && typeof color === 'object') {
    const r = color.r ?? color[0]
    const g = color.g ?? color[1]
    const b = color.b ?? color[2]
    if ([r, g, b].every((v) => typeof v === 'number' && !isNaN(v))) return rgbToHex(r, g, b)
  }
  return null
}

// ── HSL ─────────────────────────────────────────────────────────

export function hexToHsl(hex) {
  const rgb = hexToRgb(hex)
  if (!rgb) return { h: 0, s: 0, l: 0 }
  const r = rgb.r / 255
  const g = rgb.g / 255
  const b = rgb.b / 255
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h = 0
  let s = 0
  const l = (max + min) / 2
  if (max !== min) {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break
      case g: h = (b - r) / d + 2; break
      default: h = (r - g) / d + 4
    }
    h *= 60
  }
  return { h, s, l }
}

export function hslToHex(h, s, l) {
  const hue = ((h % 360) + 360) % 360
  const c = (1 - Math.abs(2 * l - 1)) * s
  const x = c * (1 - Math.abs(((hue / 60) % 2) - 1))
  const m = l - c / 2
  let r = 0, g = 0, b = 0
  if (hue < 60) { r = c; g = x; b = 0 }
  else if (hue < 120) { r = x; g = c; b = 0 }
  else if (hue < 180) { r = 0; g = c; b = x }
  else if (hue < 240) { r = 0; g = x; b = c }
  else if (hue < 300) { r = x; g = 0; b = c }
  else { r = c; g = 0; b = x }
  return rgbToHex((r + m) * 255, (g + m) * 255, (b + m) * 255)
}

// ── Luminance / contrast ────────────────────────────────────────

export function relativeLuminance(hex) {
  const rgb = hexToRgb(hex)
  if (!rgb) return 0
  const [r, g, b] = [rgb.r, rgb.g, rgb.b].map((v) => {
    const s = v / 255
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4)
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

export function contrastRatio(a, b) {
  const la = relativeLuminance(a)
  const lb = relativeLuminance(b)
  const hi = Math.max(la, lb)
  const lo = Math.min(la, lb)
  return (hi + 0.05) / (lo + 0.05)
}

/** Pick a readable text color (near-black or white) to sit on `hex`.
 *  Threshold ~0.179 keeps white text ≥4.5:1 on dark colors and dark text on
 *  light colors. */
export function textColorOn(hex) {
  return relativeLuminance(hex) > 0.179 ? '#1A1A1C' : '#FFFFFF'
}

// ── Mixing / derivation ─────────────────────────────────────────

export function mix(a, b, weight) {
  const ca = hexToRgb(a)
  const cb = hexToRgb(b)
  if (!ca || !cb) return a
  const w = Math.max(0, Math.min(1, weight))
  return rgbToHex(
    ca.r + (cb.r - ca.r) * w,
    ca.g + (cb.g - ca.g) * w,
    ca.b + (cb.b - ca.b) * w,
  )
}

export function lighten(hex, amt) { return mix(hex, '#ffffff', amt) }
export function darken(hex, amt) { return mix(hex, '#000000', amt) }

/** A slightly darker accent that still reads as the same family as `primary`. */
export function deriveAccent(primary) { return darken(primary, 0.10) }
