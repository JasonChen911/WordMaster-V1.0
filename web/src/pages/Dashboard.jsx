import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Zap, TrendingUp, Target, Flame, BookOpen, Clock, ChevronRight,
  RefreshCw, ArrowRight, Sparkles, Search, X, Volume2,
  Calendar, BarChart3, Trophy, Timer, Star,
} from 'lucide-react'
import { api } from '../api'
import SegmentControl from '../components/SegmentControl'

// ═══════════════════════════════════════════════════════════════
// Crystalline Literacy — Dashboard
// Design: warm indigo accent, paper-toned surfaces, deliberate rhythm
// All business logic preserved verbatim.
// ═══════════════════════════════════════════════════════════════

/** SVG Progress Ring — refined stroke & cap */
function ProgressRing({ percent, size = 140, strokeWidth = 6, children }) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (Math.min(100, percent) / 100) * circumference
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="var(--surface-tertiary)" strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="var(--accent)" strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.0s cubic-bezier(0.22, 0.61, 0.36, 1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">{children}</div>
    </div>
  )
}

/** GitHub-style contribution heatmap — 30 days, 7-row grid */
function Heatmap({ data }) {
  if (!data || data.length === 0) return null
  const maxCount = Math.max(1, ...data.map(d => d.count))
  const dayLabels = ['', '一', '', '三', '', '五', '']

  // Build columns: each column is one week (Sun-Sat), oldest first
  const cols = []
  let col = new Array(7).fill(null)
  for (let i = 0; i < data.length; i++) {
    const date = new Date(data[i].date)
    const dayOfWeek = date.getDay()  // 0=Sun, 1=Mon, ..., 6=Sat
    if (dayOfWeek === 0 && col.some(c => c !== null)) {
      cols.push(col)
      col = new Array(7).fill(null)
    }
    col[dayOfWeek] = data[i]
  }
  if (col.some(c => c !== null)) cols.push(col)

  const cellSize = 14
  const gap = 3

  return (
    <div className="overflow-x-auto" style={{ maxWidth: '100%' }}>
      <div style={{ display: 'flex', gap: `${gap}px` }}>
        {/* Day labels */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: `${gap}px`, marginRight: '4px' }}>
          {dayLabels.map((label, i) => (
            <span key={i} style={{
              width: `${cellSize}px`, height: `${cellSize}px`,
              fontSize: '9px', lineHeight: `${cellSize}px`,
              textAlign: 'center', color: 'var(--text-tertiary)',
            }}>{label}</span>
          ))}
        </div>
        {/* Week columns */}
        {cols.map((week, wi) => (
          <div key={wi} style={{ display: 'flex', flexDirection: 'column', gap: `${gap}px` }}>
            {week.map((d, di) => {
              if (!d) return <div key={di} style={{ width: cellSize, height: cellSize }} />
              const intensity = d.count / maxCount
              let bg
              if (d.count === 0) bg = 'var(--surface-tertiary)'
              else if (intensity < 0.25) bg = 'color-mix(in srgb, var(--accent) 22%, var(--surface-tertiary))'
              else if (intensity < 0.5) bg = 'color-mix(in srgb, var(--accent) 44%, var(--surface-tertiary))'
              else if (intensity < 0.75) bg = 'color-mix(in srgb, var(--accent) 68%, var(--surface-tertiary))'
              else bg = 'var(--accent)'
              return (
                <div key={di} className="rounded-sm transition-all duration-500" title={`${d.date}: ${d.count} 词`}
                  style={{ width: cellSize, height: cellSize, backgroundColor: bg, borderRadius: '3px' }} />
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [favorites, setFavorites] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const searchInputRef = useRef(null)
  const [animatedProgress, setAnimatedProgress] = useState(0)
  const progressRef = useRef(0)
  const [activeBook, setActiveBook] = useState(null)
  const bookIdRef = useRef(null)
  const [visible, setVisible] = useState(false)

  const fetchData = useCallback(async (bookId, silent = false) => {
    if (!silent) setLoading(true)
    else setError(null)
    try {
      const d = await api.getDashboard(bookId)
      setData(d)
      if (d.active_book) setActiveBook(d.active_book)
      progressRef.current = 0
      const target = d.progress_percent || 0
      const step = () => {
        progressRef.current = Math.min(target, progressRef.current + target / 30)
        setAnimatedProgress(progressRef.current)
        if (progressRef.current < target) requestAnimationFrame(step)
      }
      requestAnimationFrame(step)
    } catch (e) {
      if (!silent) setError('无法连接到服务器，请确保后端已启动。')
      console.error(e)
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    setVisible(true)
    api.getActiveBook().then(resp => {
      const bookId = resp.book?.id || null
      bookIdRef.current = bookId
      if (resp.book) setActiveBook(resp.book)
      fetchData(bookId)
    }).catch(() => fetchData(null))
    // Fetch favorites count
    api.getFavorites().then(setFavorites).catch(() => {})
  }, [])

  useEffect(() => {
    let refreshCounter = 0
    const interval = setInterval(async () => {
      try {
        const resp = await api.getActiveBook()
        const newBookId = resp.book?.id || null
        if (newBookId !== bookIdRef.current) {
          bookIdRef.current = newBookId
          setActiveBook(resp.book)
          fetchData(newBookId)
          refreshCounter = 0
        } else {
          refreshCounter++
          if (refreshCounter >= 5) {
            refreshCounter = 0
            fetchData(bookIdRef.current, true)
            api.getFavorites().then(setFavorites).catch(() => {})
          }
        }
      } catch (e) { /* ignore */ }
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 280)
    return () => clearTimeout(timer)
  }, [searchQuery])

  const doSearch = useCallback(async (q) => {
    if (!q.trim()) { setSearchResults(null); return }
    setSearchLoading(true)
    try {
      const result = await api.searchAll(q)
      setSearchResults(result)
    } catch (e) {
      console.error('Search error:', e)
    } finally {
      setSearchLoading(false)
    }
  }, [])

  useEffect(() => { doSearch(debouncedQuery) }, [debouncedQuery, doSearch])

  const clearSearch = () => {
    setSearchQuery('')
    setSearchResults(null)
    if (searchInputRef.current) searchInputRef.current.focus()
  }

  const speakWord = (word, lang = 'en-US') => {
    if (!window.speechSynthesis) return
    speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(word)
    utterance.lang = lang
    utterance.rate = 0.88
    speechSynthesis.speak(utterance)
  }

  const resultEmoji = (r) => {
    if (r === 'too_easy') return '⚡'
    if (r === 'know') return '✅'
    if (r === 'fuzzy') return '🤔'
    return '❌'
  }

  const formatTime = (mins) => {
    if (!mins || mins === 0) return '0 分钟'
    if (mins < 60) return `${mins} 分钟`
    const h = Math.floor(mins / 60)
    const m = mins % 60
    return m > 0 ? `${h} 小时 ${m} 分钟` : `${h} 小时`
  }

  const estDate = data?.est_completion_days
    ? new Date(Date.now() + data.est_completion_days * 86400000).toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })
    : null

  // ═══════════════════════════════════════
  // Loading State
  // ═══════════════════════════════════════
  if (loading) {
    return (
      <div className="page flex items-center justify-center min-h-[70vh]">
        <div className="flex flex-col items-center gap-5">
          <div className="w-10 h-10 rounded-full border-[2.5px] animate-spin"
            style={{ borderColor: 'var(--border)', borderTopColor: 'var(--accent)' }} />
          <p className="text-sm font-medium" style={{ color: 'var(--text-tertiary)' }}>正在准备你的学习数据...</p>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════
  // Error State
  // ═══════════════════════════════════════
  if (error) {
    return (
      <div className="page flex items-center justify-center min-h-[70vh]">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-5"
            style={{ backgroundColor: 'var(--surface-tertiary)' }}>
            <Sparkles size={28} style={{ color: 'var(--text-tertiary)' }} />
          </div>
          <p className="text-sm mb-5 leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{error}</p>
          <button onClick={() => fetchData(bookIdRef.current)}
            className="ios-button ios-button-secondary"
            style={{ borderRadius: 'var(--radius-md)' }}>重试</button>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════
  // Main Dashboard
  // ═══════════════════════════════════════
  return (
    <div className="page" style={{
      opacity: visible ? 1 : 0,
      transform: visible ? 'translateY(0)' : 'translateY(8px)',
      transition: 'opacity 0.5s ease, transform 0.5s cubic-bezier(0.22, 0.61, 0.36, 1)',
    }}>
      {/* ═══ Zone 1: Greeting ═══ */}
      <header style={{ marginBottom: '2.25rem' }}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[13px] font-medium tracking-wide mb-1"
              style={{ color: 'var(--text-tertiary)', letterSpacing: '0.03em', textTransform: 'uppercase' }}>
              {new Date().toLocaleDateString('zh-CN', { weekday: 'long', month: 'long', day: 'numeric' })}
            </p>
            <h1 className="text-[28px] font-bold tracking-tight"
              style={{ color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
              欢迎回来
            </h1>
          </div>
          {activeBook && (
            <button
              onClick={() => navigate('/dictionary')}
              title="管理词书"
              className="flex items-center gap-2 px-3.5 py-2 rounded-full transition-all duration-200 hover:opacity-80"
              style={{ backgroundColor: 'var(--accent-subtle)', border: '1px solid color-mix(in srgb, var(--accent) 18%, transparent)', cursor: 'pointer' }}>
              <BookOpen size={14} style={{ color: 'var(--accent)' }} />
              <span className="text-xs font-semibold" style={{ color: 'var(--accent)' }}>
                {activeBook.book_name || activeBook.name}
              </span>
            </button>
          )}
        </div>
      </header>

      {/* ═══ Zone 2: Progress Snapshot ═══ */}
      <section style={{ marginBottom: '2.25rem' }}>
        <div
          style={{
            backgroundColor: 'var(--surface-secondary)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-xl)',
            padding: '1.75rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)',
          }}
        >
          <div className="flex flex-col md:flex-row items-center gap-6">
            {/* Ring */}
            <div className="flex-shrink-0">
              <ProgressRing percent={animatedProgress} size={148} strokeWidth={5.5}>
                <span className="text-[32px] font-bold tracking-tight"
                  style={{ color: 'var(--text-primary)', letterSpacing: '-0.04em', lineHeight: 1 }}>
                  {Math.round(animatedProgress)}
                </span>
                <span className="text-[11px] font-medium mt-0.5" style={{ color: 'var(--text-tertiary)' }}>%</span>
              </ProgressRing>
            </div>

            {/* Stat tiles */}
            <div className="flex-1 grid grid-cols-2 gap-2.5 w-full">
              {[
                { icon: Target, label: '待复习', value: data?.active_book?.review_due ?? data?.today_words_count ?? 0, accent: 'var(--warning)' },
                { icon: BookOpen, label: '已学习', value: data?.active_book?.studied_count ?? 0, sub: ` / ${data?.total_words ?? 0}` },
                { icon: Timer, label: '今日学时', value: data?.today_minutes ?? 0, sub: ' 分钟' },
                { icon: Trophy, label: '已掌握', value: data?.total_mastered ?? 0, sub: ` / ${data?.total_words ?? 0}` },
              ].map((stat, idx) => {
                const Icon = stat.icon
                const isWarning = stat.label === '待复习' && stat.value > 0
                return (
                  <div key={idx}
                    style={{
                      backgroundColor: 'var(--surface)',
                      borderRadius: 'var(--radius-md)',
                      padding: '0.9rem 1rem',
                      border: '1px solid var(--border)',
                      borderLeft: isWarning ? `3px solid ${stat.accent}` : '3px solid transparent',
                      display: 'flex', flexDirection: 'column', gap: '0.35rem',
                      transition: 'border-color 0.3s ease, box-shadow 0.3s ease',
                    }}>
                    <div className="flex items-center gap-1.5">
                      <Icon size={13} style={{ color: isWarning ? stat.accent : 'var(--text-tertiary)' }} />
                      <span className="text-[11px] font-semibold tracking-wide"
                        style={{ color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>{stat.label}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.15rem' }}>
                      <span className="text-xl font-bold tracking-tight"
                        style={{ color: isWarning ? stat.accent : 'var(--text-primary)', letterSpacing: '-0.03em' }}>
                        {stat.value}
                      </span>
                      {stat.sub && (
                        <span className="text-[13px] font-medium" style={{ color: 'var(--text-tertiary)' }}>{stat.sub}</span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Subtle progress bar below ring */}
          <div style={{
            marginTop: '1.25rem',
            height: '4px',
            borderRadius: '100px',
            backgroundColor: 'var(--surface-tertiary)',
            overflow: 'hidden',
          }}>
            <div style={{
              height: '100%',
              borderRadius: '100px',
              backgroundColor: 'var(--accent)',
              width: `${Math.min(100, animatedProgress)}%`,
              transition: 'width 1.0s cubic-bezier(0.22, 0.61, 0.36, 1)',
            }} />
          </div>
          <p className="text-[11px] font-medium mt-2" style={{ color: 'var(--text-tertiary)' }}>
            {data?.total_mastered > 0
              ? `已掌握 ${data.total_mastered} 个单词 · 继续加油`
              : '开始学习，点滴积累成就词汇大师'}
          </p>
        </div>
      </section>

      {/* ═══ Zone 3: Search + Goal ═══ */}
      <section style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {/* Search */}
          <div className="relative">
            <Search size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
              style={{ color: 'var(--text-tertiary)' }} />
            <input ref={searchInputRef} type="text" value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索单词或释义..."
              className="input py-2.5 pl-10 pr-10 text-sm"
              style={{
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--surface-secondary)',
              }} />
            {searchQuery && (
              <button onClick={clearSearch}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 rounded-md transition-all hover:bg-[var(--surface-tertiary)]"
                style={{ color: 'var(--text-tertiary)' }}>
                <X size={15} />
              </button>
            )}
          </div>

          {/* Search results dropdown */}
          {searchQuery && (searchLoading || searchResults) && (
            <div className="rounded-xl overflow-hidden"
              style={{
                position: 'relative', zIndex: 20,
                backgroundColor: 'var(--surface-secondary)',
                border: '1px solid var(--border)',
                boxShadow: '0 16px 48px rgba(0,0,0,0.15)',
                maxHeight: '380px', overflowY: 'auto',
              }}>
              {searchLoading && (
                <div className="flex items-center gap-3 px-4 py-6 justify-center">
                  <div className="w-4 h-4 border-2 rounded-full animate-spin"
                    style={{ borderColor: 'var(--border)', borderTopColor: 'var(--accent)' }} />
                  <span className="text-sm" style={{ color: 'var(--text-tertiary)' }}>搜索中...</span>
                </div>
              )}
              {!searchLoading && searchResults && searchResults.total === 0 && (
                <div className="px-4 py-10 text-center">
                  <Search size={26} className="mx-auto mb-3" style={{ color: 'var(--text-tertiary)' }} />
                  <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>未找到 "{searchQuery}"</p>
                </div>
              )}
              {!searchLoading && searchResults && searchResults.total > 0 && (
                <div>
                  {searchResults.study_words?.length > 0 && (
                    <div>
                      <div className="px-4 py-2 text-[11px] font-semibold uppercase tracking-wider"
                        style={{ color: 'var(--text-tertiary)', backgroundColor: 'var(--surface)' }}>
                        学习词库 ({searchResults.study_words.length})
                      </div>
                      {searchResults.study_words.slice(0, 5).map((w) => (
                        <div key={`study-${w.id}`}
                          className="flex items-center justify-between px-4 py-2.5 cursor-pointer transition-all hover:bg-[var(--surface)]"
                          style={{ borderBottom: '1px solid var(--border)' }}
                          onClick={() => navigate(`/search?q=${encodeURIComponent(w.english)}`)}>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{w.english}</span>
                              <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{w.phonetic}</span>
                            </div>
                            <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--text-secondary)' }}>{w.chinese}</p>
                          </div>
                          <button onClick={(e) => { e.stopPropagation(); speakWord(w.english) }}
                            className="p-1.5 rounded-lg transition-all hover:bg-[var(--surface-tertiary)] ml-2"
                            style={{ color: 'var(--text-tertiary)' }}>
                            <Volume2 size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="px-4 py-2.5 text-xs text-center" style={{ color: 'var(--text-tertiary)' }}>
                    共 {searchResults.total} 个结果 ·{' '}
                    <span className="cursor-pointer font-medium hover:underline"
                      style={{ color: 'var(--accent)' }}
                      onClick={() => navigate(`/search?q=${encodeURIComponent(searchQuery)}`)}>查看全部 →</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Daily goal — inline compact */}
          <DailyGoalCompact />
        </div>
      </section>

      {/* ═══ Zone 4: Prediction Banner ═══ */}
      {estDate && data?.remaining_words > 0 && (
        <section style={{ marginBottom: '1.75rem' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.75rem',
            padding: '0.9rem 1.25rem',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--accent-subtle)',
            border: '1px solid color-mix(in srgb, var(--accent) 12%, transparent)',
          }}>
            <Calendar size={17} style={{ color: 'var(--accent)', flexShrink: 0 }} />
            <div>
              <p className="text-[13px] font-semibold" style={{ color: 'var(--text-primary)' }}>
                预计 {estDate} 完成全部学习
              </p>
              <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
                每日 {data.avg_daily_words} 词 · 还剩 {data.remaining_words} 词
              </p>
            </div>
          </div>
        </section>
      )}

      {/* ═══ Zone 5: Heatmap ═══ */}
      {data?.heatmap && data.heatmap.length > 0 && (
        <section style={{ marginBottom: '1.75rem' }}>
          <div style={{
            backgroundColor: 'var(--surface-secondary)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem 1.25rem 1rem',
          }}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[13px] font-semibold tracking-tight" style={{ color: 'var(--text-primary)' }}>学习热力图</h3>
              <span className="text-[11px] font-medium" style={{ color: 'var(--text-tertiary)' }}>
                累计 {formatTime(data.total_minutes)}
              </span>
            </div>
            <div className="flex justify-center">
              <Heatmap data={data.heatmap} />
            </div>
          </div>
        </section>
      )}

      {/* ═══ Zone 6: Primary Actions ═══ */}
      <section style={{ marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
        {/* Start Study — primary CTA */}
        <button onClick={() => navigate('/study')}
          style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.65rem',
            padding: '0.95rem 0', borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--accent)', color: '#fff',
            border: 'none', cursor: 'pointer',
            fontSize: '0.9375rem', fontWeight: 600, letterSpacing: '-0.01em',
            boxShadow: '0 2px 10px color-mix(in srgb, var(--accent) 35%, transparent)',
            transition: 'all 0.25s cubic-bezier(0.22, 0.61, 0.36, 1)',
          }}
          className="btn-hover-scale">
          <Zap size={19} />
          开始背单词
          <ArrowRight size={17} />
        </button>

        {/* ⭐ Favorites Card */}
        {favorites.length > 0 && (
          <button
            onClick={() => navigate('/favorites')}
            className="w-full text-left rounded-2xl p-4 transition-all duration-300 hover:-translate-y-0.5"
            style={{
              backgroundColor: 'var(--surface-secondary)',
              border: '1px solid var(--border)',
              boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
              cursor: 'pointer',
            }}>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: 'rgba(245,158,11,0.12)' }}>
                <Star size={18} style={{ color: '#f59e0b' }} fill="#f59e0b" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold tracking-tight" style={{ color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                  我的收藏
                </h3>
                <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
                  {favorites.length} 个单词 · {favorites.slice(0, 3).map(w => w.english).join('、')}{favorites.length > 3 ? '…' : ''}
                </p>
              </div>
              <ChevronRight size={16} style={{ color: 'var(--text-tertiary)' }} />
            </div>
          </button>
        )}

        {/* AI Tutor — secondary */}
        <button onClick={() => navigate('/ai-tutor')}
          style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.65rem',
            padding: '0.8rem 0', borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--surface-secondary)', color: 'var(--text-primary)',
            border: '1px solid var(--border)', cursor: 'pointer',
            fontSize: '0.8125rem', fontWeight: 600,
            transition: 'all 0.25s cubic-bezier(0.22, 0.61, 0.36, 1)',
          }}
          className="btn-hover-scale">
          <Sparkles size={16} style={{ color: 'var(--accent)' }} />
          AI Tutor · 英语学习助手
          <ChevronRight size={14} style={{ color: 'var(--text-tertiary)' }} />
        </button>

      </section>

      {/* ═══ Zone: 词书管理 Card ═══ */}
      <section style={{ marginBottom: '1.5rem' }}>
        <button
          onClick={() => navigate('/dictionary')}
          className="w-full text-left rounded-2xl p-5 transition-all duration-300 hover:-translate-y-0.5"
          style={{
            backgroundColor: 'var(--surface-secondary)',
            border: '1px solid var(--border)',
            boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
            cursor: 'pointer',
          }}>
          <div className="flex items-center gap-4">
            {/* Icon */}
            <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: 'var(--accent-subtle)' }}>
              <BookOpen size={20} style={{ color: 'var(--accent)' }} />
            </div>
            {/* Content */}
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-bold tracking-tight mb-0.5" style={{ color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                词书管理
              </h3>
              <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                {activeBook
                  ? `当前：${activeBook.book_name}`
                  : '选择当前学习词书'}
              </p>
            </div>
            {/* Arrow */}
            <ChevronRight size={18} style={{ color: 'var(--text-tertiary)' }} />
          </div>
          {/* Sub-labels */}
          <div className="flex gap-2 mt-3">
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'var(--surface-tertiary)', color: 'var(--text-tertiary)' }}>
              导入词书
            </span>
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'var(--surface-tertiary)', color: 'var(--text-tertiary)' }}>
              切换词书
            </span>
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'var(--surface-tertiary)', color: 'var(--text-tertiary)' }}>
              管理词书
            </span>
          </div>
        </button>
      </section>

      {/* ═══ Zone 7: Recent Activity ═══ */}
      {data?.recent_records && data.recent_records.length > 0 && (
        <section style={{ marginBottom: '2rem' }}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[13px] font-semibold tracking-tight" style={{ color: 'var(--text-primary)' }}>最近学习记录</h3>
            <button onClick={() => navigate('/analytics')}
              className="text-[12px] font-medium flex items-center gap-1 transition-all hover:opacity-70"
              style={{ color: 'var(--text-tertiary)' }}>
              查看全部 <ChevronRight size={11} />
            </button>
          </div>
          <div className="rounded-xl overflow-hidden" style={{
            backgroundColor: 'var(--surface-secondary)',
            border: '1px solid var(--border)',
          }}>
            {data.recent_records.slice(0, 8).map((rec, i) => (
              <div key={i} className="flex items-center justify-between px-4 py-2.5 transition-all hover:bg-[var(--surface)]"
                style={{ borderBottom: i < Math.min(data.recent_records.length, 8) - 1 ? '1px solid var(--border)' : 'none' }}>
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-sm flex-shrink-0">{resultEmoji(rec.result)}</span>
                  <span className="text-[13px] font-semibold flex-shrink-0" style={{ color: 'var(--text-primary)' }}>{rec.word}</span>
                  <span className="text-xs truncate" style={{ color: 'var(--text-tertiary)' }}>{rec.chinese}</span>
                </div>
                <Clock size={12} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ═══ Zone 8: Learning Tip ═══ */}
      <div style={{
        marginBottom: '1.5rem',
        padding: '1rem 1.25rem',
        borderRadius: 'var(--radius-md)',
        backgroundColor: 'var(--surface-tertiary)',
        fontSize: '0.75rem', lineHeight: 1.7,
        color: 'var(--text-tertiary)',
      }}>
        <span className="font-semibold" style={{ color: 'var(--text-secondary)' }}>💡 学习提示 </span>
        系统使用艾宾浩斯记忆曲线自动安排复习。标记"认识"的单词将间隔更长时间出现，"不认识"的单词会高频复习，直到你掌握为止。
      </div>

      {/* ═══ Version ═══ */}
      <div className="text-center pb-6">
        <span className="text-[11px] font-medium tracking-wider"
          style={{ color: 'var(--text-tertiary)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
          WordMaster v0.1.0 Beta
        </span>
      </div>
    </div>
  )

  // ═══════════════════════════════════════
  // Inline sub-component: compact daily goal
  // ═══════════════════════════════════════
  function DailyGoalCompact() {
    const [goal, setGoal] = useState(() => {
      const saved = localStorage.getItem('wordmaster-daily-goal')
      return saved ? parseInt(saved, 10) : 20
    })
    const options = [10, 20, 30, 50, 100]

    const handleChange = (value) => {
      setGoal(value)
      localStorage.setItem('wordmaster-daily-goal', String(value))
    }

    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.65rem',
        padding: '0.6rem 1rem',
        borderRadius: 'var(--radius-md)',
        backgroundColor: 'var(--surface-secondary)',
        border: '1px solid var(--border)',
      }}>
        <span className="text-[11px] font-semibold tracking-wide flex-shrink-0"
          style={{ color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>每日目标</span>
        <SegmentControl
          options={options.map(String)}
          value={String(goal)}
          onChange={v => handleChange(parseInt(v))}
          size="sm"
        />
      </div>
    )
  }
}
