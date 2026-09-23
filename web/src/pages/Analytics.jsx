import { useState, useEffect } from 'react'
import {
  TrendingUp, Target, Flame, BookOpen, AlertTriangle,
  RefreshCw, Sparkles, Brain, Clock, Trophy, Zap, ListOrdered, Dumbbell,
} from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, AreaChart, Area,
} from 'recharts'
import { api } from '../api'
import Modal from '../components/Modal'

export default function Analytics() {
  const [stats, setStats] = useState(null)
  const [weekly, setWeekly] = useState([])
  const [insights, setInsights] = useState(null)
  const [confusion, setConfusion] = useState([])
  const [aiInsights, setAiInsights] = useState(null)
  const [loading, setLoading] = useState(true)

  // Per-word diagnosis state
  const [diagnosing, setDiagnosing] = useState(null)
  const [diagnosis, setDiagnosis] = useState(null)

  // Exercise state
  const [exercises, setExercises] = useState(null)
  const [exerciseLoading, setExerciseLoading] = useState(false)
  const [exerciseType, setExerciseType] = useState('multiple_choice')
  const [exerciseAnswers, setExerciseAnswers] = useState({})

  const [aiLoading, setAiLoading] = useState(false)

  const load = () => {
    setLoading(true)
    Promise.all([
      api.getStats(),
      api.getWeeklyStats(),
      api.getInsights(),
      api.getConfusionSets(),
    ])
      .then(([s, w, i, c]) => {
        setStats(s)
        setWeekly(w)
        setInsights(i)
        setConfusion(c.sets || [])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleAIInsights = async () => {
    setAiLoading(true)
    try {
      const r = await api.getAIInsights()
      setAiInsights(r)
    } catch (e) {
      setAiInsights({ ai_available: false, insight: 'AI 分析失败，请检查 API 配置。', highlights: [] })
    } finally { setAiLoading(false) }
  }

  const handleDiagnose = async (word) => {
    setDiagnosing(word)
    setDiagnosis(null)
    try {
      const r = await api.analyzeWordStruggle(word.english, {})
      setDiagnosis({ ...r, word: word.english, chinese: word.chinese })
    } catch (e) {
      setDiagnosis({ word: word.english, chinese: word.chinese, ai_available: false, diagnosis: '诊断失败，请稍后重试。', suggestions: [], mistake_pattern: '', practice_sentence: '' })
    } finally { setDiagnosing(null) }
  }

  const handleGenerateExercises = async () => {
    if (!insights?.weak_words?.length) return
    setExerciseLoading(true); setExercises(null); setExerciseAnswers({})
    try {
      const r = await api.generateExercises(
        insights.weak_words.slice(0, 8).map((w) => ({ english: w.english, chinese: w.chinese })),
        exerciseType,
        5
      )
      setExercises(r)
    } catch (e) {
      setExercises({ questions: [], ai_available: false })
    } finally { setExerciseLoading(false) }
  }

  const toggleConfusion = async (s) => {
    try {
      await api.toggleConfusion(s.id)
      setConfusion((prev) => prev.map((x) => x.id === s.id ? { ...x, mastered: !x.mastered } : x))
    } catch (e) { /* ignore */ }
  }

  if (loading) {
    return (
      <div className="page flex items-center justify-center min-h-[70vh]">
        <RefreshCw size={28} className="animate-spin" style={{ color: 'var(--text-tertiary)' }} />
      </div>
    )
  }

  const todayAccuracy = stats?.today_total ? Math.round((stats.today_correct / stats.today_total) * 100) : 0
  const d7 = insights?.last_7_days || {}
  const proficiencyData = stats?.proficiency_distribution
    ? Object.entries(stats.proficiency_distribution).map(([level, count]) => ({ level: `Lv${level}`, count }))
    : []

  return (
    <div className="page animate-fade-in">
      <h1 className="text-2xl font-bold tracking-tight mb-1" style={{ color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
        学习分析
      </h1>
      <p className="text-sm mb-8" style={{ color: 'var(--text-tertiary)' }}>
        真实学习数据 · AI 洞察 · 针对性练习
      </p>

      {/* ═══ 7-day real stats ═══ */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-8">
        <StatCard icon={BookOpen} label="7天学习" value={d7.words_studied ?? 0} color="var(--accent)" />
        <StatCard icon={RefreshCw} label="7天复习" value={d7.reviews ?? 0} color="var(--text-tertiary)" />
        <StatCard icon={TrendingUp} label="平均正确率" value={`${Math.round((d7.avg_accuracy ?? 0) * 100)}%`} color="var(--success)" />
        <StatCard icon={AlertTriangle} label="遗忘率" value={`${Math.round((d7.forgetting_rate ?? 0) * 100)}%`} color="var(--danger)" />
        <StatCard icon={Clock} label="学习时长" value={`${d7.minutes ?? 0}分`} color="var(--warning)" />
      </div>

      {/* ═══ Weekly trend ═══ */}
      <div className="card mb-6">
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>📈 近7天学习趋势</h3>
        {weekly.some(d => d.words_studied > 0) ? (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={weekly} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
              <defs>
                <linearGradient id="colorStudied" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--text-tertiary)' }} tickFormatter={(d) => d.slice(5)} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-tertiary)' }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '12px', fontSize: '12px', color: 'var(--text-primary)' }} />
              <Area type="monotone" dataKey="words_studied" stroke="var(--accent)" strokeWidth={2} fill="url(#colorStudied)" name="学习单词" />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-sm text-center py-8" style={{ color: 'var(--text-tertiary)' }}>还没有学习数据</p>
        )}
      </div>

      {/* ═══ AI 学习洞察 ═══ */}
      <div className="card mb-6" style={{ borderColor: 'var(--accent)', borderWidth: '1.5px' }}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Brain size={15} style={{ color: 'var(--accent)' }} />
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>AI 学习洞察</h3>
          </div>
          {!aiInsights && (
            <button onClick={handleAIInsights} disabled={aiLoading} className="btn-ghost text-xs gap-1 py-1.5 px-3">
              <Sparkles size={13} />
              {aiLoading ? '分析中…' : '生成洞察'}
            </button>
          )}
        </div>
        {aiInsights?.ai_available ? (
          <div>
            <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--text-secondary)' }}>{aiInsights.insight}</p>
            {aiInsights.highlights?.length > 0 && (
              <div className="space-y-1.5">
                {aiInsights.highlights.map((h, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span style={{ color: 'var(--accent)', fontSize: '0.8rem' }}>•</span>
                    <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{h}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : aiInsights ? (
          <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>{aiInsights.insight || '暂无洞察。'}</p>
        ) : (
          <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
            点击「生成洞察」，AI 将基于你的真实学习数据（而非凭空统计）给出分析。
          </p>
        )}
      </div>

      {/* ═══ FSRS 高风险词汇 ═══ */}
      <div className="card mb-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle size={15} style={{ color: 'var(--warning)' }} />
          <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
            FSRS 高风险词汇（{insights?.high_risk_words?.length ?? 0}）
          </h3>
        </div>
        {(insights?.high_risk_words?.length ?? 0) === 0 ? (
          <p className="text-sm text-center py-4" style={{ color: 'var(--text-tertiary)' }}>暂无高风险词汇，继续保持！</p>
        ) : (
          <div className="space-y-1.5 max-h-56 overflow-y-auto">
            {insights.high_risk_words.map((w) => (
              <div key={w.id} className="flex items-center justify-between py-2 px-3 rounded-lg" style={{ backgroundColor: 'var(--surface-tertiary)' }}>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{w.english}</span>
                  <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{w.chinese}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs" style={{ color: 'var(--warning)' }}>保持率 {Math.round((w.retrievability || 0) * 100)}%</span>
                  <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: 'var(--danger-subtle)', color: 'var(--danger)' }}>忘 {w.lapses} 次</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ═══ 薄弱词汇 + 为什么总记不住 ═══ */}
      <div className="card mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Target size={15} style={{ color: 'var(--danger)' }} />
          <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
            薄弱词汇（{insights?.weak_words?.length ?? 0}）— 点击「分析」看错因
          </h3>
        </div>
        {(insights?.weak_words?.length ?? 0) === 0 ? (
          <p className="text-sm text-center py-4" style={{ color: 'var(--text-tertiary)' }}>🎉 还没有薄弱词汇，继续学习吧！</p>
        ) : (
          <div className="space-y-1.5 max-h-64 overflow-y-auto">
            {insights.weak_words.map((w) => (
              <div key={w.id} className="flex items-center justify-between py-2 px-3 rounded-lg" style={{ backgroundColor: 'var(--surface-tertiary)' }}>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{w.english}</span>
                  <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{w.chinese}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: 'var(--danger-subtle)', color: 'var(--danger)' }}>错 {w.wrong_count} 次</span>
                  <button onClick={() => handleDiagnose(w)} disabled={diagnosing?.english === w.english}
                    className="btn-ghost text-xs gap-1 py-1 px-2">
                    {diagnosing?.english === w.english ? <RefreshCw size={12} className="animate-spin" /> : <Brain size={12} />}
                    分析
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ═══ AI 针对性练习 ═══ */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Dumbbell size={15} style={{ color: 'var(--accent)' }} />
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>AI 针对性练习</h3>
          </div>
          {!exercises && (insights?.weak_words?.length ?? 0) > 0 && (
            <button onClick={handleGenerateExercises} disabled={exerciseLoading} className="btn-ghost text-xs gap-1 py-1.5 px-3">
              {exerciseLoading ? <RefreshCw size={13} className="animate-spin" /> : <Zap size={13} />}
              {exerciseLoading ? '生成中…' : '生成练习'}
            </button>
          )}
        </div>
        {!exercises && (insights?.weak_words?.length ?? 0) === 0 && (
          <p className="text-sm text-center py-4" style={{ color: 'var(--text-tertiary)' }}>学习后出现薄弱词，即可生成针对性练习。</p>
        )}
        {exercises && (
          <div>
            {!exercises.ai_available && (
              <p className="text-xs mb-2" style={{ color: 'var(--warning)' }}>AI 不可用，已生成本地练习。</p>
            )}
            <ExerciseList questions={exercises.questions || []} answers={exerciseAnswers} setAnswers={setExerciseAnswers} />
            <button onClick={() => { setExercises(null) }} className="text-xs mt-3" style={{ color: 'var(--text-tertiary)', background: 'none', border: 'none', cursor: 'pointer' }}>收起练习</button>
          </div>
        )}
      </div>

      {/* ═══ 易混词系统 ═══ */}
      <div className="card mb-6">
        <div className="flex items-center gap-2 mb-4">
          <ListOrdered size={15} style={{ color: 'var(--accent)' }} />
          <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>易混词辨析</h3>
        </div>
        {confusion.length === 0 ? (
          <p className="text-sm text-center py-4" style={{ color: 'var(--text-tertiary)' }}>暂无易混词。</p>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {confusion.map((s) => (
              <div key={s.id} style={{ padding: '0.7rem 0.9rem', borderRadius: 'var(--radius-md)', backgroundColor: s.mastered ? 'var(--success-subtle)' : 'var(--surface-tertiary)' }}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
                    {s.word_a} <span style={{ color: 'var(--text-tertiary)' }}>vs</span> {s.word_b}
                  </span>
                  <button onClick={() => toggleConfusion(s)} className="text-[11px] font-semibold" style={{ color: s.mastered ? 'var(--success)' : 'var(--text-tertiary)', background: 'none', border: 'none', cursor: 'pointer' }}>
                    {s.mastered ? '已掌握' : '标记掌握'}
                  </button>
                </div>
                <p className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>{s.distinction_cn}</p>
                {s.memory_tip_cn && <p className="text-[11px] mb-1" style={{ color: 'var(--accent)' }}>💡 {s.memory_tip_cn}</p>}
                {s.example_en && <p className="text-[11px] italic" style={{ color: 'var(--text-tertiary)' }}>"{s.example_en}"</p>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ═══ Proficiency distribution ═══ */}
      <div className="card mb-6">
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>📊 熟练度分布</h3>
        {proficiencyData.some((d) => d.count > 0) ? (
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={proficiencyData} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="level" tick={{ fontSize: 11, fill: 'var(--text-tertiary)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-tertiary)' }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={40}>
                {proficiencyData.map((entry, i) => (
                  <Cell key={i} fill={entry.count > 0 ? 'var(--text-primary)' : 'var(--border)'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-sm text-center py-8" style={{ color: 'var(--text-tertiary)' }}>还没有学习数据</p>
        )}
      </div>

      {/* ═══ 诊断 Modal ═══ */}
      <Modal
        open={!!diagnosis}
        onClose={() => setDiagnosis(null)}
        title={`为什么总记不住「${diagnosis?.word || ''}」？`}
        message={null}
        confirmLabel="知道了"
        cancelLabel=""
        onConfirm={() => setDiagnosis(null)}
      >
        {diagnosis && (
          <div className="space-y-2 py-1">
            {diagnosis.insufficient_data ? (
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>学习数据不足，继续学习后将生成更准确的分析。</p>
            ) : diagnosis.ai_available ? (
              <>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{diagnosis.diagnosis}</p>
                {diagnosis.mistake_pattern && (
                  <div className="text-xs px-3 py-2 rounded-lg" style={{ backgroundColor: 'var(--surface-tertiary)' }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>错误模式：</span>
                    <span style={{ color: 'var(--text-primary)' }}>{diagnosis.mistake_pattern}</span>
                  </div>
                )}
                {diagnosis.suggestions?.length > 0 && (
                  <div className="space-y-1">
                    {diagnosis.suggestions.map((s, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span style={{ color: 'var(--accent)' }}>•</span>
                        <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{s}</span>
                      </div>
                    ))}
                  </div>
                )}
                {diagnosis.practice_sentence && (
                  <p className="text-xs italic" style={{ color: 'var(--accent)' }}>练习：{diagnosis.practice_sentence}</p>
                )}
              </>
            ) : (
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{diagnosis.diagnosis || 'AI 服务不可用，无法生成诊断。'}</p>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="stat-card">
      <Icon size={15} style={{ color }} />
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

function ExerciseList({ questions, answers, setAnswers }) {
  if (!questions?.length) return <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>暂无练习。</p>
  return (
    <div className="space-y-2">
      {questions.map((q, i) => {
        const chosen = answers[i]
        const revealed = chosen !== undefined
        const isCorrect = revealed && chosen === q.answer
        return (
          <div key={i} style={{ padding: '0.7rem 0.9rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--surface-tertiary)' }}>
            <p className="text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>{i + 1}. {q.question}</p>
            {q.options?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-2">
                {q.options.map((opt, oi) => {
                  const letter = String.fromCharCode(65 + oi)
                  const isSel = chosen === letter
                  return (
                    <button key={oi} onClick={() => setAnswers((p) => ({ ...p, [i]: letter }))}
                      style={{
                        padding: '0.25rem 0.6rem', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem',
                        backgroundColor: isSel ? 'var(--accent-subtle)' : 'var(--surface)',
                        border: isSel ? '1px solid var(--accent)' : '1px solid var(--border)',
                        color: isSel ? 'var(--accent)' : 'var(--text-secondary)', cursor: 'pointer',
                      }}>
                      {letter}. {opt}
                    </button>
                  )
                })}
              </div>
            )}
            {revealed && (
              <p className="text-xs" style={{ color: isCorrect ? 'var(--success)' : 'var(--danger)' }}>
                {isCorrect ? '✓ 正确' : `✗ 正确答案：${q.answer}`}
                {q.explanation ? ` — ${q.explanation}` : ''}
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}
