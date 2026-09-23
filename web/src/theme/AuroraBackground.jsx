import { useMemo } from 'react'

/**
 * Aurora Borealis — flowing light bands via CSS gradients + animations.
 *
 * 3 translucent light bands (cyan → purple → green) that drift slowly
 * across the viewport. Pure CSS, GPU-composited, zero JS animation.
 *
 * Performance: 3 absolutely-positioned divs with radial-gradient + blur.
 * Total GPU cost: ~3 layers. Fits within 60fps budget on low-end devices.
 */
export default function AuroraBackground() {
  const bands = useMemo(() => [
    { id: 0, color: '#22D3EE', top: '15%', left: '-20%', w: 600, h: 300,
      duration: '22s', delay: '0s', opacity: 0.22 },
    { id: 1, color: '#A78BFA', top: '45%', left: '30%', w: 500, h: 250,
      duration: '25s', delay: '-7s', opacity: 0.18 },
    { id: 2, color: '#34D399', top: '65%', left: '-10%', w: 550, h: 280,
      duration: '20s', delay: '-14s', opacity: 0.16 },
  ], [])

  return (
    <div aria-hidden="true" style={{
      position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
      overflow: 'hidden', backgroundColor: '#061826',
    }}>
      <style>{`
        @keyframes auroraDrift {
          0%   { transform: translate(0, 0) rotate(0deg) scale(1); }
          25%  { transform: translate(8vw, 3vh) rotate(3deg) scale(1.05); }
          50%  { transform: translate(-4vw, -2vh) rotate(-2deg) scale(0.95); }
          75%  { transform: translate(-6vw, 4vh) rotate(1deg) scale(1.02); }
          100% { transform: translate(0, 0) rotate(0deg) scale(1); }
        }
        @keyframes auroraPulse {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 1; }
        }
      `}</style>
      {bands.map((b) => (
        <div
          key={b.id}
          style={{
            position: 'absolute',
            top: b.top, left: b.left,
            width: b.w, height: b.h,
            borderRadius: '50%',
            background: `radial-gradient(ellipse at center, ${b.color} 0%, transparent 70%)`,
            opacity: b.opacity,
            filter: 'blur(60px)',
            transform: 'translateZ(0)',
            backfaceVisibility: 'hidden',
            animation: `auroraDrift ${b.duration} ${b.delay} ease-in-out infinite, auroraPulse ${parseInt(b.duration) * 0.6}s ${b.delay} ease-in-out infinite`,
          }}
        />
      ))}
    </div>
  )
}
