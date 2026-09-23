import { useMemo } from 'react'

/**
 * Deep-space starfield — twinkling stars, pure CSS, GPU-composited.
 */
const MAX_STARS = 70

export default function StarlightParticles({
  count = 60,
  color = '#94A3B8',
  opacity = 0.7,
}) {
  const capped = Math.min(MAX_STARS, Math.max(1, count))

  const stars = useMemo(() =>
    Array.from({ length: capped }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: 1 + Math.random() * 2.5,
      delay: Math.random() * 5,
      duration: 2 + Math.random() * 4,
      driftX: (Math.random() - 0.5) * 40,
      driftY: (Math.random() - 0.5) * 40,
      maxOpacity: 0.3 + Math.random() * 0.6,
    })), [capped])

  if (count <= 0) return null

  return (
    <div aria-hidden="true" style={{
      position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
      overflow: 'hidden',
    }}>
      <style>{`
        @keyframes twinkle {
          0%, 100% { opacity: 0.15; }
          30%  { opacity: var(--max-op); }
          70%  { opacity: 0.3; }
        }
        @keyframes stardrift {
          0%   { transform: translate(0, 0); }
          100% { transform: translate(var(--dx), var(--dy)); }
        }
      `}</style>

      {/* Twinkling stars */}
      {stars.map((s) => (
        <div
          key={s.id}
          style={{
            position: 'absolute',
            left: `${s.left}%`, top: `${s.top}%`,
            width: s.size, height: s.size,
            borderRadius: '50%',
            backgroundColor: color,
            '--max-op': s.maxOpacity,
            '--dx': `${s.driftX}px`,
            '--dy': `${s.driftY}px`,
            animation: `twinkle ${s.duration}s ${s.delay}s ease-in-out infinite, stardrift ${s.duration + 3}s ${s.delay}s ease-in-out infinite alternate`,
          }}
        />
      ))}

    </div>
  )
}
