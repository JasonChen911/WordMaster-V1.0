import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft, GraduationCap, Users, TrendingUp, AlertTriangle, Sparkles,
  RefreshCw, BookOpen, Plus, BadgeCheck,
} from 'lucide-react'
import { api } from '../api'

export default function Teacher() {
  const navigate = useNavigate()
  const [overview, setOverview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [report, setReport] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)

  const load = () => {
    setLoading(true)
    api.getTeacherOverview()
      .then(setOverview)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleReport = async () => {
    setReportLoading(true)
    try {
      const r = await api.getTeacherReport()
      setReport(r)
    } catch (e) { setReport({ ai_available: false, summary: '报告生成失败。' }) }
    finally { setReportLoading(false) }
  }

  if (loading) {
    return (
      <div className="page flex items-center justify-center min-h-[70vh]">
        <RefreshCw size={28} className="animate-spin" style={{ color: 'var(--text-tertiary)' }} />
      </div>
    )
  }

  const s = overview?.class_stats || {}
  const weak = overview?.class_weak_words || []

  return (
    <div className="page animate-fade-in" style={{ maxWidth: 820 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1.5rem' }}>
        <button onClick={() => navigate('/')} className="ios-icon-button" aria-label="Back"><ArrowLeft size={19} /></button>
        <div>
          <h1 className="text-lg font-bold tracking-tight" style={{ color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Teacher Preview
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full ml-2" style={{ backgroundColor: 'var(--warning-subtle)', color: 'var(--warning)', verticalAlign: 'middle' }}>Preview</span>
          </h1>
          <p className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>课程 · 班级学习情况 · 教学建议（轻量预览）</p>
        </div>
      </div>

      {/* Preview data label */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.5rem',
        padding: '0.6rem 0.9rem', marginBottom: '1.25rem', borderRadius: 'var(--radius-md)',
        backgroundColor: 'var(--surface-tertiary)', border: '1px solid var(--border)',
      }}>
        <BadgeCheck size={14} style={{ color: 'var(--warning)' }} />
        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
          <strong>Preview 演示数据：</strong>当前为「{overview?.demo_class_name || 'Demo Class'}」的虚构学生数据，仅用于预览课堂场景，<strong>不是真实运营结果</strong>。
        </span>
      </div>

      {/* Class stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard icon={Users} label="学生数" value={s.student_count ?? 0} color="var(--accent)" />
        <StatCard icon={TrendingUp} label="完成率" value={`${Math.round((s.completion_rate ?? 0) * 100)}%`} color="var(--success)" />
        <StatCard icon={BookOpen} label="平均正确率" value={`${Math.round((s.avg_accuracy ?? 0) * 100)}%`} color="var(--accent)" />
        <StatCard icon={AlertTriangle} label="遗忘率" value={`${Math.round((s.forgetting_rate ?? 0) * 100)}%`} color="var(--danger)" />
      </div>

      {/* AI teaching report */}
      <div className="card mb-6" style={{ borderColor: 'var(--accent)', borderWidth: '1.5px' }}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles size={15} style={{ color: 'var(--accent)' }} />
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>AI 教学总结</h3>
          </div>
          {!report && (
            <button onClick={handleReport} disabled={reportLoading} className="btn-ghost text-xs gap-1 py-1.5 px-3">
              {reportLoading ? <RefreshCw size={13} className="animate-spin" /> : <Sparkles size={13} />}
              {reportLoading ? '生成中…' : '生成总结'}
            </button>
          )}
        </div>
        {report?.ai_available ? (
          <div>
            <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--text-secondary)' }}>{report.summary}</p>
            {report.weak_points?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-3">
                {report.weak_points.map((w, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: 'var(--danger-subtle)', color: 'var(--danger)' }}>{w}</span>
                ))}
              </div>
            )}
            {report.suggestions?.length > 0 && (
              <div className="space-y-1.5">
                {report.suggestions.map((s, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span style={{ color: 'var(--accent)' }}>•</span>
                    <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{s}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : report ? (
          <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>{report.summary || '暂无总结。'}</p>
        ) : (
          <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>点击「生成总结」，AI 基于班级真实统计给出教学建议。</p>
        )}
      </div>

      {/* Class weak words */}
      <div className="card mb-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle size={15} style={{ color: 'var(--danger)' }} />
          <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>班级共性薄弱词</h3>
        </div>
        {weak.length === 0 ? (
          <p className="text-sm text-center py-4" style={{ color: 'var(--text-tertiary)' }}>暂无薄弱词。</p>
        ) : (
          <div className="space-y-1.5 max-h-64 overflow-y-auto">
            {weak.map((w) => (
              <div key={w.word} className="flex items-center justify-between py-2 px-3 rounded-lg" style={{ backgroundColor: 'var(--surface-tertiary)' }}>
                <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{w.word}</span>
                <div className="flex items-center gap-3">
                  <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{w.students} 人出错</span>
                  <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: 'var(--danger-subtle)', color: 'var(--danger)' }}>共错 {w.wrong_count} 次</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Students */}
      <div className="card mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Users size={15} style={{ color: 'var(--accent)' }} />
          <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>学生名单（演示）</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {overview?.students?.map((st) => (
            <div key={st.id} style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--surface-tertiary)' }}>
              <div className="text-sm font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>{st.name}</div>
              <div className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>
                掌握 {st.words_mastered}/{st.words_studied} · 正确率 {st.total_reviews ? Math.round((st.correct_count / st.total_reviews) * 100) : 0}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Create course CTA */}
      <button onClick={() => navigate('/material')}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
          padding: '0.85rem', borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
          color: 'var(--text-primary)', cursor: 'pointer', fontSize: '0.875rem', fontWeight: 600,
        }}>
        <Plus size={16} style={{ color: 'var(--accent)' }} />
        上传材料，AI 提取课程词书
      </button>
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
