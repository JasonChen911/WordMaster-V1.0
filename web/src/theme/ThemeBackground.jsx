import { useMemo } from 'react'
import { useTheme } from './ThemeContext'
import StarlightParticles from './StarlightParticles'
import AuroraBackground from './AuroraBackground'

/**
 * Theme-specific immersive backgrounds:
 * - aurora  → flowing light bands (AuroraBackground)
 * - starlight → starfield + shooting star (StarlightParticles)
 * - custom particles → user-configured stars
 * - gradient → CSS gradient overlay
 */
export default function ThemeBackground() {
  const { themeName, themeDef, customTheme } = useTheme()

  const bgType = themeDef.backgroundType
  const gradient = themeDef.backgroundGradient
  const particles = themeDef.particles

  const gradientCSS = useMemo(() => {
    if (bgType !== 'gradient' || !gradient) return null
    const deg = gradient.direction === 'horizontal' ? '90deg'
      : gradient.direction === 'vertical' ? '180deg'
      : '135deg'
    return `linear-gradient(${deg}, ${gradient.from}, ${gradient.to})`
  }, [bgType, gradient])

  // ── Aurora: immersive flowing light bands ──
  if (themeName === 'aurora') {
    return <AuroraBackground />
  }

  // ── Starlight: deep-space starfield ──
  if (themeName === 'starlight') {
    return (
      <StarlightParticles count={60} color="#94A3B8" opacity={0.7} />
    )
  }

  return (
    <>
      {/* Gradient overlay for aurora/galaxy/mono themes */}
      {gradientCSS && (
        <div
          aria-hidden="true"
          style={{
            position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
            background: gradientCSS,
            opacity: 0.35,
          }}
        />
      )}

      {/* Custom particle backgrounds */}
      {bgType === 'particles' && particles && themeName !== 'starlight' && (
        <StarlightParticles
          count={particles.count}
          color={particles.color}
          opacity={particles.opacity}
        />
      )}
    </>
  )
}
