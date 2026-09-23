import { useState, useEffect, useRef, useMemo } from 'react'
import { playWhoosh, playChime, playTick } from '../useSound'

const QUOTES = [
  'Small steps, big progress.',
  'Keep going.',
  'Every word matters.',
  'One word at a time.',
  'Consistency is the key.',
  'You are building something great.',
  'Today is a good day to learn.',
  'Progress, not perfection.',
]

/** Floating particle data */
function createParticles(count) {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: 50 + (Math.random() - 0.5) * 60,
    y: 50 + (Math.random() - 0.5) * 60,
    size: 3 + Math.random() * 5,
    delay: Math.random() * 1.5,
    duration: 2 + Math.random() * 3,
    drift: (Math.random() - 0.5) * 120,
    color: ['#6366f1', '#818cf8', '#10b981', '#f59e0b', '#f87171'][i % 5],
  }))
}

/** Animated number counter */
function AnimatedNumber({ target, suffix = '', duration = 800 }) {
  const [value, setValue] = useState(0)
  const rafRef = useRef(null)
  const startRef = useRef(null)

  useEffect(() => {
    startRef.current = performance.now()
    const step = (now) => {
      const elapsed = now - startRef.current
      const progress = Math.min(1, elapsed / duration)
      // easeOutExpo
      const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress)
      setValue(Math.round(eased * target))
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(step)
      }
    }
    rafRef.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(rafRef.current)
  }, [target, duration])

  return (
    <span style={{ fontVariantNumeric: 'tabular-nums' }}>
      {value}{suffix}
    </span>
  )
}

export default function Celebration({
  wordsCount = 0,
  masteredToday = 0,
  streakDays = 0,
  onDismiss,
}) {
  const [phase, setPhase] = useState(0)
  const [exiting, setExiting] = useState(false)
  const quote = useMemo(() => QUOTES[Math.floor(Math.random() * QUOTES.length)], [])
  const particles = useMemo(() => createParticles(30), [])

  useEffect(() => {
    const t0 = setTimeout(() => { playWhoosh(); setPhase(1) }, 200)
    const t1 = setTimeout(() => { playChime(); setPhase(2) }, 700)
    const t2 = setTimeout(() => { setPhase(3) }, 1200)
    const t3 = setTimeout(() => { setPhase(4) }, 2000)
    return () => { clearTimeout(t0); clearTimeout(t1); clearTimeout(t2); clearTimeout(t3) }
  }, [])

  const handleDismiss = () => {
    setExiting(true)
    setTimeout(() => onDismiss?.(), 250)
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center select-none"
      style={{
        backgroundColor: `rgba(0,0,0,${phase >= 1 ? 0.55 : 0})`,
        backdropFilter: `blur(${phase >= 1 ? 12 : 0}px)`,
        WebkitBackdropFilter: `blur(${phase >= 1 ? 12 : 0}px)`,
        opacity: exiting ? 0 : undefined,
        transition: 'opacity 0.25s ease, background-color 0.6s cubic-bezier(0.16, 1, 0.3, 1), backdrop-filter 0.6s ease',
      }}
      onClick={phase >= 4 ? handleDismiss : undefined}
    >
      {/* Floating particles */}
      {particles.map((p) => (
        <div
          key={p.id}
          className="absolute rounded-full pointer-events-none"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            backgroundColor: p.color,
            opacity: phase >= 1 ? 0 : 0,
            animation: phase >= 1
              ? `celebrationParticle ${p.duration}s ${p.delay}s ease-out forwards`
              : 'none',
            '--drift': `${p.drift}px`,
          }}
        />
      ))}

      {/* Center content */}
      <div
        className="flex flex-col items-center gap-3"
        style={{
          opacity: exiting ? 0 : (phase >= 1 ? 1 : 0),
          transform: exiting ? 'scale(0.95) translateY(8px)' : (phase >= 1 ? 'scale(1)' : 'scale(0.85)'),
          transition: exiting
            ? 'opacity 0.2s ease, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1)'
            : 'opacity 0.5s ease, transform 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        {/* Checkmark circle */}
        <div className="relative flex items-center justify-center" style={{ width: 100, height: 100 }}>
          {/* Expanding rings */}
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="absolute rounded-full"
              style={{
                width: 100,
                height: 100,
                border: '1.5px solid var(--success)',
                opacity: phase >= 2 ? 0 : 0.3,
                animation: phase >= 1
                  ? `celebrationRing ${1.2 + i * 0.3}s ease-out forwards`
                  : 'none',
                animationDelay: `${i * 0.15}s`,
              }}
            />
          ))}

          {/* Checkmark SVG */}
          <svg
            width="50"
            height="50"
            viewBox="0 0 50 50"
            style={{
              opacity: phase >= 2 ? 1 : 0,
              transform: phase >= 2 ? 'scale(1)' : 'scale(0)',
              transition: 'opacity 0.3s ease, transform 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          >
            <circle
              cx="25" cy="25" r="23"
              fill="none"
              stroke="var(--success)"
              strokeWidth="2"
              strokeDasharray="145"
              strokeDashoffset={phase >= 2 ? 0 : 145}
              style={{ transition: 'stroke-dashoffset 0.5s ease 0.1s' }}
            />
            <path
              d="M14 25 L22 33 L36 17"
              fill="none"
              stroke="var(--success)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray="40"
              strokeDashoffset={phase >= 2 ? 0 : 40}
              style={{ transition: 'stroke-dashoffset 0.4s ease 0.3s' }}
            />
          </svg>
        </div>

        {/* Title */}
        <h2
          className="text-2xl font-bold tracking-tight"
          style={{
            color: '#fff',
            opacity: phase >= 2 ? 1 : 0,
            transform: phase >= 2 ? 'translateY(0)' : 'translateY(8px)',
            transition: 'all 0.5s ease 0.2s',
          }}
        >
          学习完成
        </h2>

        {/* Words count */}
        <div
          className="text-5xl font-extrabold tracking-tight"
          style={{
            color: '#fff',
            opacity: phase >= 3 ? 1 : 0,
            transform: phase >= 3 ? 'translateY(0)' : 'translateY(10px)',
            transition: 'all 0.4s ease',
          }}
        >
          +<AnimatedNumber target={wordsCount} />
        </div>

        {/* Stats row */}
        <div
          className="flex gap-6 mt-2"
          style={{
            opacity: phase >= 3 ? 1 : 0,
            transform: phase >= 3 ? 'translateY(0)' : 'translateY(8px)',
            transition: 'all 0.5s ease 0.1s',
          }}
        >
          <StatItem label="今日掌握" value={masteredToday} suffix=" 词" />
          <StatItem label="连续学习" value={streakDays} suffix=" 天" />
        </div>

        {/* Motivational quote */}
        <p
          className="text-sm font-medium mt-4"
          style={{
            color: 'rgba(255,255,255,0.5)',
            opacity: phase >= 4 ? 1 : 0,
            transform: phase >= 4 ? 'translateY(0)' : 'translateY(6px)',
            transition: 'all 0.6s ease',
            fontStyle: 'italic',
          }}
        >
          {quote}
        </p>

        {/* Continue button */}
        <button
          onClick={onDismiss}
          className="mt-8 px-8 py-2.5 rounded-full text-sm font-semibold transition-all duration-300 hover:scale-105 active:scale-95"
          style={{
            backgroundColor: 'rgba(255,255,255,0.15)',
            color: '#fff',
            opacity: phase >= 4 ? 1 : 0,
            transform: phase >= 4 ? 'translateY(0)' : 'translateY(8px)',
            transition: 'all 0.5s ease 0.2s',
          }}
        >
          继续学习
        </button>
      </div>

      {/* Inject keyframes once */}
      <style>{`
        @keyframes celebrationRing {
          0% { transform: scale(1); opacity: 0.3; }
          100% { transform: scale(3.5); opacity: 0; }
        }
        @keyframes celebrationParticle {
          0% { transform: translate(0, 0) scale(1); opacity: 0.8; }
          100% { transform: translate(var(--drift), calc(var(--drift) * -0.7)) scale(0); opacity: 0; }
        }
      `}</style>
    </div>
  )
}

function StatItem({ label, value, suffix = '' }) {
  return (
    <div className="text-center">
      <div className="text-xs font-medium" style={{ color: 'rgba(255,255,255,0.45)' }}>
        {label}
      </div>
      <div className="text-lg font-bold tracking-tight" style={{ color: '#fff' }}>
        <AnimatedNumber target={value} duration={600} />
        <span className="text-sm font-normal" style={{ color: 'rgba(255,255,255,0.5)' }}>
          {suffix}
        </span>
      </div>
    </div>
  )
}
