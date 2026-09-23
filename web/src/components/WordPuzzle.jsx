import { useState, useEffect, useRef, useCallback } from 'react'
import { ArrowLeft, ArrowRight, CheckCircle2, RefreshCw, Sparkles, AlertCircle, BookOpen } from 'lucide-react'
import { api } from '../api'

// ═══════════════════════════════════════════════════════════════
// Web Audio — gentle two-tone success chime (C5→E5, fast fade)
// ═══════════════════════════════════════════════════════════════
let audioCtx = null
function getAudioContext() {
  if (!audioCtx) {
    try { audioCtx = new (window.AudioContext || window.webkitAudioContext)() } catch (_) { /* no audio */ }
  }
  return audioCtx
}

function playSuccessSound(volume = 0.18) {
  const ctx = getAudioContext()
  if (!ctx) return
  // Resume if suspended (browser autoplay policy)
  if (ctx.state === 'suspended') ctx.resume()

  const now = ctx.currentTime

  // Tone 1: C5 (523 Hz)
  const osc1 = ctx.createOscillator()
  const gain1 = ctx.createGain()
  osc1.type = 'sine'
  osc1.frequency.value = 523
  gain1.gain.setValueAtTime(volume, now)
  gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.35)
  osc1.connect(gain1).connect(ctx.destination)
  osc1.start(now)
  osc1.stop(now + 0.35)

  // Tone 2: E5 (659 Hz) — slightly delayed
  const osc2 = ctx.createOscillator()
  const gain2 = ctx.createGain()
  osc2.type = 'sine'
  osc2.frequency.value = 659
  gain2.gain.setValueAtTime(0, now)
  gain2.gain.linearRampToValueAtTime(volume, now + 0.08)
  gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.45)
  osc2.connect(gain2).connect(ctx.destination)
  osc2.start(now + 0.06)
  osc2.stop(now + 0.45)
}

// ═══════════════════════════════════════════════════════════════
// Particle spawn on correct answer
// ═══════════════════════════════════════════════════════════════
function spawnSuccessParticles(x, y, count = 8) {
  const colors = ['#10b981', '#34d399', '#818cf8', '#6366f1', '#a78bfa']
  for (let i = 0; i < count; i++) {
    const p = document.createElement('div')
    const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.5
    const dist = 25 + Math.random() * 45
    p.style.cssText = `
      position:fixed; left:${x}px; top:${y}px; z-index:9999;
      width:${3 + Math.random() * 4}px; height:${3 + Math.random() * 4}px;
      border-radius:50%; pointer-events:none;
      background:${colors[i % colors.length]};
      transition:all ${0.45 + Math.random() * 0.3}s cubic-bezier(.16,1,.3,1);
      opacity:1;
    `
    document.body.appendChild(p)
    requestAnimationFrame(() => {
      p.style.transform = `translate(${Math.cos(angle) * dist}px,${Math.sin(angle) * dist - 8}px) scale(0)`
      p.style.opacity = '0'
    })
    setTimeout(() => p.remove(), 1000)
  }
}

// ═══════════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════════
function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function pickWords(words) {
  return words.filter(w => {
    const unique = new Set(w.english.toLowerCase().replace(/[^a-z]/g, ''))
    return unique.size >= 3 && w.english.length >= 3 && w.english.length <= 12
  })
}

// ═══════════════════════════════════════════════════════════════
// WordPuzzle Component
// ═══════════════════════════════════════════════════════════════
export default function WordPuzzle({ onBack }) {
  const [words, setWords] = useState([])
  const [index, setIndex] = useState(0)
  const [letters, setLetters] = useState([])
  const [placed, setPlaced] = useState([])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [score, setScore] = useState(0)
  const [total, setTotal] = useState(0)
  const [completed, setCompleted] = useState(false)

  // Active book (unified with Study + FillBlank)
  const [activeBook, setActiveBook] = useState(null)

  // Animation states
  const [pressingTile, setPressingTile] = useState(null)
  const [newPlacedIdx, setNewPlacedIdx] = useState(null)
  const [answerGlow, setAnswerGlow] = useState(false)
  const [answerShake, setAnswerShake] = useState(false)
  const [scoreBounce, setScoreBounce] = useState(false)

  const dragItem = useRef(null)
  const dragOverItem = useRef(null)
  const answerRef = useRef(null)
  const nextAnimTimer = useRef(null)

  // ── Cleanup timers ──
  useEffect(() => {
    return () => { if (nextAnimTimer.current) clearTimeout(nextAnimTimer.current) }
  }, [])

  // ── Init: get active book (same pattern as FillBlank + Study), then load words ──
  useEffect(() => {
    let cancelled = false
    async function init() {
      try {
        const resp = await api.getActiveBook()
        if (cancelled) return
        const book = resp.book
        setActiveBook(book)
        if (book) {
          const data = await api.getGamesWords(30, book.id)
          if (cancelled) return
          const valid = pickWords(data.words || [])
          if (valid.length > 0) {
            setWords(valid)
            initRound(valid, 0)
          }
        }
        setLoading(false)
      } catch (err) {
        if (!cancelled) {
          setError('无法加载游戏数据，请检查词书配置。')
          setLoading(false)
        }
      }
    }
    init()
    return () => { cancelled = true }
  }, [])

  const initRound = useCallback((wordList, idx) => {
    if (idx >= wordList.length) {
      setCompleted(true)
      return
    }
    const word = wordList[idx]
    const chars = word.english.toLowerCase().replace(/[^a-z]/g, '').split('')
    let shuffled
    do { shuffled = shuffle(chars) } while (shuffled.join('') === chars.join('') && chars.length > 2)
    setLetters(shuffled)
    setPlaced([])
    setResult(null)
    setNewPlacedIdx(null)
    setAnswerGlow(false)
    setAnswerShake(false)
  }, [])

  // ── Current word ──
  const current = words[index]
  const placedWord = placed.map(i => letters[i]).join('')

  // ── Drag handlers ──
  const handleDragStart = (i) => { dragItem.current = i }
  const handleDragEnter = (i) => { dragOverItem.current = i }
  const handleDragEnd = () => {
    const from = dragItem.current
    const to = dragOverItem.current
    if (from === null || to === null || from === to) {
      dragItem.current = null; dragOverItem.current = null; return
    }
    const newLetters = [...letters]
    ;[newLetters[from], newLetters[to]] = [newLetters[to], newLetters[from]]
    setLetters(newLetters)
    setPlaced(prev => prev.map(p => p === from ? to : p === to ? from : p))
    dragItem.current = null; dragOverItem.current = null
  }

  // ── Letter click with animation ──
  const handleLetterClick = (i) => {
    // Visual press feedback
    setPressingTile(i)
    setTimeout(() => setPressingTile(null), 180)

    if (placed.includes(i)) {
      setPlaced(prev => prev.filter(p => p !== i))
      setNewPlacedIdx(null)
    } else {
      setPlaced(prev => [...prev, i])
      setNewPlacedIdx(i) // trigger pop-in on this letter
      setTimeout(() => setNewPlacedIdx(null), 400)
    }
  }

  // ── Check answer ──
  const handleCheck = () => {
    const answer = placedWord.toLowerCase()
    const target = current.english.toLowerCase().replace(/[^a-z]/g, '')
    setTotal(prev => prev + 1)

    if (answer === target) {
      setResult('correct')
      setScore(prev => prev + 1)
      setAnswerGlow(true)
      setScoreBounce(true)
      setTimeout(() => setScoreBounce(false), 400)

      // Sound + particles
      playSuccessSound()
      if (answerRef.current) {
        const r = answerRef.current.getBoundingClientRect()
        spawnSuccessParticles(r.left + r.width / 2, r.top + r.height / 2, 10)
      }
    } else {
      setResult('wrong')
      setAnswerShake(true)
      setTimeout(() => setAnswerShake(false), 450)
      // Record the wrong spelling into the mistake book (source = game).
      api.recordMistake(current.english, 'game', 'spelling').catch(() => {})
    }
  }

  // ── Next word ──
  const handleNext = () => {
    if (nextAnimTimer.current) clearTimeout(nextAnimTimer.current)
    const nextIdx = index + 1
    setIndex(nextIdx)
    initRound(words, nextIdx)
  }

  const handleReshuffle = () => {
    const chars = current.english.toLowerCase().replace(/[^a-z]/g, '').split('')
    let newLetters
    do { newLetters = shuffle(chars) } while (newLetters.join('') === chars.join('') && chars.length > 2)
    setLetters(newLetters)
    setPlaced([])
    setResult(null)
    setNewPlacedIdx(null)
  }

  // ═══════════════════════════════════════
  // Loading
  // ═══════════════════════════════════════
  if (loading) {
    return (
      <div className="page flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 rounded-full border-[2.5px] animate-spin"
            style={{ borderColor: 'var(--border)', borderTopColor: 'var(--accent)' }} />
          <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
            {activeBook ? `加载「${activeBook.book_name}」单词...` : '加载游戏数据...'}
          </p>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════
  // Error
  // ═══════════════════════════════════════
  if (error) {
    return (
      <div className="page flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ backgroundColor: 'var(--danger-subtle)' }}>
            <AlertCircle size={28} style={{ color: 'var(--danger)' }} />
          </div>
          <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>{error}</p>
          <button onClick={onBack} className="ios-button ios-button-secondary" style={{ borderRadius: 'var(--radius-md)' }}>
            <ArrowLeft size={15} /> 返回
          </button>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════
  // No active book
  // ═══════════════════════════════════════
  if (!activeBook) {
    return (
      <div className="page flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-5"
            style={{ backgroundColor: 'var(--accent-subtle)' }}>
            <BookOpen size={32} style={{ color: 'var(--accent)' }} />
          </div>
          <h3 className="text-base font-bold mb-2" style={{ color: 'var(--text-primary)' }}>未选择词书</h3>
          <p className="text-sm mb-2" style={{ color: 'var(--text-secondary)' }}>
            请先在首页「词书管理」中选择当前学习词书。
          </p>
          <p className="text-xs mb-6" style={{ color: 'var(--text-tertiary)' }}>
            背单词、复习、小游戏均使用统一词书。
          </p>
          <button onClick={onBack}
            className="ios-button ios-button-secondary" style={{ borderRadius: 'var(--radius-md)' }}>
            <ArrowLeft size={15} /> 返回
          </button>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════
  // Empty (no suitable words in book)
  // ═══════════════════════════════════════
  if (words.length === 0) {
    return (
      <div className="page flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <p className="text-sm mb-2" style={{ color: 'var(--text-secondary)' }}>
            「{activeBook.book_name}」中没有适合字母拼词的单词。
          </p>
          <p className="text-xs mb-4" style={{ color: 'var(--text-tertiary)' }}>
            请选择单词数量较多的词书，或切换到挖空填词游戏。
          </p>
          <button onClick={onBack} className="ios-button ios-button-secondary" style={{ borderRadius: 'var(--radius-md)' }}>
            <ArrowLeft size={15} /> 返回
          </button>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════
  // Completed
  // ═══════════════════════════════════════
  if (completed) {
    return (
      <div className="page">
        <div className="text-center py-16">
          <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-5"
            style={{ backgroundColor: 'var(--accent-subtle)' }}>
            <Sparkles size={36} style={{ color: 'var(--accent)' }} />
          </div>
          <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>游戏完成！</h2>
          <p className="text-sm mb-8" style={{ color: 'var(--text-secondary)' }}>
            正确 {score} / {total}（{total > 0 ? Math.round((score / total) * 100) : 0}%）
          </p>
          <div className="flex gap-3 justify-center">
            <button onClick={onBack} className="ios-button ios-button-secondary" style={{ borderRadius: 'var(--radius-md)' }}>
              <ArrowLeft size={15} /> 返回游戏列表
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════
  // Counter badge
  // ═══════════════════════════════════════
  const counterBadge = (
    <div className={`flex items-center gap-1.5 ${scoreBounce ? 'score-bounce' : ''}`}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)"
        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
        style={{ transition: 'transform 0.2s ease' }}>
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      </svg>
      <span className="text-xs font-bold tracking-tight" style={{
        color: 'var(--accent)',
        fontVariantNumeric: 'tabular-nums',
        minWidth: '1.2em', textAlign: 'center',
      }}>
        {score}
      </span>
    </div>
  )

  return (
    <div className="page" style={{ paddingTop: '0.5rem' }}>
      {/* ═══ Top Bar ═══ */}
      <div className="flex items-center justify-between mb-6">
        <button onClick={onBack} className="ios-icon-button" aria-label="Back">
          <ArrowLeft size={19} />
        </button>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-3 py-1 rounded-full"
            style={{ backgroundColor: 'var(--accent-subtle)', color: 'var(--accent)' }}>
            字母拼词
          </span>
          {activeBook && (
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'var(--surface-tertiary)', color: 'var(--text-tertiary)' }}>
              {activeBook.book_name}
            </span>
          )}
          <span className="text-xs font-medium" style={{ color: 'var(--text-tertiary)' }}>
            {index + 1}/{words.length}
          </span>
        </div>
        {counterBadge}
      </div>

      {/* ═══ Chinese Hint ═══ */}
      <div className="text-center mb-6">
        <p className="text-xs font-semibold uppercase tracking-wider mb-1"
          style={{ color: 'var(--text-tertiary)' }}>中文提示</p>
        <h2 className="text-2xl font-bold tracking-tight"
          style={{ color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
          {current.chinese}
        </h2>
        {current.phonetic && (
          <p className="text-sm mt-1" style={{ color: 'var(--text-tertiary)' }}>{current.phonetic}</p>
        )}
      </div>

      {/* ═══ Word Display: full word on correct, letter tiles otherwise ═══ */}
      <div className="flex justify-center mb-6" ref={answerRef}>
        {result === 'correct' ? (
          <div className="text-center animate-scale-in" style={{ width: '100%' }}>
            <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--success)' }}>
              正确单词
            </p>
            <span style={{
              display: 'inline-block', padding: '0.5rem 1.5rem',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--success-subtle)', border: '1.5px solid var(--success)',
              fontSize: '2.5rem', fontWeight: 800, letterSpacing: '0.02em',
              color: 'var(--text-primary)',
              animation: 'scaleIn 0.35s cubic-bezier(0.22, 0.61, 0.36, 1) forwards',
            }}>
              {current.english}
            </span>
          </div>
        ) : (
          <div
            className={`flex gap-1.5 flex-wrap justify-center min-h-[3rem] px-4 py-3 rounded-xl transition-all duration-300
              ${answerGlow ? 'correct-glow' : ''}
              ${answerShake ? 'shake' : ''}`}
            style={{
              backgroundColor: result === 'wrong' ? 'var(--danger-subtle)' : 'var(--surface-tertiary)',
              border: `1.5px solid ${result === 'wrong' ? 'var(--danger)' : 'var(--border)'}`,
              transform: 'scale(1)',
              transition: 'transform 0.3s cubic-bezier(0.22, 0.61, 0.36, 1), background-color 0.3s ease, border-color 0.3s ease',
            }}>
            {placed.length === 0 ? (
              <span className="text-sm" style={{ color: 'var(--text-tertiary)', opacity: 0.5 }}>
                点击下方字母排列
              </span>
            ) : (
              placed.map((letterIdx, i) => (
                <span key={i}
                  className={`inline-flex items-center justify-center w-9 h-9 rounded-lg text-base font-extrabold uppercase tracking-wider cursor-pointer select-none
                    ${newPlacedIdx === letterIdx ? 'letter-pop' : ''}`}
                  style={{
                    backgroundColor: result === 'wrong' ? 'var(--danger-subtle)' : 'var(--surface-secondary)',
                    color: result === 'wrong' ? 'var(--danger)' : 'var(--text-primary)',
                    border: `1.5px solid ${result === 'wrong' ? 'var(--danger)' : 'var(--border)'}`,
                    transition: 'transform 0.2s cubic-bezier(0.22, 0.61, 0.36, 1), background-color 0.2s ease, border-color 0.2s ease',
                  }}
                  onClick={() => handleLetterClick(letterIdx)}>
                  {letters[letterIdx]}
                </span>
              ))
            )}
          </div>
        )}
      </div>

      {/* ═══ Result Feedback ═══ */}
      {result && (
        <div className="text-center mb-5 animate-scale-in">
          {result === 'correct' ? (
            <div className="flex items-center justify-center gap-2 text-sm font-bold"
              style={{ color: 'var(--success)' }}>
              <CheckCircle2 size={18} /> Correct!
            </div>
          ) : (
            <div className="space-y-1">
              <p className="text-sm font-semibold" style={{ color: 'var(--danger)' }}>
                不对哦，正确答案是：
              </p>
              <p className="text-base font-bold tracking-wide" style={{ color: 'var(--accent)' }}>
                {current.english}
              </p>
            </div>
          )}
        </div>
      )}

      {/* ═══ Letter Tiles (hidden once the word is solved) ═══ */}
      {result === 'correct' ? null : (
      <div className="flex flex-wrap justify-center gap-2 mb-6">
        {letters.map((letter, i) => {
          const isPlaced = placed.includes(i)
          return (
            <div
              key={i}
              draggable
              onDragStart={() => handleDragStart(i)}
              onDragEnter={() => handleDragEnter(i)}
              onDragEnd={handleDragEnd}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => handleLetterClick(i)}
              className={`inline-flex items-center justify-center w-11 h-11 sm:w-12 sm:h-12 rounded-xl text-lg font-extrabold uppercase cursor-pointer select-none
                ${pressingTile === i ? 'letter-press' : ''}`}
              style={{
                backgroundColor: isPlaced ? 'var(--accent-subtle)' : 'var(--surface-secondary)',
                color: isPlaced ? 'var(--accent)' : 'var(--text-primary)',
                border: `1.5px solid ${isPlaced ? 'var(--accent)' : 'var(--border)'}`,
                opacity: isPlaced ? 0.45 : 1,
                boxShadow: isPlaced ? 'none' : '0 1px 3px rgba(0,0,0,0.04)',
                transform: isPlaced ? 'scale(0.95)' : 'scale(1)',
                transition: 'transform 0.18s cubic-bezier(0.22, 0.61, 0.36, 1), background-color 0.18s ease, border-color 0.18s ease, opacity 0.18s ease, box-shadow 0.18s ease',
              }}
              onMouseDown={(e) => {
                // Subtle glow on press
                e.currentTarget.style.boxShadow = isPlaced
                  ? 'none'
                  : '0 0 8px color-mix(in srgb, var(--accent) 30%, transparent)'
              }}
              onMouseUp={(e) => {
                e.currentTarget.style.boxShadow = isPlaced
                  ? 'none'
                  : '0 1px 3px rgba(0,0,0,0.04)'
              }}>
              {letter}
            </div>
          )
        })}
      </div>
      )}

      {/* ═══ Action Buttons ═══ */}
      <div className="flex items-center justify-center gap-3">
        <button onClick={handleReshuffle}
          className="ios-button ios-button-secondary gap-2 text-sm"
          style={{ borderRadius: 'var(--radius-md)' }}
          disabled={!!result}>
          <RefreshCw size={14} /> 重新打乱
        </button>

        {!result ? (
          <button onClick={handleCheck}
            className="ios-button ios-button-primary gap-2 text-sm"
            style={{ borderRadius: 'var(--radius-md)' }}
            disabled={placed.length === 0}>
            检查答案
          </button>
        ) : (
          <button onClick={handleNext}
            className="ios-button ios-button-primary gap-2 text-sm"
            style={{ borderRadius: 'var(--radius-md)', animation: 'scaleIn 0.3s cubic-bezier(0.22, 0.61, 0.36, 1) forwards' }}>
            {result === 'correct' ? '下一题' : '跳过'} <ArrowRight size={14} />
          </button>
        )}
      </div>
    </div>
  )
}
