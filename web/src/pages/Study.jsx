import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft, CheckCircle2, HelpCircle, XCircle, Sparkles, RefreshCw,
  Zap, Trophy, BookOpen, RotateCcw, Gamepad2, Brain,
} from 'lucide-react'
import { api } from '../api'
import { speak, preloadQueue, getAutoPlay, stop as stopTts } from '../tts'
import WordCard from '../components/WordCard'
import Modal, { AlertModal } from '../components/Modal'
import Celebration from '../components/Celebration'

// ═══════════════════════════════════════════════════════════════
// Crystalline Literacy — Study Page
// All business logic preserved verbatim. Only render layer changed.
// ═══════════════════════════════════════════════════════════════

/** Answer button config — four-grade FSRS feedback.
 *  Order matches keyboard shortcuts 1-4: 忘记 → 困难 → 一般 → 简单. */
const ANSWER_BUTTONS = [
  { result: 'unknown',  icon: XCircle,      label: '忘记', key: '1', color: '#ef4444' },
  { result: 'fuzzy',    icon: HelpCircle,   label: '困难', key: '2', color: '#f59e0b' },
  { result: 'know',     icon: CheckCircle2, label: '一般', key: '3', color: '#10b981' },
  { result: 'too_easy', icon: Zap,          label: '简单', key: '4', color: '#6366f1' },
]

export default function Study() {
  const navigate = useNavigate()
  const [words, setWords] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [showAnswer, setShowAnswer] = useState(false)
  const [loading, setLoading] = useState(true)
  const [completed, setCompleted] = useState(false)
  const [sessionStats, setSessionStats] = useState({ too_easy: 0, know: 0, fuzzy: 0, unknown: 0 })
  const [animating, setAnimating] = useState(false)
  const [error, setError] = useState(null)
  const [transition, setTransition] = useState('in')
  const [activeBook, setActiveBook] = useState(null)
  const [dailyGoal, setDailyGoal] = useState(20)
  const [dailyCompleted, setDailyCompleted] = useState(0)
  const [summary, setSummary] = useState(null)
  const [showResetModal, setShowResetModal] = useState(false)
  const [alertMsg, setAlertMsg] = useState(null)
  const [showCelebration, setShowCelebration] = useState(false)
  const [celebrationData, setCelebrationData] = useState({ wordsCount: 0, masteredToday: 0, streakDays: 0 })
  const [lastFsrs, setLastFsrs] = useState(null)
  const [showWhy, setShowWhy] = useState(false)
  const [whyData, setWhyData] = useState(null)
  const [whyLoading, setWhyLoading] = useState(false)
  const cardStartTime = useRef(Date.now())
  const bookIdRef = useRef(null)
  const sessionIdRef = useRef(`study-${Date.now()}-${Math.floor(Math.random() * 1e6)}`)

  // ── Unified study summary (daily goal + ETA, same as the homepage) ──
  const fetchSummary = useCallback(async () => {
    try {
      const s = await api.getStudySummary()
      setSummary(s)
      if (s?.daily_goal) setDailyGoal(s.daily_goal)
    } catch (e) { console.error(e) }
  }, [])

  // ── Load words (queue size = unified daily goal) ──
  const fetchWords = useCallback(async (bookId, goal) => {
    setLoading(true); setError(null)
    try {
      const data = await api.getStudyQueue(bookId, goal)
      setWords(data)
    } catch (e) {
      setError('Failed to load words.')
      console.error(e)
    } finally { setLoading(false) }
  }, [])

  // ── Init ──
  useEffect(() => {
    let cancelled = false
    async function init() {
      try {
        const [bookResp, summaryData] = await Promise.all([api.getActiveBook(), api.getStudySummary()])
        if (cancelled) return
        const book = bookResp.book
        setActiveBook(book)
        if (summaryData) {
          setSummary(summaryData)
          setDailyGoal(summaryData.daily_goal || 20)
        }
        const goal = summaryData?.daily_goal || 20
        if (book) { bookIdRef.current = book.id; await fetchWords(book.id, goal) }
        else { await fetchWords(null, goal) }
      } catch (e) {
        if (!cancelled) { await fetchSummary(); await fetchWords(null, 20) }
      }
    }
    init()
    return () => { cancelled = true }
  }, [])

  // ── Poll for book changes ──
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const resp = await api.getActiveBook()
        if (resp.book && resp.book.id !== bookIdRef.current) {
          const newBook = resp.book
          setActiveBook(newBook); bookIdRef.current = newBook.id
          setCurrentIndex(0); setShowAnswer(false); setWords([])
          setCompleted(false); setDailyCompleted(0)
          setSessionStats({ too_easy: 0, know: 0, fuzzy: 0, unknown: 0 })
          cardStartTime.current = Date.now()
          api.getStudySummary().then((s) => {
            setSummary(s); setDailyGoal(s?.daily_goal || 20)
            fetchWords(newBook.id, s?.daily_goal || 20)
          })
        }
      } catch (e) { /* ignore */ }
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  const currentWord = words[currentIndex]

  const handleCardTap = () => {
    if (!showAnswer && currentWord) setShowAnswer(true)
  }

  const handleResult = async (result) => {
    if (!currentWord || animating) return
    setAnimating(true)
    const secondsSpent = Math.round((Date.now() - cardStartTime.current) / 1000)
    const responseTimeMs = Date.now() - cardStartTime.current
    try {
      const resp = await api.recordStudy(currentWord.english, result, secondsSpent, sessionIdRef.current, responseTimeMs)
      setSessionStats(prev => ({ ...prev, [result]: prev[result] + 1 }))
      setDailyCompleted(prev => prev + 1)
      setLastFsrs(resp?.fsrs || null)
      fetchSummary() // refresh the unified ETA after completing a word
    } catch (e) {
      console.error(e)
      setLastFsrs(null)
    }

    setTransition('out')
    setTimeout(() => {
      setShowAnswer(false)
      setLastFsrs(null)
      if (currentIndex + 1 < words.length) {
        setCurrentIndex(prev => prev + 1)
        cardStartTime.current = Date.now()
      } else {
        setCompleted(true)
        triggerCelebration()
      }
      setAnimating(false)
      setTransition('in')
    }, 550)
  }

  // ── Keyboard shortcuts: 1 忘记 · 2 困难 · 3 一般 · 4 简单 ──
  useEffect(() => {
    const onKey = (e) => {
      if (!showAnswer || animating || completed) return
      const btn = ANSWER_BUTTONS.find((b) => b.key === e.key)
      if (btn) handleResult(btn.result)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [showAnswer, animating, completed, currentWord, currentIndex, words])

  // ── Preload current + next 1–2 word audio (background, non-blocking) ──
  useEffect(() => {
    if (!currentWord) return
    const texts = [
      currentWord.english,
      words[currentIndex + 1]?.english,
      words[currentIndex + 2]?.english,
    ].filter(Boolean)
    preloadQueue(texts)
  }, [currentIndex, words, currentWord])

  // ── Auto-play the new word once its card has transitioned ──
  useEffect(() => {
    if (!currentWord || !getAutoPlay()) return
    const t = setTimeout(() => speak(currentWord.english), 420)
    return () => clearTimeout(t)
  }, [currentWord?.english])

  // ── Stop any playing audio when leaving the study page ──
  useEffect(() => {
    return () => stopTts()
  }, [])

  const openWhy = async () => {
    if (!currentWord) return
    setShowWhy(true)
    setWhyLoading(true)
    setWhyData(null)
    try {
      const data = await api.getWordFsrs(currentWord.id)
      setWhyData(data)
    } catch (e) {
      setWhyData({ has_history: false, english: currentWord.english, review_count: 0 })
    } finally {
      setWhyLoading(false)
    }
  }

  const handleToggleFavorite = async () => {
    if (!currentWord) return
    try {
      await api.toggleFavorite(currentWord.id)
      setWords(prev => prev.map((w, i) => (i === currentIndex ? { ...w, is_favorite: !w.is_favorite } : w)))
    } catch (e) { console.error(e) }
  }

  const triggerCelebration = async () => {
    const total = sessionStats.too_easy + sessionStats.know + sessionStats.fuzzy + sessionStats.unknown + 1
    const known = sessionStats.too_easy + sessionStats.know + 1
    try {
      const dashData = await api.getDashboard(bookIdRef.current)
      setCelebrationData({ wordsCount: total, masteredToday: known, streakDays: dashData?.streak_days || 0 })
    } catch (e) {
      setCelebrationData({ wordsCount: total, masteredToday: known, streakDays: 0 })
    }
    setShowCelebration(true)
  }

  const handleDismissCelebration = () => setShowCelebration(false)

  const handleReset = () => setShowResetModal(true)

  const doReset = async () => {
    setShowResetModal(false)
    try {
      await api.resetProgress(bookIdRef.current)
      setCurrentIndex(0); setShowAnswer(false); setCompleted(false)
      setDailyCompleted(0)
      setSessionStats({ too_easy: 0, know: 0, fuzzy: 0, unknown: 0 })
      cardStartTime.current = Date.now()
      localStorage.removeItem('wordmaster-daily-' + new Date().toISOString().slice(0, 10))
      await fetchWords(bookIdRef.current)
    } catch (e) {
      setAlertMsg('重置失败: ' + (e.message || '未知错误'))
    }
  }

  // ═══════════════════════════════════════
  // Loading
  // ═══════════════════════════════════════
  if (loading) {
    return (
      <div className="page flex items-center justify-center min-h-[70vh]">
        <div className="flex flex-col items-center gap-5">
          <div className="w-10 h-10 rounded-full border-[2.5px] animate-spin"
            style={{ borderColor: 'var(--border)', borderTopColor: 'var(--accent)' }} />
          <p className="text-sm font-medium" style={{ color: 'var(--text-tertiary)' }}>准备学习数据...</p>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════
  // Error
  // ═══════════════════════════════════════
  if (error) {
    return (
      <div className="page flex items-center justify-center min-h-[70vh]">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-5"
            style={{ backgroundColor: 'var(--surface-tertiary)' }}>
            <Sparkles size={28} style={{ color: 'var(--text-tertiary)' }} />
          </div>
          <p className="text-sm mb-5" style={{ color: 'var(--text-secondary)' }}>{error}</p>
          <button onClick={() => fetchWords(bookIdRef.current)}
            className="ios-button ios-button-secondary" style={{ borderRadius: 'var(--radius-md)' }}>重试</button>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════
  // Empty
  // ═══════════════════════════════════════
  if (words.length === 0 && !loading) {
    return (
      <div className="page flex items-center justify-center min-h-[70vh]">
        <div className="text-center max-w-sm">
          <div className="w-20 h-20 rounded-[20px] flex items-center justify-center mx-auto mb-6"
            style={{ backgroundColor: 'var(--accent-subtle)' }}>
            <Trophy size={36} style={{ color: 'var(--accent)' }} />
          </div>
          <h2 className="text-xl font-bold mb-2 tracking-tight" style={{ color: 'var(--text-primary)' }}>
            全部完成！
          </h2>
          <p className="text-sm mb-8 leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            {activeBook
              ? `${activeBook.book_name} — 暂无需要复习的单词`
              : '暂无需要复习的单词'}
          </p>
          <div className="flex flex-col gap-3 items-center">
            <button onClick={() => navigate('/')}
              className="ios-button ios-button-secondary"
              style={{ borderRadius: 'var(--radius-md)', minWidth: '12rem' }}>返回首页</button>
            <button onClick={handleReset}
              className="text-xs flex items-center gap-1.5 transition-all hover:opacity-70"
              style={{ color: 'var(--text-tertiary)' }}>
              <RotateCcw size={12} /> 重置学习进度
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════
  // Completed
  // ═══════════════════════════════════════
  if (completed) {
    const total = sessionStats.too_easy + sessionStats.know + sessionStats.fuzzy + sessionStats.unknown
    const known = sessionStats.too_easy + sessionStats.know
    const accuracy = total > 0 ? Math.round((known / total) * 100) : 0

    return (
      <>
        {showCelebration && (
          <Celebration
            wordsCount={celebrationData.wordsCount}
            masteredToday={celebrationData.masteredToday}
            streakDays={celebrationData.streakDays}
            onDismiss={handleDismissCelebration}
          />
        )}

        <div className="page">
          <div className="text-center py-12">
            {/* Trophy */}
            <div className="w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6 relative"
              style={{ backgroundColor: 'var(--accent-subtle)' }}>
              <div className="absolute inset-0 rounded-full animate-sound-wave"
                style={{ border: '2px solid var(--accent)', opacity: 0.25 }} />
              <Trophy size={38} style={{ color: 'var(--accent)' }} />
            </div>

            <h2 className="text-[1.75rem] font-bold mb-2 tracking-tight"
              style={{ color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
              学习完成
            </h2>
            <p className="text-sm mb-8" style={{ color: 'var(--text-secondary)' }}>
              {total} 个单词 · {accuracy}% 正确率
            </p>

            {/* Stat cards grid */}
            <div className="grid grid-cols-4 gap-2.5 mb-10 max-w-md mx-auto">
              {ANSWER_BUTTONS.map(({ result, icon: Icon, label, color }) => (
                <div key={result}
                  style={{
                    backgroundColor: 'var(--surface-secondary)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '0.9rem 0.5rem',
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem',
                  }}>
                  <Icon size={18} style={{ color }} />
                  <div className="text-xl font-bold tracking-tight"
                    style={{ color, letterSpacing: '-0.02em' }}>{sessionStats[result]}</div>
                  <div className="text-[10px] font-semibold uppercase tracking-wider"
                    style={{ color: 'var(--text-tertiary)' }}>{label}</div>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="flex gap-3 justify-center">
              <button onClick={() => {
                setCurrentIndex(0); setCompleted(false); setShowAnswer(false)
                setDailyCompleted(0)
                setSessionStats({ too_easy: 0, know: 0, fuzzy: 0, unknown: 0 })
                setShowCelebration(false)
                cardStartTime.current = Date.now()
                fetchWords(bookIdRef.current)
              }}
                className="ios-button ios-button-secondary gap-2"
                style={{ borderRadius: 'var(--radius-md)' }}>
                <RefreshCw size={15} /> 再来一轮
              </button>
              <button onClick={() => navigate('/')}
                className="ios-button ios-button-primary gap-2"
                style={{ borderRadius: 'var(--radius-md)' }}>
                <ArrowLeft size={15} /> 返回首页
              </button>
            </div>
          </div>
        </div>
      </>
    )
  }

  // ═══════════════════════════════════════
  // Main Study View
  // ═══════════════════════════════════════
  const sessionPct = words.length > 0 ? (currentIndex / words.length) * 100 : 0
  const goalPct = Math.min(100, (dailyCompleted / dailyGoal) * 100)

  return (
    <div className="page" style={{ paddingTop: '1.5rem' }}>
      {/* ═══ Top Bar ═══ */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: '1.25rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button onClick={() => navigate('/')} className="ios-icon-button" aria-label="Back">
            <ArrowLeft size={19} />
          </button>
          <button onClick={() => navigate('/games')} className="ios-icon-button" title="小游戏"
            style={{ color: 'var(--accent)' }}>
            <Gamepad2 size={17} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.15rem' }}>
          {activeBook && (
            <button
              onClick={() => navigate('/dictionary')}
              title="管理词书"
              className="text-[11px] font-semibold px-3 py-0.5 rounded-full transition-all duration-200 hover:opacity-70"
              style={{ backgroundColor: 'var(--accent-subtle)', color: 'var(--accent)', border: 'none', cursor: 'pointer' }}>
              {activeBook.book_name}
            </button>
          )}
          <span className="text-[11px] font-medium" style={{ color: 'var(--text-tertiary)' }}>
            {currentIndex + 1} / {words.length}
          </span>
        </div>

        <button onClick={handleReset} className="ios-icon-button" title="重置进度"
          style={{ color: 'var(--text-tertiary)' }}>
          <RotateCcw size={16} />
        </button>
      </div>

      {/* ═══ Unified Progress ═══ */}
      <div style={{ marginBottom: '1.75rem' }}>
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
          marginBottom: '0.4rem',
        }}>
          <span className="text-[10px] font-semibold uppercase tracking-wider"
            style={{ color: 'var(--text-tertiary)' }}>
            {summary?.display_text || '加载中…'}
          </span>
          <span className="text-[10px] font-semibold uppercase tracking-wider"
            style={{ color: 'var(--text-tertiary)' }}>
            进度 {Math.round(sessionPct)}%
          </span>
        </div>
        <div style={{
          display: 'flex', gap: '3px',
          height: '4px', borderRadius: '100px', overflow: 'hidden',
          backgroundColor: 'var(--surface-tertiary)',
        }}>
          <div style={{
            height: '100%', borderRadius: '100px',
            backgroundColor: 'var(--accent)',
            width: `${goalPct}%`,
            transition: 'width 0.6s cubic-bezier(0.22, 0.61, 0.36, 1)',
          }} />
          <div style={{
            height: '100%', borderRadius: '100px',
            backgroundColor: 'var(--text-tertiary)', opacity: 0.25,
            width: `${Math.max(0, sessionPct - goalPct)}%`,
            transition: 'width 0.6s cubic-bezier(0.22, 0.61, 0.36, 1)',
          }} />
        </div>
      </div>

      {/* ═══ Word Card ═══ */}
      <div style={{
        opacity: transition === 'out' ? 0 : 1,
        transform: transition === 'out' ? 'translateY(-10px) scale(0.975)' : 'none',
        transition: 'opacity 0.22s ease, transform 0.28s cubic-bezier(0.22, 0.61, 0.36, 1)',
      }}>
        <WordCard
          word={currentWord}
          showAnswer={showAnswer}
          onToggleAnswer={handleCardTap}
          onToggleFavorite={handleToggleFavorite}
          onAskAI={null}
        />
      </div>

      {/* ═══ Answer Buttons ═══ */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.6rem',
        marginTop: '1.25rem',
        opacity: showAnswer ? 1 : 0,
        transform: showAnswer ? 'translateY(0)' : 'translateY(10px)',
        transition: 'all 0.3s cubic-bezier(0.22, 0.61, 0.36, 1)',
        pointerEvents: showAnswer ? 'auto' : 'none',
      }}>
        {ANSWER_BUTTONS.map(({ result, icon: Icon, label, key, color }) => (
          <button
            key={result}
            onClick={() => handleResult(result)}
            disabled={animating}
            className="ios-answer-button"
            style={{ '--btn-color': color, position: 'relative' }}
          >
            <span style={{
              position: 'absolute', top: 4, right: 6,
              fontSize: '9px', fontWeight: 700, opacity: 0.45,
            }}>{key}</span>
            <Icon size={20} strokeWidth={2} />
            <span className="text-[11px] font-semibold">{label}</span>
          </button>
        ))}
      </div>

      {/* ═══ FSRS feedback after answering ═══ */}
      {lastFsrs && showAnswer && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
          marginTop: '0.9rem', padding: '0.6rem 0.9rem',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--surface-secondary)',
          border: '1px solid var(--border)',
          animation: 'fadeSlideIn 0.3s ease forwards',
        }}>
          <Sparkles size={13} style={{ color: 'var(--accent)', flexShrink: 0 }} />
          <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            {formatFsrsFeedback(lastFsrs)}
          </span>
        </div>
      )}

      {/* ═══ Why? / footer hint ═══ */}
      <div className="text-center mt-6 flex items-center justify-center gap-3">
        <p className="text-[11px]" style={{ color: 'var(--text-tertiary)', opacity: 0.5 }}>
          点击卡片查看释义 · 键盘 1-4 快速作答
        </p>
        <button
          onClick={openWhy}
          className="flex items-center gap-1 text-[11px] font-semibold transition-opacity hover:opacity-70"
          style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer' }}>
          <Brain size={13} /> 为什么今天复习？
        </button>
      </div>

      {/* ═══ Why modal ═══ */}
      <Modal
        open={showWhy}
        onClose={() => setShowWhy(false)}
        title="为什么今天复习这个词？"
        message={null}
        confirmLabel="知道了"
        cancelLabel=""
        onConfirm={() => setShowWhy(false)}
      >
        {whyLoading ? (
          <p className="text-sm py-4" style={{ color: 'var(--text-tertiary)' }}>正在计算记忆状态...</p>
        ) : whyData && whyData.has_history ? (
          <div className="space-y-2 py-1">
            <FsrsStat label="预计记忆保持率" value={`${Math.round((whyData.retrievability || 0) * 100)}%`} />
            <FsrsStat label="记忆稳定度" value={`${whyData.stability_days ?? 0} 天`} />
            <FsrsStat label="遗忘风险" value={riskLabel(whyData.forgetting_risk)} />
            <FsrsStat label="已复习" value={`${whyData.reps ?? 0} 次 · 遗忘 ${whyData.lapses ?? 0} 次`} />
            {whyData.next_review && (
              <FsrsStat label="下次复习" value={formatNextReview(whyData.next_review)} />
            )}
          </div>
        ) : (
          <p className="text-sm py-4" style={{ color: 'var(--text-secondary)' }}>
            这个词还没有复习记录。完成第一次学习后，FSRS 会根据你的记忆表现自动计算下一次复习时间。
          </p>
        )}
      </Modal>

      {/* ═══ Reset Modal ═══ */}
      <Modal
        open={showResetModal}
        onClose={() => setShowResetModal(false)}
        title="重置学习进度？"
        message={'确定要重置所有学习进度吗？\n\n清除：\n已学单词 · 记忆状态 · 复习记录 · 今日记录\n\n保留：\n词书 · 单词数据\n\n所有词书回到 0 进度。'}
        confirmLabel="确认重置"
        cancelLabel="取消"
        onConfirm={doReset}
        danger
      />

      <AlertModal
        open={!!alertMsg}
        onClose={() => setAlertMsg(null)}
        title="提示"
        message={alertMsg || ''}
      />
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
// FSRS helpers
// ═══════════════════════════════════════════════════════════════

function formatFsrsFeedback(fsrs) {
  if (!fsrs) return '已记录本次复习。'
  const r = Math.round((fsrs.retrievability || 0) * 100)
  const d = fsrs.next_review ? formatNextReview(fsrs.next_review) : ''
  if (fsrs.forgetting_risk === 'high') {
    return `遗忘风险较高，明天再次出现${d ? `（${d}）` : ''}。`
  }
  return `${d ? `预计 ${d} 后复习` : '复习时间已更新'}，当前保持率约 ${r}%。`
}

function formatNextReview(iso) {
  if (!iso) return ''
  const due = new Date(iso.endsWith('Z') ? iso : iso + '')
  const diffMs = due.getTime() - Date.now()
  if (isNaN(diffMs)) return ''
  const minutes = Math.round(diffMs / 60000)
  if (minutes < 60) return `${Math.max(1, minutes)} 分钟`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} 小时`
  const days = Math.round(hours / 24)
  return `${days} 天`
}

function riskLabel(risk) {
  if (risk === 'high') return '高（建议尽快复习）'
  if (risk === 'medium') return '中'
  return '低'
}

function FsrsStat({ label, value }) {
  return (
    <div className="flex items-center justify-between py-1.5 px-3 rounded-lg"
      style={{ backgroundColor: 'var(--surface-tertiary)' }}>
      <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{label}</span>
      <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{value}</span>
    </div>
  )
}
