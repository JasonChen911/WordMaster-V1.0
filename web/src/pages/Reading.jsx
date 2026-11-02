import { useState, useRef, useEffect } from 'react'
import { ArrowLeft, Sparkles, BookOpen, Loader2, Volume2, ChevronDown, ChevronUp, Shuffle, Check, X, Search, PlusCircle, CheckCircle2, Pause, Square, Play } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import SegmentControl from '../components/SegmentControl'
import { api } from '../api'
import { speakWord as pronounceWord, getAccent } from '../tts'
import { ReadingPlayer } from '../readingPlayer'

const EXAMS = [
  { id: '高中英语', label: '高中英语' },
  { id: 'CET-4', label: '大学四级 CET-4' },
  { id: 'CET-6', label: '大学六级 CET-6' },
  { id: 'IELTS', label: '雅思 IELTS' },
  { id: 'TOEFL', label: '托福 TOEFL' },
  { id: '日常英语', label: '日常英语' },
]
const LEVELS = ['简单', '中等', '困难', '专家']
const TOPICS = ['科技','人工智能','历史','文化','自然','环境','心理学','商业','经济','教育','社会','健康','旅行','体育','文学','未来科技']
const WORD_COUNTS = [
  { label: '短 · 300词', value: 300 },
  { label: '中 · 500词', value: 500 },
  { label: '长 · 800词', value: 800 },
  { label: '挑战 · 1200词', value: 1200 },
]

/* ── Custom Dropdown — Crystalline glass style ── */
function Dropdown({ value, onChange, options, label }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  useEffect(() => {
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', h); return () => document.removeEventListener('mousedown', h)
  }, [])
  const selected = options.find(o => o.id === value)
  return (
    <div ref={ref} style={{ position: 'relative', flex: 1 }}>
      <label className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>{label}</label>
      <button onClick={() => setOpen(!open)}
        style={{
          width: '100%', marginTop: 4, padding: '0.5rem 0.75rem',
          borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)', color: 'var(--text-primary)',
          fontSize: '0.8125rem', fontFamily: 'inherit', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          transition: 'all 0.2s ease',
        }}>
        <span>{selected?.label || value}</span>
        <ChevronDown size={14} style={{
          color: 'var(--text-tertiary)',
          transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.25s ease',
        }} />
      </button>
      {open && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 50, marginTop: 4,
          borderRadius: 'var(--radius-md)', backgroundColor: 'var(--surface-secondary)',
          border: '1px solid var(--border)',
          boxShadow: '0 12px 40px rgba(0,0,0,0.10)',
          overflow: 'hidden',
          animation: 'dropdownIn 0.25s cubic-bezier(0.22, 0.61, 0.36, 1) forwards',
        }}>
          {options.map(o => (
            <button key={o.id} onClick={() => { onChange(o.id); setOpen(false) }}
              style={{
                width: '100%', padding: '0.55rem 0.75rem', textAlign: 'left',
                border: 'none', borderBottom: '1px solid var(--border)',
                backgroundColor: value === o.id ? 'var(--accent-subtle)' : 'transparent',
                color: value === o.id ? 'var(--accent)' : 'var(--text-primary)',
                fontSize: '0.8125rem', fontFamily: 'inherit', cursor: 'pointer',
                fontWeight: value === o.id ? 600 : 400,
                transition: 'background-color 0.15s ease',
              }}
              onMouseEnter={e => { if (value !== o.id) e.target.style.backgroundColor = 'var(--surface-tertiary)' }}
              onMouseLeave={e => { if (value !== o.id) e.target.style.backgroundColor = 'transparent' }}>
              {o.label}
              {value === o.id && <Check size={12} style={{ marginLeft: 6, display: 'inline', color: 'var(--accent)' }} />}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Reading() {
  const navigate = useNavigate()
  const [exam, setExam] = useState('CET-4')
  const [level, setLevel] = useState('中等')
  const [topic, setTopic] = useState('科技')
  const [words, setWords] = useState(500)
  const [loading, setLoading] = useState(false)
  const [article, setArticle] = useState(null)
  const [error, setError] = useState(null)
  const [fontSize, setFontSize] = useState(16)
  const [selectedVocab, setSelectedVocab] = useState(null)
  const [showVocab, setShowVocab] = useState(false)
  // Quiz state
  const [userAnswers, setUserAnswers] = useState({})
  const [showReview, setShowReview] = useState(false)
  const [addedWords, setAddedWords] = useState(() => new Set())
  const allDone = article?.questions?.length > 0 && article.questions.every(q => userAnswers[q.question] != null)

  // ── Long-form reading player (state machine: IDLE/LOADING/PLAYING/PAUSED/…) ──
  const playerRef = useRef(null)
  const [reading, setReading] = useState({ state: 'IDLE', index: 0, total: 0 })
  useEffect(() => {
    const player = new ReadingPlayer()
    player.setVoice(getAccent())
    playerRef.current = player
    const unsub = player.subscribe((s) => setReading(s))
    return () => { unsub(); player.stop() }
  }, [])

  const addWordToStudy = async (v) => {
    if (addedWords.has(v.word)) return
    try {
      await api.addReadingWord(v.word, v.meaning, v.example || '', article?.title || 'AI 阅读', '')
      setAddedWords((prev) => new Set(prev).add(v.word))
    } catch (e) {
      console.error('add word failed', e)
    }
  }

  const randomTopic = () => {
    const others = TOPICS.filter(t => t !== topic)
    setTopic(others[Math.floor(Math.random() * others.length)])
  }

  const handleGenerate = async () => {
    setLoading(true); setError(null); setArticle(null)
    setUserAnswers({}); setShowReview(false)
    try {
      const r = await fetch('/api/ai/generate-reading', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exam, level, topic, words }),
      })
      const d = await r.json()
      if (d.error) { setError(d.error) }
      else { setArticle(d); setShowVocab(false); setSelectedVocab(null) }
    } catch (e) { setError('网络错误，请检查连接。') }
    finally { setLoading(false) }
  }

  const speakWord = (word) => {
    if (!word) return
    pronounceWord(word)
  }

  const startReading = () => {
    if (!article?.content || !playerRef.current) return
    playerRef.current.play(article.content)
  }

  const togglePause = () => {
    const p = playerRef.current
    if (!p) return
    if (p.state === 'PLAYING' || p.state === 'LOADING') p.pause()
    else if (p.state === 'PAUSED') p.resume()
    else startReading()
  }

  const stopReading = () => playerRef.current?.stop()

  const selectAnswer = (qText, letter) => {
    if (showReview) return
    setUserAnswers(prev => ({ ...prev, [qText]: letter }))
  }

  const correctCount = article?.questions
    ? article.questions.filter(q => userAnswers[q.question] === q.answer).length
    : 0

  return (
    <div className="page" style={{ maxWidth: 760, animation: 'fadeSlideIn 0.35s ease forwards' }}>
      <style>{`
        @keyframes dropdownIn {
          from { opacity: 0; transform: translateY(-8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes reviewIn {
          from { opacity: 0; max-height: 0; }
          to   { opacity: 1; max-height: 2000px; }
        }
      `}</style>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1.5rem' }}>
        <button onClick={() => navigate('/')} className="ios-icon-button"><ArrowLeft size={19} /></button>
        <div>
          <h1 className="text-lg font-bold tracking-tight" style={{ color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>AI 阅读</h1>
          <p className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>生成专属英语阅读材料 · 智能出题 · 详细解析</p>
        </div>
      </div>

      {/* Config card */}
      <div style={{
        backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-xl)', padding: '1.25rem', marginBottom: '1.25rem',
        animation: 'fadeSlideIn 0.4s 0.05s ease both',
      }}>
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <Dropdown value={exam} onChange={setExam} options={EXAMS} label="考试类型" />
          <div style={{ flex: 1 }}>
            <label className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>难度</label>
            <div style={{ marginTop: 4 }}>
              <SegmentControl options={LEVELS} value={level} onChange={setLevel} size="sm" />
            </div>
          </div>
        </div>

        <div style={{ marginBottom: '0.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>主题</label>
            <button onClick={randomTopic}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 2, fontSize: '0.625rem', fontWeight: 600 }}>
              <Shuffle size={10} />随机
            </button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginTop: 4 }}>
            {TOPICS.map(t => (
              <button key={t} onClick={() => setTopic(t)}
                style={{
                  padding: '0.25rem 0.55rem', borderRadius: 'var(--radius-sm)',
                  backgroundColor: topic === t ? 'var(--accent-subtle)' : 'var(--surface)',
                  color: topic === t ? 'var(--accent)' : 'var(--text-secondary)',
                  border: topic === t ? '1px solid var(--accent)' : '1px solid var(--border)',
                  cursor: 'pointer', fontSize: '0.625rem', fontWeight: 500,
                  transition: 'all 0.2s cubic-bezier(0.22, 0.61, 0.36, 1)',
                }}>{t}</button>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <SegmentControl
            options={WORD_COUNTS.map(w => w.label)}
            value={WORD_COUNTS.find(w => w.value === words)?.label || '中 · 500词'}
            onChange={label => setWords(WORD_COUNTS.find(w => w.label === label)?.value || 500)}
            size="sm"
          />
        </div>

        <button onClick={handleGenerate} disabled={loading}
          style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
            padding: '0.7rem', borderRadius: 'var(--radius-md)',
            backgroundColor: loading ? 'var(--surface-tertiary)' : 'var(--accent)',
            color: loading ? 'var(--text-tertiary)' : '#fff', border: 'none',
            cursor: loading ? 'wait' : 'pointer', fontSize: '0.875rem', fontWeight: 600,
            transition: 'all 0.25s cubic-bezier(0.22, 0.61, 0.36, 1)',
            boxShadow: loading ? 'none' : '0 2px 8px color-mix(in srgb, var(--accent) 30%, transparent)',
            transform: loading ? 'none' : undefined,
          }}
          className={loading ? '' : 'btn-hover-scale'}>
          {loading ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
          {loading ? 'AI 正在准备你的阅读材料...' : '生成文章'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{ padding: '1rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--danger-subtle)', border: '1px solid var(--danger)', color: 'var(--danger)', fontSize: '0.8125rem', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {/* Article display */}
      {article && !loading && (
        <div style={{
          backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-xl)', padding: '1.5rem',
          animation: 'fadeSlideIn 0.4s ease forwards',
        }}>
          <h2 className="text-xl font-bold mb-4 tracking-tight" style={{ color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            {article.title}
          </h2>

          {/* Font controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--surface-tertiary)' }}>
            <span className="text-[10px] font-semibold uppercase" style={{ color: 'var(--text-tertiary)' }}>Aa</span>
            <input type="range" min={14} max={22} value={fontSize} onChange={e => setFontSize(parseInt(e.target.value))}
              style={{ flex: 1, accentColor: 'var(--accent)' }} />
            <span className="text-[10px]" style={{ color: 'var(--text-tertiary)' }}>{fontSize}px</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              {reading.state === 'PLAYING' || reading.state === 'LOADING' ? (
                <button onClick={togglePause} title="暂停"
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 3, fontSize: '0.6875rem', fontWeight: 600 }}>
                  <Pause size={14} />暂停
                </button>
              ) : (
                <button onClick={togglePause} title={reading.state === 'PAUSED' ? '继续' : '朗读'}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 3, fontSize: '0.6875rem', fontWeight: 600 }}>
                  {reading.state === 'PAUSED' ? <Play size={14} /> : <Volume2 size={14} />}
                  {reading.state === 'PAUSED' ? '继续' : '朗读'}
                </button>
              )}
              {(reading.state === 'PLAYING' || reading.state === 'PAUSED' || reading.state === 'LOADING') && (
                <button onClick={stopReading} title="停止"
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 3, fontSize: '0.6875rem', fontWeight: 600 }}>
                  <Square size={13} />停止
                </button>
              )}
            </div>
          </div>

          {/* Content */}
          <div style={{ fontSize: `${fontSize}px`, lineHeight: 1.8, color: 'var(--text-primary)', whiteSpace: 'pre-wrap', marginBottom: '1.5rem' }}>
            {article.content}
          </div>

          {/* Vocabulary */}
          {article.vocabulary?.length > 0 && (
            <div style={{ marginBottom: '1.25rem' }}>
              <button onClick={() => setShowVocab(!showVocab)}
                style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 600, marginBottom: showVocab ? '0.65rem' : 0 }}>
                <BookOpen size={14} style={{ color: 'var(--accent)' }} />
                重点词汇 ({article.vocabulary.length})
                {showVocab ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              </button>
              {showVocab && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                  {article.vocabulary.map((v, i) => (
                    <button key={i} onClick={() => { setSelectedVocab(v); speakWord(v.word) }}
                      style={{
                        padding: '0.35rem 0.65rem', borderRadius: 'var(--radius-sm)',
                        backgroundColor: selectedVocab?.word === v.word ? 'var(--accent-subtle)' : 'var(--surface-tertiary)',
                        border: selectedVocab?.word === v.word ? '1px solid var(--accent)' : '1px solid var(--border)',
                        cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600,
                        color: 'var(--text-primary)', transition: 'all 0.2s ease',
                      }}>
                      {v.word}
                      <span style={{ color: 'var(--text-tertiary)', fontWeight: 400, marginLeft: 4 }}>{v.meaning}</span>
                    </button>
                  ))}
                </div>
              )}
              {selectedVocab && showVocab && (
                <div style={{ marginTop: '0.5rem', padding: '0.75rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.875rem' }}>{selectedVocab.word}</span>
                      <button onClick={() => speakWord(selectedVocab.word)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)' }}><Volume2 size={13} /></button>
                    </div>
                    <button onClick={() => addWordToStudy(selectedVocab)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: '0.3rem',
                        padding: '0.25rem 0.65rem', borderRadius: 'var(--radius-sm)', fontSize: '0.6875rem', fontWeight: 600,
                        backgroundColor: addedWords.has(selectedVocab.word) ? 'var(--success-subtle)' : 'var(--accent-subtle)',
                        color: addedWords.has(selectedVocab.word) ? 'var(--success)' : 'var(--accent)',
                        border: '1px solid ' + (addedWords.has(selectedVocab.word) ? 'var(--success)' : 'var(--accent)'),
                        cursor: addedWords.has(selectedVocab.word) ? 'default' : 'pointer',
                      }}>
                      {addedWords.has(selectedVocab.word) ? <CheckCircle2 size={12} /> : <PlusCircle size={12} />}
                      {addedWords.has(selectedVocab.word) ? '已加入' : '加入生词'}
                    </button>
                  </div>
                  <p className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>{selectedVocab.meaning}</p>
                  {selectedVocab.example && <p className="text-xs italic" style={{ color: 'var(--text-tertiary)' }}>"{selectedVocab.example}"</p>}
                </div>
              )}
            </div>
          )}

          {/* ── Quiz section: no answers shown ── */}
          {article.questions?.length > 0 && (
            <div style={{ marginBottom: showReview ? '1rem' : '0.5rem' }}>
              <h3 className="text-sm font-bold mb-3" style={{ color: 'var(--text-primary)' }}>
                阅读理解 ({article.questions.length} 题)
                {allDone && !showReview && <span style={{ color: 'var(--success)', fontWeight: 600, fontSize: '0.6875rem', marginLeft: 8 }}>已全部作答</span>}
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                {article.questions.map((q, qi) => {
                  const chosen = userAnswers[q.question]
                  return (
                    <div key={qi} style={{ padding: '0.85rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}>
                      <p className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>{qi + 1}. {q.question}</p>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        {q.options?.map((opt, oi) => {
                          const letter = String.fromCharCode(65 + oi)
                          const isChosen = chosen === letter
                          const isCorrect = showReview && letter === q.answer
                          const isWrong = showReview && isChosen && letter !== q.answer
                          let bg = 'transparent'
                          if (showReview && isCorrect) bg = 'var(--success-subtle)'
                          else if (isWrong) bg = 'var(--danger-subtle)'
                          else if (isChosen) bg = 'var(--accent-subtle)'
                          return (
                            <button key={oi} onClick={() => selectAnswer(q.question, letter)}
                              style={{
                                padding: '0.35rem 0.6rem', borderRadius: 'var(--radius-sm)',
                                backgroundColor: bg,
                                color: showReview && isCorrect ? 'var(--success)' : showReview && isWrong ? 'var(--danger)' : isChosen ? 'var(--accent)' : 'var(--text-secondary)',
                                border: isChosen && !showReview ? '1.5px solid var(--accent)' : '1px solid transparent',
                                fontSize: '0.75rem', fontWeight: isChosen ? 600 : 400,
                                cursor: showReview ? 'default' : 'pointer',
                                textAlign: 'left', fontFamily: 'inherit',
                                transition: 'all 0.2s ease',
                                display: 'flex', alignItems: 'center', gap: '0.35rem',
                              }}
                              onMouseEnter={e => { if (!showReview && !isChosen) { e.target.style.backgroundColor = 'var(--surface-tertiary)'; e.target.style.borderColor = 'var(--border)' } }}
                              onMouseLeave={e => { if (!showReview && !isChosen) { e.target.style.backgroundColor = 'transparent'; e.target.style.borderColor = 'transparent' } }}>
                              {showReview && isCorrect && <Check size={13} />}
                              {isWrong && <X size={13} />}
                              {letter}. {opt}
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* ── Review button ── */}
          {allDone && !showReview && (
            <button onClick={() => setShowReview(true)}
              style={{
                width: '100%', padding: '0.65rem', borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--success)', color: '#fff', border: 'none',
                cursor: 'pointer', fontSize: '0.8125rem', fontWeight: 600,
                transition: 'all 0.25s ease',
                boxShadow: '0 2px 8px color-mix(in srgb, var(--success) 30%, transparent)',
              }}
              className="btn-hover-scale">
              <Search size={15} style={{ marginRight: 6, display: 'inline' }} />
              查看答案与解析
            </button>
          )}

          {/* ── Review panel ── */}
          {showReview && (
            <div style={{
              overflow: 'hidden',
              animation: 'reviewIn 0.5s cubic-bezier(0.22, 0.61, 0.36, 1) forwards',
            }}>
              <div style={{
                marginTop: '1rem', padding: '1.25rem', borderRadius: 'var(--radius-lg)',
                backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
                borderLeft: '4px solid var(--accent)',
              }}>
                <h3 className="text-sm font-bold mb-3" style={{ color: 'var(--text-primary)' }}>
                  📖 阅读解析
                </h3>
                {/* Score */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 800, color: correctCount === article.questions.length ? 'var(--success)' : 'var(--accent)' }}>
                    {correctCount}/{article.questions.length}
                  </div>
                  <div>
                    <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                      {correctCount === article.questions.length ? '全部正确！' : correctCount >= article.questions.length / 2 ? '做得不错！' : '继续加油！'}
                    </p>
                    <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                      正确率 {Math.round((correctCount / article.questions.length) * 100)}%
                    </p>
                  </div>
                </div>

                {/* Per-question explanations */}
                {article.questions.map((q, qi) => {
                  const chosen = userAnswers[q.question]
                  const isCorrect = chosen === q.answer
                  return (
                    <div key={qi} style={{
                      marginBottom: '0.75rem', padding: '0.85rem', borderRadius: 'var(--radius-md)',
                      backgroundColor: isCorrect ? 'var(--success-subtle)' : 'var(--danger-subtle)',
                      border: `1px solid ${isCorrect ? 'var(--success)' : 'var(--danger)'}`,
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                        {isCorrect ? <Check size={14} style={{ color: 'var(--success)' }} /> : <X size={14} style={{ color: 'var(--danger)' }} />}
                        <span className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>Q{qi + 1}: {q.question.slice(0, 60)}...</span>
                      </div>
                      <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                        你的答案: <span style={{ fontWeight: 700, color: isCorrect ? 'var(--success)' : 'var(--danger)' }}>{chosen || '未作答'}</span>
                        {!isCorrect && <span> · 正确答案: <span style={{ fontWeight: 700, color: 'var(--success)' }}>{q.answer}</span></span>}
                      </p>
                      {q.explanation && (
                        <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)', fontStyle: 'italic' }}>
                          💡 {q.explanation}
                        </p>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
