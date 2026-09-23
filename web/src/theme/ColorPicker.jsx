import { useRef, useCallback } from 'react'
import { hexToHsl, hslToHex } from './themeUtils'

/**
 * ColorPicker — a visual HSV picker (no RGB sliders).
 *
 * Top: 2-D saturation/lightness area (x = saturation, y = lightness) for the
 * current hue. Bottom: a hue slider. Both support click and drag via pointer
 * events, so the user sees colors and picks them directly.
 */
export default function ColorPicker({ value, onChange }) {
  const svRef = useRef(null)
  const hueRef = useRef(null)
  const dragging = useRef(null) // 'sv' | 'hue' | null

  const { h, s, l } = hexToHsl(value)

  const updateSv = useCallback((clientX, clientY) => {
    const el = svRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const sat = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
    const light = 1 - Math.max(0, Math.min(1, (clientY - rect.top) / rect.height))
    onChange(hslToHex(h, sat, light))
  }, [h, onChange])

  const updateHue = useCallback((clientX) => {
    const el = hueRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const x = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
    onChange(hslToHex(x * 360, s, l))
  }, [s, l, onChange])

  const onSvPointerDown = (e) => {
    dragging.current = 'sv'
    e.currentTarget.setPointerCapture?.(e.pointerId)
    updateSv(e.clientX, e.clientY)
  }
  const onHuePointerDown = (e) => {
    dragging.current = 'hue'
    e.currentTarget.setPointerCapture?.(e.pointerId)
    updateHue(e.clientX)
  }
  const onPointerMove = (e) => {
    if (dragging.current === 'sv') updateSv(e.clientX, e.clientY)
    else if (dragging.current === 'hue') updateHue(e.clientX)
  }
  const onPointerUp = () => { dragging.current = null }

  const svBackground = {
    background: `linear-gradient(to top, #000, rgba(0,0,0,0)), linear-gradient(to right, #fff, hsl(${h},100%,50%))`,
  }
  const thumbX = `${s * 100}%`
  const thumbY = `${(1 - l) * 100}%`
  const hueX = `${(h / 360) * 100}%`

  return (
    <div
      style={{ touchAction: 'none', userSelect: 'none' }}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
    >
      {/* SV area */}
      <div
        ref={svRef}
        onPointerDown={onSvPointerDown}
        style={{
          ...svBackground,
          position: 'relative', height: 160, borderRadius: 'var(--radius-md)',
          cursor: 'crosshair', border: '1px solid var(--border)',
        }}
      >
        <div style={{
          position: 'absolute', left: thumbX, top: thumbY,
          width: 18, height: 18, borderRadius: '50%',
          backgroundColor: value, border: '2px solid #fff',
          boxShadow: '0 0 0 1px rgba(0,0,0,0.25)',
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none',
        }} />
      </div>

      {/* Hue slider */}
      <div
        ref={hueRef}
        onPointerDown={onHuePointerDown}
        style={{
          position: 'relative', height: 14, marginTop: '0.75rem',
          borderRadius: '100px', cursor: 'pointer',
          background: 'linear-gradient(to right, #f00 0%, #ff0 17%, #0f0 33%, #0ff 50%, #00f 67%, #f0f 83%, #f00 100%)',
          border: '1px solid var(--border)',
        }}
      >
        <div style={{
          position: 'absolute', left: hueX, top: '50%',
          width: 18, height: 18, borderRadius: '50%',
          backgroundColor: hslToHex(h, 1, 0.5), border: '2px solid #fff',
          boxShadow: '0 0 0 1px rgba(0,0,0,0.25)',
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none',
        }} />
      </div>
    </div>
  )
}
