import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, BookOpen, RefreshCw, Trash2, Play, X } from 'lucide-react'
import { api } from '../api'
import Modal from '../components/Modal'

const SOURCE_COLORS = {
  daily: { bg: 'var(--warning-subtle)', color: 'var(--warning)' },
  game: { bg: 'var(--accent-subtle)', color: 'var(--accent)' },
}

/** Group per-(word, source) rows into one entry per word. */
function groupByWord(mistakes) {
  const map = new Map()
  for (const m of mistakes) {
    let entry = map.get(m.word_id)
    if (!entry) {
      entry = {
        word_id: m.word_id, english: m.english, chinese: m.chinese, phonetic: m.phonetic,
        last_occurred_at: m.last_occurred_at,
        daily: 0, game: 0, total: 0,
      }
      map.set(m.word_id, entry)
    }
    entry[m.source] += m.count
    entry.total += m.count
    if (m.last_occurred_at > entry.last_occurred_at) entry.last_occurred_at = m.last_occurred_at
  }
  return Array.from(map.values())
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const sameDay = d.toDateString() === now.toDateString()
  if (sameDay) return `今天 ${d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

export default function MistakeBook() {
  const navigate = useNavigate()
  const [filter, setFilter] = useState('all') // all | daily | game
  const [raw, setRaw] = useState([])
  const [stats, setStats] = useState({ total: 0, daily: 0, game: 0 })
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null) // grouped entry for detail

  const load = () => {
    setLoading(true)
    Promise.all([api.getMistakes('all'), api.getMistakeStats()])
      .then(([m, s]) => {
        setRaw(m.mistakes || [])
        setStats(s)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const grouped = useMemo(() => groupByWord(raw), [raw])
  const filtered = useMemo(() => {
    if (filter === 'daily') return grouped.filter((g) => g.daily > 0)
    if (filter === 'game') return grouped.filter((g) => g.game > 0)
    return grouped
  }, [grouped, filter])

  const handleRemove = async () => {
    if (!selected) return
    try {
      await api.removeMistake(selected.word_id)
      setSelected(null)
      load()
    } catch (e) { console.error(e) }
  }

  const handleAddReview = async () => {
    if (!selected) return
    try {
      await api.addMistakeToReview(selected.word_id)
      setSelected((prev) => prev ? { ...prev, addedReview: true } : prev)
    } catch (e) { console.error(e) }
  }

  const tabs = [
    { key: 'all', label: '全部错误', count: stats.total },
    { key: 'daily', label: '日常错误', count: stats.daily },
    { key: 'game', label: '游戏错误', count: stats.game },
  ]

  return (
    <div className="page animate-fade-in" style={{ maxWidth: 720 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1.5rem' }}>
        <button onClick={() => navigate('/')} className="ios-icon-button" aria-label="Back"><ArrowLeft size={19} /></button>
        <div>
          <h1 className="text-lg font-bold tracking-tight" style={{ color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>错词本</h1>
          <p className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>汇总日常背词与拼词游戏中的错误</p>
        </div>
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setFilter(t.key)}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
              padding: '0.45rem 0.9rem', borderRadius: '100px', border: 'none', cursor: 'pointer',
              fontSize: '0.8125rem', fontWeight: 600,
              backgroundColor: filter === t.key ? 'var(--accent)' : 'var(--surface-secondary)',
              color: filter === t.key ? '#fff' : 'var(--text-secondary)',
              transition: 'all 0.15s ease',
            }}>
            {t.label}
            <span style={{
              fontSize: '0.6875rem', fontWeight: 700,
              padding: '0.05rem 0.45rem', borderRadius: '100px',
              backgroundColor: filter === t.key ? 'rgba(255,255,255,0.25)' : 'var(--surface-tertiary)',
              color: filter === t.key ? '#fff' : 'var(--text-tertiary)',
            }}>{t.count}</span>
          </button>
        ))}
      </div>

      {/* List */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <RefreshCw size={24} className="animate-spin" style={{ color: 'var(--text-tertiary)' }} />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16">
          <BookOpen size={36} style={{ color: 'var(--text-tertiary)', margin: '0 auto 1rem' }} />
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            {filter === 'all' ? '还没有错词，继续保持！' : '该来源下暂无错词。'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {filtered.map((g) => (
            <button key={g.word_id} onClick={() => setSelected(g)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.75rem', width: '100%',
                padding: '0.7rem 0.9rem', borderRadius: 'var(--radius-md)', textAlign: 'left',
                backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
                cursor: 'pointer', transition: 'all 0.15s ease',
              }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{g.english}</span>
                  {g.phonetic && <span className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>{g.phonetic}</span>}
                </div>
                <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--text-secondary)' }}>{g.chinese}</p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem', flexShrink: 0 }}>
                <div style={{ display: 'flex', gap: '0.3rem' }}>
                  {g.daily > 0 && (
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full"
                      style={{ backgroundColor: SOURCE_COLORS.daily.bg, color: SOURCE_COLORS.daily.color }}>
                      日常 {g.daily}次
                    </span>
                  )}
                  {g.game > 0 && (
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full"
                      style={{ backgroundColor: SOURCE_COLORS.game.bg, color: SOURCE_COLORS.game.color }}>
                      游戏 {g.game}次
                    </span>
                  )}
                </div>
                <span className="text-[10px]" style={{ color: 'var(--text-tertiary)' }}>{formatTime(g.last_occurred_at)}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Detail modal */}
      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected?.english || ''}
        message={null}
        confirmLabel="关闭"
        cancelLabel=""
        onConfirm={() => setSelected(null)}
      >
        {selected && (
          <div className="space-y-2.5 py-1">
            {selected.phonetic && <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>{selected.phonetic}</p>}
            <p className="text-sm" style={{ color: 'var(--text-primary)' }}>{selected.chinese}</p>

            <div className="flex flex-wrap gap-1.5">
              {selected.daily > 0 && (
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full"
                  style={{ backgroundColor: SOURCE_COLORS.daily.bg, color: SOURCE_COLORS.daily.color }}>
                  日常错误 · {selected.daily} 次
                </span>
              )}
              {selected.game > 0 && (
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full"
                  style={{ backgroundColor: SOURCE_COLORS.game.bg, color: SOURCE_COLORS.game.color }}>
                  游戏错误 · {selected.game} 次
                </span>
              )}
            </div>

            <div className="text-xs px-3 py-2 rounded-lg" style={{ backgroundColor: 'var(--surface-tertiary)' }}>
              <span style={{ color: 'var(--text-tertiary)' }}>总错误 </span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{selected.total} 次</span>
              <span style={{ color: 'var(--text-tertiary)' }}> · 最近 {formatTime(selected.last_occurred_at)}</span>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', paddingTop: '0.25rem' }}>
              <button onClick={handleAddReview}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold"
                style={{ backgroundColor: selected.addedReview ? 'var(--success-subtle)' : 'var(--accent)', color: selected.addedReview ? 'var(--success)' : '#fff', border: 'none', cursor: 'pointer' }}>
                {selected.addedReview ? '✓ 已加入' : <><Play size={13} /> 加入今日复习</>}
              </button>
              <button onClick={handleRemove}
                className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold"
                style={{ backgroundColor: 'var(--danger-subtle)', color: 'var(--danger)', border: 'none', cursor: 'pointer' }}>
                <Trash2 size={13} /> 移除
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
