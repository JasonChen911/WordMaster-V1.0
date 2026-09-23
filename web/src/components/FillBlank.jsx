import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft, ArrowRight, CheckCircle2, XCircle, Trophy, Sparkles,
  BookOpen, Zap, Volume2, ChevronRight, RotateCcw,
} from 'lucide-react'
import { api } from '../api'
import { speak } from '../tts'

// ═══════════════════════════════════════════════════════════════
// Web Audio — comprehensive game sound system
// ═══════════════════════════════════════════════════════════════
let _audioCtx = null
function ctx() {
  if (!_audioCtx) {
    try { _audioCtx = new (window.AudioContext || window.webkitAudioContext)() } catch (_) { /* noop */ }
  }
  if (_audioCtx && _audioCtx.state === 'suspended') _audioCtx.resume()
  return _audioCtx
}

function tone(freq, start, duration, vol = 0.12, type = 'sine') {
  const c = ctx(); if (!c) return
  const o = c.createOscillator()
  const g = c.createGain()
  o.type = type; o.frequency.value = freq
  g.gain.setValueAtTime(vol, start)
  g.gain.exponentialRampToValueAtTime(0.001, start + duration)
  o.connect(g).connect(c.destination)
  o.start(start); o.stop(start + duration)
}

function playStartSound() {
  const c = ctx(); if (!c) return
  const t = c.currentTime
  tone(392, t, 0.12, 0.10)       // G4
  tone(523, t + 0.06, 0.15, 0.10) // C5
  tone(659, t + 0.12, 0.15, 0.14) // E5
  tone(784, t + 0.18, 0.15, 0.18) // G5
}

function playLetterTickSound() {
  const c = ctx(); if (!c) return
  const t = c.currentTime
  tone(880, t, 0.06, 0.06)  // A5 — quick tick
}

function playCorrectSound() {
  const c = ctx(); if (!c) return
  const t = c.currentTime
  tone(523, t, 0.15, 0.10)       // C5
  tone(659, t + 0.05, 0.18, 0.10) // E5
  tone(784, t + 0.10, 0.25, 0.12) // G5
}

function playComboSound(combo) {
  const c = ctx(); if (!c) return
  const t = c.currentTime
  const base = 523 + combo * 80 // pitch rises with combo
  tone(base, t, 0.12, 0.08)
  tone(base * 1.25, t + 0.04, 0.15, 0.08)
  tone(base * 1.5, t + 0.08, 0.18, 0.10)
  tone(base * 2, t + 0.12, 0.20, 0.12)
}

function playWrongSound() {
  const c = ctx(); if (!c) return
  const t = c.currentTime
  tone(200, t, 0.25, 0.12, 'triangle')  // low, soft
  tone(180, t + 0.08, 0.20, 0.10, 'triangle')
}

// ═══════════════════════════════════════════════════════════════
// Particle dissolve on blank positions
// ═══════════════════════════════════════════════════════════════
function spawnDissolveParticles(el, count = 6) {
  if (!el) return
  const r = el.getBoundingClientRect()
  const cx = r.left + r.width / 2
  const cy = r.top + r.height / 2
  for (let i = 0; i < count; i++) {
    const p = document.createElement('div')
    const angle = (Math.PI * 2 * i) / count
    const dist = 8 + Math.random() * 16
    p.style.cssText = `
      position:fixed; left:${cx}px; top:${cy}px; z-index:9999;
      width:2px; height:2px; border-radius:50%; pointer-events:none;
      background:var(--accent);
      --dx:${Math.cos(angle) * dist}px; --dy:${Math.sin(angle) * dist - 6}px;
      animation: dissolveParticle 0.5s ease-out forwards;
    `
    document.body.appendChild(p)
    setTimeout(() => p.remove(), 600)
  }
}

// ═══════════════════════════════════════════════════════════════
// Dynamic masking algorithm
// ═══════════════════════════════════════════════════════════════
function computeMask(word) {
  const chars = word.toLowerCase().split('')
  const len = chars.length
  if (len <= 2) return { display: chars, blanks: [] }

  // Number of blanks: ~35-45% of letters
  const blankCount = Math.max(1, Math.min(Math.floor(len * 0.45), len - 2))
  const vowels = new Set(['a', 'e', 'i', 'o', 'u'])
  const blankIndices = new Set()

  // Always keep first letter visible
  // Prefer vowels for hiding
  const candidates = []
  for (let i = 1; i < len; i++) {
    candidates.push({ idx: i, isVowel: vowels.has(chars[i]) })
  }

  // Sort: vowels first, then random shuffle within groups
  const vowelCands = candidates.filter(c => c.isVowel)
  const consCands = candidates.filter(c => !c.isVowel)

  // Fisher-Yates for each group
  for (let i = vowelCands.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[vowelCands[i], vowelCands[j]] = [vowelCands[j], vowelCands[i]]
  }
  for (let i = consCands.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[consCands[i], consCands[j]] = [consCands[j], consCands[i]]
  }

  const ordered = [...vowelCands, ...consCands]

  // Pick blanks, ensuring no consecutive blanks
  let picked = 0
  for (const c of ordered) {
    if (picked >= blankCount) break
    if (blankIndices.has(c.idx - 1) || blankIndices.has(c.idx + 1)) continue
    blankIndices.add(c.idx)
    picked++
  }

  // If we still need more, pick random from remaining (relax consecutive rule)
  if (picked < blankCount) {
    for (const c of ordered) {
      if (picked >= blankCount) break
      if (!blankIndices.has(c.idx)) {
        blankIndices.add(c.idx)
        picked++
      }
    }
  }

  return {
    display: chars.map((ch, i) => blankIndices.has(i) ? '_' : ch),
    blanks: [...blankIndices].sort((a, b) => a - b),
  }
}

// ═══════════════════════════════════════════════════════════════
// FillBlank Component
// ═══════════════════════════════════════════════════════════════
export default function FillBlank({ onBack }) {
  const navigate = useNavigate()
  // ── Game phases: 'loading' | 'playing' | 'done'
  const [phase, setPhase] = useState('loading')

  // ── Active book (same source as Study module) ──
  const [activeBook, setActiveBook] = useState(null)

  // ── Game state ──
  const [words, setWords] = useState([])
  const [index, setIndex] = useState(0)
  const [mask, setMask] = useState(null)
  const [userInput, setUserInput] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [score, setScore] = useState(0)
  const [total, setTotal] = useState(0)
  const [combo, setCombo] = useState(0)
  const [bestCombo, setBestCombo] = useState(0)

  // ── Animation states ──
  const [lettersVisible, setLettersVisible] = useState([])
  const [showWord, setShowWord] = useState(false)
  const [answerShake, setAnswerShake] = useState(false)
  const [comboPopup, setComboPopup] = useState(false)
  const [comboCount, setComboCount] = useState(0)
  const [scoreBounce, setScoreBounce] = useState(false)

  const inputRef = useRef(null)
  const maskRefs = useRef([])
  const letterTimer = useRef(null)
  const comboPopupTimer = useRef(null)
  const autoAdvanceTimer = useRef(null)
  const canAdvance = useRef(false)

  // ── Cleanup ──
  useEffect(() => {
    return () => {
      if (letterTimer.current) clearInterval(letterTimer.current)
      if (comboPopupTimer.current) clearTimeout(comboPopupTimer.current)
      if (autoAdvanceTimer.current) clearTimeout(autoAdvanceTimer.current)
    }
  }, [])

  // ── Init: get active book (same pattern as Study.jsx), then start game ──
  useEffect(() => {
    let cancelled = false
    async function init() {
      try {
        const resp = await api.getActiveBook()
        if (cancelled) return
        const book = resp.book
        setActiveBook(book)
        if (book) {
          await loadGameWords(book)
        } else {
          setLoading(false)
          setPhase('loading')  // stay — will show "no book" UI
        }
      } catch (e) {
        if (!cancelled) { setLoading(false); setPhase('loading') }
      }
    }
    init()
    return () => { cancelled = true }
  }, [])

  // ── Focus input ──
  useEffect(() => {
    if (phase === 'playing' && !loading && words.length > 0) {
      setTimeout(() => inputRef.current?.focus(), 200)
    }
  }, [phase, index, loading])

  // ── Global keyboard: results screen ──
  useEffect(() => {
    if (phase !== 'done') return
    const handler = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        handleRestart()
      } else if (e.key === 'Escape') {
        e.preventDefault()
        onBack()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [phase])

  // ═══════════════════════════════════════
  // Start game
  // ═══════════════════════════════════════
  const GAME_SIZE = 10

  // ── Load words from the active book (same as Study page) ──
  const loadGameWords = async (book) => {
    setLoading(true)
    playStartSound()

    try {
      const data = await api.getGamesWords(Math.max(40, GAME_SIZE * 4), book.id)
      const allWords = (data.words || []).filter(w =>
        w.english && w.english.length >= 2 && w.chinese
      )
      if (allWords.length > 0) {
        const shuffled = [...allWords]
        for (let i = shuffled.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1))
          ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
        }
        const selected = shuffled.slice(0, GAME_SIZE)
        setWords(selected)
        setScore(0); setTotal(0); setCombo(0); setBestCombo(0)
        setPhase('playing')
        startRound(selected, 0)
      } else {
        setPhase('loading')  // stay — will show "no words" UI
      }
    } catch (err) {
      console.error('FillBlank load error:', err)
    }
    setLoading(false)
  }

  // ── Restart with same book ──
  const handleRestart = () => {
    setWords([])
    setMask(null)
    setUserInput('')
    setResult(null)
    setCombo(0)
    setBestCombo(0)
    setPhase('loading')
    if (activeBook) {
      loadGameWords(activeBook)
    }
  }

  // ═══════════════════════════════════════
  // Start a round
  // ═══════════════════════════════════════
  const startRound = useCallback((wordList, idx) => {
    if (idx >= wordList.length) {
      setPhase('done')
      return
    }
    const word = wordList[idx]
    const m = computeMask(word.english)
    setMask(m)
    setUserInput('')
    setResult(null)
    setShowWord(false)
    setAnswerShake(false)

    // Staggered letter reveal
    setLettersVisible([])
    if (letterTimer.current) clearTimeout(letterTimer.current)
    const totalLetters = m.display.length
    let revealed = 0
    const interval = Math.min(60, 300 / totalLetters)
    const timer = setInterval(() => {
      revealed++
      setLettersVisible(prev => [...prev, revealed - 1])
      playLetterTickSound()
      if (revealed >= totalLetters) clearInterval(timer)
    }, interval)
    letterTimer.current = timer
  }, [])

  // ═══════════════════════════════════════
  // Check answer
  // ═══════════════════════════════════════
  const current = words[index]

  const handleSubmit = (e) => {
    e?.preventDefault()
    if (!current || canAdvance.current) return  // guard: prevent double-enter
    const answer = userInput.trim().toLowerCase()
    const target = current.english.toLowerCase().replace(/[^a-z]/g, '')
    setTotal(prev => prev + 1)

    if (answer === target) {
      setResult('correct')
      setScore(prev => prev + 1)
      setShowWord(true)
      const newCombo = combo + 1
      setCombo(newCombo)
      if (newCombo > bestCombo) setBestCombo(newCombo)

      if (newCombo >= 3) {
        playComboSound(newCombo)
        setComboPopup(true)
        setComboCount(newCombo)
        comboPopupTimer.current = setTimeout(() => setComboPopup(false), 1500)
      } else {
        playCorrectSound()
      }

      setScoreBounce(true)
      setTimeout(() => setScoreBounce(false), 400)

      // Spawn particles
      if (maskRefs.current) {
        mask.blanks.forEach((bi, i) => {
          setTimeout(() => {
            const el = maskRefs.current[bi]
            if (el) spawnDissolveParticles(el, 5)
          }, i * 80)
        })
      }

      // Auto-advance after 1s, or allow Enter to skip
      canAdvance.current = true
      autoAdvanceTimer.current = setTimeout(() => {
        canAdvance.current = false
        handleNext()
      }, 1000)
    } else {
      setResult('wrong')
      setCombo(0)
      setAnswerShake(true)
      playWrongSound()
      setTimeout(() => setAnswerShake(false), 450)
      // For wrong answers, allow manual advance immediately
      canAdvance.current = true
    }
  }

  // ═══════════════════════════════════════
  // Next word
  // ═══════════════════════════════════════
  const handleNext = () => {
    if (autoAdvanceTimer.current) clearTimeout(autoAdvanceTimer.current)
    canAdvance.current = false
    const nextIdx = index + 1
    setIndex(nextIdx)
    startRound(words, nextIdx)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (result && canAdvance.current) {
        handleNext()
      } else if (!result) {
        handleSubmit(e)
      }
    } else if (e.key === 'Escape') {
      e.preventDefault()
      handleRestart()
    }
  }

  // ═══════════════════════════════════════
  // Phase: Init / No active book
  // ═══════════════════════════════════════
  if (phase === 'loading' && !activeBook && !loading) {
    return (
      <div className="page" style={{ paddingTop: '2rem' }}>
        <div className="flex items-center gap-3 mb-8">
          <button onClick={onBack} className="ios-icon-button"><ArrowLeft size={19} /></button>
          <BookOpen size={20} style={{ color: 'var(--accent)' }} />
          <h2 className="text-lg font-bold tracking-tight" style={{ color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
            挖空填词
          </h2>
        </div>

        <div className="text-center py-16">
          <div className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-5"
            style={{ backgroundColor: 'var(--accent-subtle)' }}>
            <BookOpen size={32} style={{ color: 'var(--accent)' }} />
          </div>
          <h3 className="text-base font-bold mb-2" style={{ color: 'var(--text-primary)' }}>未选择词书</h3>
          <p className="text-sm mb-2 leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            请先在首页「词书管理」中选择当前学习词书。
          </p>
          <p className="text-xs mb-6" style={{ color: 'var(--text-tertiary)' }}>
            背单词、复习、小游戏均使用统一词书。
          </p>
          <div className="flex gap-3 justify-center">
            <button onClick={onBack}
              className="ios-button ios-button-secondary" style={{ borderRadius: 'var(--radius-md)' }}>
              <ArrowLeft size={15} /> 返回
            </button>
            <button onClick={() => navigate('/dictionary')}
              className="ios-button ios-button-primary" style={{ borderRadius: 'var(--radius-md)' }}>
              前往词书管理
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════
  // Phase: Results
  // ═══════════════════════════════════════
  if (phase === 'done') {
    const pct = total > 0 ? Math.round((score / total) * 100) : 0
    return (
      <div className="page">
        <div className="text-center py-12">
          <div className="w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6 relative"
            style={{ backgroundColor: 'var(--accent-subtle)' }}>
            <Trophy size={40} style={{ color: 'var(--accent)' }} />
          </div>
          <h2 className="text-2xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>游戏完成！</h2>
          <p className="text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>
            {activeBook?.book_name} · 正确 {score}/{total}（{pct}%）
          </p>

          {/* Stats grid */}
          <div className="grid grid-cols-3 gap-3 max-w-xs mx-auto mt-6 mb-8">
            <div className="rounded-xl p-3" style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)' }}>
              <div className="text-lg font-bold" style={{ color: 'var(--accent)' }}>{score}</div>
              <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>正确</div>
            </div>
            <div className="rounded-xl p-3" style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)' }}>
              <div className="text-lg font-bold" style={{ color: pct >= 70 ? 'var(--success)' : pct >= 40 ? 'var(--warning)' : 'var(--danger)' }}>{pct}%</div>
              <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>正确率</div>
            </div>
            <div className="rounded-xl p-3" style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)' }}>
              <div className="text-lg font-bold" style={{ color: 'var(--accent)' }}>{bestCombo}</div>
              <div className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>最高连击</div>
            </div>
          </div>

          <div className="flex gap-3 justify-center">
            <button onClick={handleRestart}
              className="ios-button ios-button-secondary gap-2" style={{ borderRadius: 'var(--radius-md)' }}>
              <RotateCcw size={14} /> 再来一轮
            </button>
            <button onClick={onBack}
              className="ios-button ios-button-primary gap-2" style={{ borderRadius: 'var(--radius-md)' }}>
              <ArrowLeft size={14} /> 返回
            </button>
          </div>

          <div className="flex items-center justify-center gap-4 mt-5">
            <kbd className="text-[10px] px-2 py-0.5 rounded font-medium"
              style={{ color: 'var(--accent)', backgroundColor: 'var(--accent-subtle)', border: '1px solid color-mix(in srgb, var(--accent) 20%, transparent)' }}>
              Enter 再来一轮
            </kbd>
            <kbd className="text-[10px] px-2 py-0.5 rounded font-medium"
              style={{ color: 'var(--text-tertiary)', backgroundColor: 'var(--surface-tertiary)', border: '1px solid var(--border)' }}>
              Esc 返回选择
            </kbd>
          </div>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════
  // Phase: Playing — loading or empty
  // ═══════════════════════════════════════
  if (loading) {
    return (
      <div className="page flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 rounded-full border-[2.5px] animate-spin"
            style={{ borderColor: 'var(--border)', borderTopColor: 'var(--accent)' }} />
          <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>加载「{activeBook?.book_name}」词书单词...</p>
        </div>
      </div>
    )
  }

  if (words.length === 0) {
    return (
      <div className="page flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ backgroundColor: 'var(--accent-subtle)' }}>
            <BookOpen size={28} style={{ color: 'var(--accent)' }} />
          </div>
          <p className="text-sm mb-2" style={{ color: 'var(--text-secondary)' }}>
            「{activeBook?.book_name}」中没有可用单词。
          </p>
          <p className="text-xs mb-5" style={{ color: 'var(--text-tertiary)' }}>
            请确认该词书包含单词数据，或选择其他词书。
          </p>
          <button onClick={handleRestart}
            className="ios-button ios-button-secondary" style={{ borderRadius: 'var(--radius-md)' }}>
            <ArrowLeft size={15} /> 重新选择
          </button>
        </div>
      </div>
    )
  }

  // Score display
  const scoreDisplay = (
    <div className={`flex items-center gap-1.5 ${scoreBounce ? 'score-bounce' : ''}`}>
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--accent)"
        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      </svg>
      <span className="text-xs font-bold tracking-tight" style={{ color: 'var(--accent)', fontVariantNumeric: 'tabular-nums' }}>
        {score}
      </span>
    </div>
  )

  return (
    <div className="page" style={{ paddingTop: '0.5rem' }}>
      {/* ═══ Top Bar ═══ */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <button onClick={handleRestart} className="ios-icon-button" aria-label="Back">
            <ArrowLeft size={19} />
          </button>
          <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full"
            style={{ backgroundColor: 'var(--accent-subtle)', color: 'var(--accent)', display: activeBook ? '' : 'none' }}>
            {activeBook?.book_name}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium" style={{ color: 'var(--text-tertiary)' }}>
            {index + 1}/{words.length}
          </span>
          {scoreDisplay}
        </div>
      </div>

      {/* ═══ Combo popup ═══ */}
      {comboPopup && (
        <div className="flex justify-center mb-4 combo-popup">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
            style={{ backgroundColor: 'var(--accent-subtle)' }}>
            <Zap size={14} style={{ color: 'var(--accent)' }} />
            <span className="text-xs font-bold" style={{ color: 'var(--accent)' }}>{comboCount} 连击!</span>
          </div>
        </div>
      )}

      {/* ═══ Question Card ═══ */}
      <div className={`rounded-2xl p-6 mb-6 card-enter ${answerShake ? 'shake' : ''}`}
        style={{
          backgroundColor: 'var(--surface-secondary)',
          border: `1.5px solid ${result === 'correct' ? 'var(--success)' : result === 'wrong' ? 'var(--danger)' : 'var(--border)'}`,
          transition: 'border-color 0.3s ease',
          animationDelay: '0s',
        }}>
        {/* Chinese hint */}
        <div className="mb-4">
          <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
            中文提示
          </span>
          <p className="text-lg font-bold mt-0.5" style={{ color: 'var(--text-primary)' }}>
            {current?.chinese}
          </p>
        </div>

        {/* Masked word display */}
        <div className="rounded-xl p-5 mb-4" style={{
          backgroundColor: result === 'correct' ? 'var(--success-subtle)' : 'var(--surface-tertiary)',
          transition: 'background-color 0.4s ease',
        }}>
          <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
            拼写
          </span>
          <div className="flex justify-center gap-1.5 mt-2 flex-wrap">
            {mask && mask.display.map((ch, i) => {
              const isBlank = ch === '_'
              const visible = lettersVisible.includes(i)
              return (
                <span
                  key={i}
                  ref={el => { maskRefs.current[i] = el }}
                  className={`inline-flex items-center justify-center w-8 h-10 sm:w-9 sm:h-11 rounded-lg text-lg font-extrabold uppercase tracking-wider select-none
                    ${!visible ? '' : 'letter-appear'}
                    ${isBlank && visible ? 'blank-breathe' : ''}
                    ${isBlank && showWord ? 'letter-reveal' : ''}
                    ${!isBlank && showWord ? 'word-glow' : ''}`}
                  style={{
                    color: isBlank && showWord
                      ? 'var(--success)'
                      : isBlank
                      ? 'var(--text-tertiary)'
                      : 'var(--text-primary)',
                    backgroundColor: isBlank ? 'color-mix(in srgb, var(--accent) 8%, transparent)' : 'transparent',
                    border: isBlank && result === 'wrong'
                      ? '1.5px solid var(--danger)'
                      : isBlank
                      ? '1px dashed var(--border)'
                      : '1px solid transparent',
                    borderRadius: 'var(--radius-sm)',
                    transition: 'color 0.3s ease, border-color 0.3s ease, background-color 0.3s ease',
                  }}>
                  {showWord && isBlank ? mask.display.map((c, j) => mask.blanks.includes(j) ? current.english[j] : '')[i] || current.english[i] : ch}
                </span>
              )
            })}
          </div>
        </div>

        {/* Sentence hint */}
        {current?.example_en && (
          <div className="rounded-lg p-3" style={{ backgroundColor: 'var(--surface-tertiary)' }}>
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
                例句
              </span>
              <button
                onClick={() => current?.example_en && speak(current.example_en)}
                className="p-0.5 rounded transition-all hover:opacity-70"
                style={{ color: 'var(--text-tertiary)' }}
                title="播放例句">
                <Volume2 size={13} />
              </button>
            </div>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)', lineHeight: '1.8' }}>
              {current.example_en.replace(
                new RegExp(current.english.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'),
                '_______'
              ).replace(/_{3,}/g, '_______')}
            </p>
            {current.example_cn && (
              <p className="text-xs mt-1.5" style={{ color: 'var(--text-tertiary)' }}>{current.example_cn}</p>
            )}
          </div>
        )}

        {/* Correct answer revealed */}
        {result && showWord && (
          <div className="text-center mt-4 animate-scale-in">
            <div className="flex items-center justify-center gap-2 text-sm font-bold" style={{ color: 'var(--success)' }}>
              <CheckCircle2 size={18} /> Correct!
            </div>
          </div>
        )}

        {/* Wrong feedback */}
        {result === 'wrong' && !showWord && (
          <div className="text-center mt-4 animate-scale-in">
            <p className="text-sm font-semibold" style={{ color: 'var(--danger)' }}>
              不对哦，正确答案：
            </p>
            <p className="text-base font-bold tracking-wide mt-0.5" style={{ color: 'var(--accent)' }}>
              {current?.english}
            </p>
          </div>
        )}
      </div>

      {/* ═══ Input ═══ */}
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={showWord ? '' : '输入单词...'}
            disabled={!!result}
            className="input text-center text-lg font-semibold tracking-wide py-3.5"
            style={{
              borderRadius: 'var(--radius-lg)',
              fontSize: '1.1rem',
              letterSpacing: '0.05em',
              borderColor: result === 'wrong' ? 'var(--danger)' : undefined,
            }}
            autoComplete="off" autoCapitalize="off" spellCheck={false}
          />
          {showWord && !userInput && (
            <p className="text-center mt-2 text-xs" style={{ color: 'var(--text-tertiary)' }}>
              答案：<strong style={{ color: 'var(--accent)' }}>{current?.english}</strong>
            </p>
          )}
        </div>
      </form>

      {/* ═══ Action Buttons ═══ */}
      <div className="flex items-center justify-center gap-3">
        {!result ? (
          <>
            <button
              onClick={() => {
                if (mask?.blanks.length > 0) {
                  const chars = [...mask.display]
                  const nextBlank = mask.blanks.find(b => chars[b] === '_')
                  if (nextBlank !== undefined) {
                    chars[nextBlank] = current.english[nextBlank]
                    setMask({ ...mask, display: chars })
                  }
                }
              }}
              className="ios-button ios-button-secondary gap-2 text-sm"
              style={{ borderRadius: 'var(--radius-md)' }}>
              提示
            </button>
            <button onClick={handleSubmit}
              className="ios-button ios-button-primary gap-2 text-sm"
              style={{ borderRadius: 'var(--radius-md)' }}
              disabled={!userInput.trim()}>
              检查答案
            </button>
          </>
        ) : (
          <button onClick={handleNext}
            className="ios-button ios-button-primary gap-2 text-sm"
            style={{ borderRadius: 'var(--radius-md)', animation: 'scaleIn 0.3s cubic-bezier(0.22, 0.61, 0.36, 1) forwards' }}>
            {canAdvance.current ? '下一题' : '即将跳转...'} <ArrowRight size={14} />
          </button>
        )}
      </div>

      {/* ═══ Keyboard hints ═══ */}
      <div className="flex items-center justify-center gap-4 mt-5">
        {!result ? (
          <>
            <kbd className="text-[10px] px-2 py-0.5 rounded font-medium"
              style={{ color: 'var(--text-tertiary)', backgroundColor: 'var(--surface-tertiary)', border: '1px solid var(--border)' }}>
              Enter 提交
            </kbd>
            <kbd className="text-[10px] px-2 py-0.5 rounded font-medium"
              style={{ color: 'var(--text-tertiary)', backgroundColor: 'var(--surface-tertiary)', border: '1px solid var(--border)' }}>
              Esc 返回
            </kbd>
          </>
        ) : (
          <>
            <kbd className="text-[10px] px-2 py-0.5 rounded font-medium"
              style={{ color: 'var(--accent)', backgroundColor: 'var(--accent-subtle)', border: '1px solid color-mix(in srgb, var(--accent) 20%, transparent)' }}>
              Enter 下一题
            </kbd>
            <kbd className="text-[10px] px-2 py-0.5 rounded font-medium"
              style={{ color: 'var(--text-tertiary)', backgroundColor: 'var(--surface-tertiary)', border: '1px solid var(--border)' }}>
              Esc 返回
            </kbd>
          </>
        )}
      </div>
    </div>
  )
}
