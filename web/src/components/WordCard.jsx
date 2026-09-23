import { useState, useRef, useEffect } from 'react'
import { Star, Sparkles, Loader2 } from 'lucide-react'
import AudioControl from './AudioControl'
import { api } from '../api'

function spawnParticles(x, y, count = 10) {
  const colors = ['#6366f1','#818cf8','#10b981','#f59e0b','#ef4444']
  for (let i = 0; i < count; i++) {
    const p = document.createElement('div')
    const angle = (Math.PI * 2 * i) / count
    const dist = 30 + Math.random() * 50
    p.style.cssText = `
      position:fixed; left:${x}px; top:${y}px; z-index:9999;
      width:${2 + Math.random() * 4}px; height:${2 + Math.random() * 4}px;
      border-radius:50%; pointer-events:none;
      background:${colors[i % colors.length]};
      transition:all ${0.5 + Math.random() * 0.4}s cubic-bezier(.16,1,.3,1);
      opacity:1;
    `
    document.body.appendChild(p)
    requestAnimationFrame(() => {
      p.style.transform = `translate(${Math.cos(angle) * dist}px,${Math.sin(angle) * dist}px) scale(0)`
      p.style.opacity = '0'
    })
    setTimeout(() => p.remove(), 1200)
  }
}

export default function WordCard({ word, showAnswer, onToggleAnswer, onToggleFavorite, onAskAI }) {
  const [rotateX, setRotateX] = useState(0)
  const [rotateY, setRotateY] = useState(0)
  const [glareX, setGlareX] = useState(50)
  const [glareY, setGlareY] = useState(50)
  const [isHovered, setIsHovered] = useState(false)
  const [ripple, setRipple] = useState(null)
  const cardRef = useRef(null)
  const rafRef = useRef(null)
  const pointerRef = useRef(null)

  // AI explanation state
  const [aiData, setAiData] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiError, setAiError] = useState(null)
  const [aiExpanded, setAiExpanded] = useState(false)
  const [aiConfigured, setAiConfigured] = useState(null) // null = unchecked
  const fetchedWordRef = useRef(null)

  // Reset AI state when word changes
  useEffect(() => {
    setAiData(null)
    setAiError(null)
    setAiExpanded(false)
    fetchedWordRef.current = null
  }, [word?.english])

  // Cancel any pending tilt animation frame on unmount
  useEffect(() => {
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }
  }, [])

  // Check AI config status when card flips to answer
  useEffect(() => {
    if (!showAnswer || aiConfigured !== null) return
    let cancelled = false
    api.getAIConfigStatus()
      .then(res => { if (!cancelled) setAiConfigured(res.configured) })
      .catch(() => { if (!cancelled) setAiConfigured(false) })
    return () => { cancelled = true }
  }, [showAnswer, aiConfigured])

  // Throttle the tilt to once per animation frame and avoid reading layout on
  // every mousemove event (which would otherwise trigger layout thrashing).
  const handleMouseMove = (e) => {
    pointerRef.current = { x: e.clientX, y: e.clientY }
    if (rafRef.current) return
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null
      const card = cardRef.current
      const p = pointerRef.current
      if (!card || !p) return
      const r = card.getBoundingClientRect()
      const x = (p.x - r.left) / r.width - 0.5
      const y = (p.y - r.top) / r.height - 0.5
      setIsHovered(true)
      setRotateX(-y * (showAnswer ? 4 : 10))
      setRotateY(x * (showAnswer ? 4 : 10))
      setGlareX(x * 50 + 50)
      setGlareY(y * 50 + 50)
    })
  }

  const handleMouseLeave = () => {
    pointerRef.current = null
    if (rafRef.current) { cancelAnimationFrame(rafRef.current); rafRef.current = null }
    setIsHovered(false)
    setRotateX(0); setRotateY(0)
    setGlareX(50); setGlareY(50)
  }

  const handleClick = (e) => {
    if (!showAnswer && word) {
      const r = cardRef.current.getBoundingClientRect()
      setRipple({ x: e.clientX - r.left, y: e.clientY - r.top })
      setTimeout(() => setRipple(null), 600)
      spawnParticles(e.clientX, e.clientY, 10)
      onToggleAnswer?.()
    }
  }

  const handleAIExplain = async (e) => {
    e.stopPropagation()
    if (!word || aiLoading) return

    // If already loaded for this word, just toggle
    if (fetchedWordRef.current === word.english && aiData) {
      setAiExpanded(prev => !prev)
      return
    }

    // Reset for new word
    setAiLoading(true)
    setAiError(null)
    setAiData(null)
    setAiExpanded(true)
    fetchedWordRef.current = word.english

    try {
      const result = await api.explainWordDetail(word.english)
      setAiData(result)
    } catch (err) {
      setAiError('AI解释暂时不可用')
      console.error('AI explain error:', err)
    } finally {
      setAiLoading(false)
    }
  }

  if (!word) return null

  return (
    <div style={{ perspective: '1200px' }} className="w-full">
      <div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        className="relative w-full rounded-[24px] flex flex-col cursor-pointer select-none overflow-hidden"
        style={{
          transform: `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${isHovered && !showAnswer ? 1.006 : 1})`,
          transformStyle: 'preserve-3d',
          padding: '1.5rem',
          transition: 'transform 0.5s cubic-bezier(0.22, 0.61, 0.36, 1), box-shadow 0.5s ease',
          backgroundColor: 'var(--surface-secondary)',
          border: '1px solid var(--border)',
          boxShadow: isHovered && !showAnswer
            ? '0 20px 50px rgba(0,0,0,0.07), 0 6px 16px rgba(0,0,0,0.03)'
            : '0 1px 3px rgba(0,0,0,0.03), 0 1px 2px rgba(0,0,0,0.02)',
        }}>
        {/* Glass glare */}
        <div
          className="absolute inset-0 pointer-events-none rounded-[24px]"
          style={{
            background: `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255,255,255,${showAnswer ? 0.03 : 0.10}) 0%, transparent 50%)`,
          }}
        />

        {/* Ripple */}
        {ripple && (
          <div
            className="absolute rounded-full pointer-events-none"
            style={{
              left: ripple.x - 50, top: ripple.y - 50,
              width: 100, height: 100,
              background: 'radial-gradient(circle, color-mix(in srgb, var(--accent) 15%, transparent) 0%, transparent 70%)',
              animation: 'soundWave 0.6s ease-out forwards',
            }}
          />
        )}

        {/* ══════════ HEADER ROW — flex, NO absolute positioning ══════════ */}
        <div className="flex items-center justify-between mb-4" style={{ position: 'relative', zIndex: 10 }}>
          {/* Left: level badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium"
            style={{ backgroundColor: 'var(--surface-tertiary)', color: 'var(--text-tertiary)' }}>
            <BookIcon />
            {word.proficiency > 0
              ? `Lv.${word.proficiency}`
              : (word.study_status === 'learning' ? '学习中' : 'New')}
          </div>

          {/* Right: favorite + audio buttons in a flex row — no overlap */}
          <div className="flex items-center gap-2">
            <AudioControl word={word.english} size="sm" />
            <button onClick={(e) => { e.stopPropagation(); onToggleFavorite?.() }}
              className="p-2 rounded-full transition-all duration-200 hover:scale-110"
              style={{
                backgroundColor: word.is_favorite ? 'rgba(245,158,11,0.15)' : 'var(--surface-tertiary)',
                color: word.is_favorite ? '#f59e0b' : 'var(--text-tertiary)',
              }}
              title="收藏">
              <Star size={15} fill={word.is_favorite ? 'currentColor' : 'none'} />
            </button>
          </div>
        </div>

        {/* ═════════════════ FRONT: Word reveal ═════════════════ */}
        {!showAnswer && (
          <div className="flex flex-col items-center justify-center flex-1" style={{ minHeight: 260 }}>
            <h1
              className="text-[3.25rem] md:text-7xl font-extrabold mb-5 tracking-tight"
              style={{
                color: 'var(--text-primary)',
                letterSpacing: '-0.04em',
                animation: 'scaleIn 0.35s cubic-bezier(0.22, 0.61, 0.36, 1) forwards',
              }}>
              {word.english}
            </h1>

            {word.phonetic && (
              <span className="text-sm font-medium mb-12 tracking-wide"
                style={{ color: 'var(--text-tertiary)' }}>
                {word.phonetic}
              </span>
            )}

            <p className="text-[13px] font-medium"
              style={{ color: 'var(--text-tertiary)', opacity: 0.6 }}>
              点击卡片查看释义
            </p>
          </div>
        )}

        {/* ═════════════════ BACK: Full definition ═════════════════ */}
        {showAnswer && (
          <div className="w-full" style={{ animation: 'scaleIn 0.3s cubic-bezier(0.22, 0.61, 0.36, 1) forwards' }}>
            {/* Word + phonetic header */}
            <div className="mb-3">
              <h2 className="text-[2rem] font-bold tracking-tight mb-0.5"
                style={{ color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
                {word.english}
              </h2>
              {word.phonetic && (
                <span className="text-[13px] font-medium tracking-wide" style={{ color: 'var(--text-tertiary)' }}>
                  {word.phonetic}
                </span>
              )}
            </div>

            <div className="w-10 h-[3px] rounded-full mb-4" style={{ backgroundColor: 'var(--accent)' }} />

            {/* Chinese meaning */}
            <p className="text-[1.35rem] font-semibold leading-relaxed mb-3" style={{ color: 'var(--text-primary)' }}>
              {word.chinese || '—'}
            </p>

            {/* Source context — where you first saw this word */}
            {(word.source_document || word.source_sentence) && (
              <div className="rounded-lg p-2.5 mb-3" style={{ backgroundColor: 'var(--surface-tertiary)' }}>
                {word.source_document && (
                  <p className="text-[11px] font-semibold" style={{ color: 'var(--text-tertiary)' }}>
                    来源：《{word.source_document}》
                  </p>
                )}
                {word.source_sentence && (
                  <p className="text-xs italic mt-0.5" style={{ color: 'var(--text-secondary)' }}>"{word.source_sentence}"</p>
                )}
              </div>
            )}

            {/* AI Explain button — only when configured */}
            {aiConfigured !== false && (
              <button
                onClick={handleAIExplain}
                disabled={aiLoading}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold
                           transition-all duration-300 mb-3"
                style={{
                  backgroundColor: aiExpanded ? 'var(--accent-subtle)' : 'var(--surface-tertiary)',
                  color: aiExpanded ? 'var(--accent)' : 'var(--text-tertiary)',
                  border: aiExpanded ? '1px solid color-mix(in srgb, var(--accent) 20%, transparent)' : '1px solid transparent',
                  cursor: aiLoading ? 'wait' : 'pointer',
                }}
                onMouseEnter={(e) => {
                  if (!aiExpanded) {
                    e.currentTarget.style.backgroundColor = 'var(--accent-subtle)'
                    e.currentTarget.style.color = 'var(--accent)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!aiExpanded) {
                    e.currentTarget.style.backgroundColor = 'var(--surface-tertiary)'
                    e.currentTarget.style.color = 'var(--text-tertiary)'
                  }
                }}
              >
                <Sparkles size={13} className={aiLoading ? 'animate-spin' : ''} />
                {aiLoading ? 'AI分析中...' : aiExpanded ? '收起详细释义' : '查看详细释义'}
              </button>
            )}

            {/* Proficiency bar */}
            <div className="flex items-center gap-3 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
              <span className="text-[11px] font-semibold uppercase tracking-wider"
                style={{ color: 'var(--text-tertiary)' }}>Mastery</span>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map(l => (
                  <div key={l}
                    className="rounded-full transition-all duration-500"
                    style={{
                      width: 18, height: 3,
                      backgroundColor: l <= (word.proficiency || 0) ? 'var(--accent)' : 'var(--border)',
                      borderRadius: 100,
                    }} />
                ))}
              </div>
            </div>

            {/* ═══ AI Explanation Card ═══ */}
            <div style={{
              maxHeight: aiExpanded ? '600px' : '0px',
              opacity: aiExpanded ? 1 : 0,
              overflow: 'hidden',
              transition: 'max-height 0.4s cubic-bezier(0.22, 0.61, 0.36, 1), opacity 0.35s ease, margin-top 0.3s ease',
              marginTop: aiExpanded ? '1rem' : '0',
            }}>
              {(aiLoading || aiData || aiError) && (
                <div className="rounded-xl p-4"
                  style={{
                    backgroundColor: 'var(--surface)',
                    border: '1px solid var(--border)',
                    animation: aiExpanded ? 'scaleIn 0.3s cubic-bezier(0.22, 0.61, 0.36, 1) forwards' : 'none',
                  }}>
                  {/* Loading state */}
                  {aiLoading && (
                    <div className="flex items-center gap-3 py-4 justify-center">
                      <Loader2 size={18} className="animate-spin" style={{ color: 'var(--text-tertiary)' }} />
                      <span className="text-sm" style={{ color: 'var(--text-tertiary)' }}>AI 正在分析...</span>
                    </div>
                  )}

                  {/* Error state */}
                  {aiError && !aiLoading && (
                    <div className="py-3 text-center">
                      <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>{aiError}</p>
                      <button
                        onClick={handleAIExplain}
                        className="mt-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                        style={{
                          backgroundColor: 'var(--surface-tertiary)',
                          color: 'var(--accent)',
                          border: '1px solid var(--border)',
                        }}
                      >
                        重新生成
                      </button>
                    </div>
                  )}

                  {/* AI Result */}
                  {aiData && !aiLoading && (
                    <div className="space-y-3">
                      {/* Header */}
                      <div className="flex items-center gap-1.5 mb-1">
                        <Sparkles size={12} style={{ color: 'var(--accent)' }} />
                        <span className="text-[10px] font-semibold uppercase tracking-widest"
                          style={{ color: 'var(--accent)' }}>
                          AI 详解
                        </span>
                        {aiData.cached && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded-full ml-auto"
                            style={{ backgroundColor: 'var(--surface-tertiary)', color: 'var(--text-tertiary)' }}>
                            缓存
                          </span>
                        )}
                      </div>

                      {/* 词性 */}
                      {aiData.pos && (
                        <div>
                          <span className="text-[10px] font-semibold uppercase tracking-wider"
                            style={{ color: 'var(--text-tertiary)' }}>词性</span>
                          <p className="text-sm font-medium mt-0.5" style={{ color: 'var(--text-primary)' }}>
                            {aiData.pos}
                          </p>
                        </div>
                      )}

                      {/* 核心释义 */}
                      {aiData.core_meaning && (
                        <div>
                          <span className="text-[10px] font-semibold uppercase tracking-wider"
                            style={{ color: 'var(--text-tertiary)' }}>核心释义</span>
                          <p className="text-sm font-semibold mt-0.5" style={{ color: 'var(--text-primary)' }}>
                            {aiData.core_meaning}
                          </p>
                        </div>
                      )}

                      {/* 简单理解 */}
                      {aiData.simple_understanding && (
                        <div>
                          <span className="text-[10px] font-semibold uppercase tracking-wider"
                            style={{ color: 'var(--text-tertiary)' }}>简单理解</span>
                          <p className="text-sm mt-0.5 leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                            {aiData.simple_understanding}
                          </p>
                        </div>
                      )}

                      {/* 例句 */}
                      {aiData.example_en && (
                        <div className="rounded-lg p-3"
                          style={{ backgroundColor: 'var(--surface-tertiary)' }}>
                          <span className="text-[10px] font-semibold uppercase tracking-wider"
                            style={{ color: 'var(--text-tertiary)' }}>例句</span>
                          <p className="text-sm italic mt-1 leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                            {aiData.example_en}
                          </p>
                          {aiData.example_cn && (
                            <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
                              {aiData.example_cn}
                            </p>
                          )}
                        </div>
                      )}

                      {/* 使用提示 */}
                      {aiData.usage_tip && (
                        <div className="flex items-start gap-1.5">
                          <span className="text-xs flex-shrink-0">💡</span>
                          <p className="text-xs leading-relaxed" style={{ color: 'var(--text-tertiary)' }}>
                            {aiData.usage_tip}
                          </p>
                        </div>
                      )}

                      {!aiData.ai_available && (
                        <div className="py-2 text-center">
                          <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                            {aiData.error || 'AI 暂时无法生成解释，请重试。'}
                          </p>
                          <button
                            onClick={handleAIExplain}
                            className="mt-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                            style={{
                              backgroundColor: 'var(--surface-tertiary)',
                              color: 'var(--accent)',
                              border: '1px solid var(--border)',
                            }}
                          >
                            重新生成
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function BookIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  )
}
