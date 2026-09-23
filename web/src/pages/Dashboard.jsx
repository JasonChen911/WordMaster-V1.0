import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Zap, Sparkles, BookOpen, ArrowRight, Target, AlertTriangle, Flame,
  Layers, GraduationCap, ChevronRight, BookMarked,
} from 'lucide-react'
import { api } from '../api'

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [home, setHome] = useState(null)
  const [insight, setInsight] = useState(null)
  const [insightLoading, setInsightLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getHome().then(setHome).catch(() => setError('无法连接服务器，请确认后端已启动。'))
    // AI insight is non-blocking; it arrives whenever it arrives.
    setInsightLoading(true)
    api.getAIInsights()
      .then(setInsight)
      .catch(() => setInsight({ ai_available: false, insufficient_data: false, insight: '' }))
      .finally(() => setInsightLoading(false))
  }, [])

  if (error) {
    return (
      <div className="page flex items-center justify-center min-h-[70vh]">
        <div className="text-center">
          <p className="text-sm mb-5" style={{ color: 'var(--text-secondary)' }}>{error}</p>
          <button onClick={() => window.location.reload()} className="ios-button ios-button-secondary" style={{ borderRadius: 'var(--radius-md)' }}>重试</button>
        </div>
      </div>
    )
  }

  if (!home) {
    return (
      <div className="page flex items-center justify-center min-h-[70vh]">
        <div className="w-10 h-10 rounded-full border-[2.5px] animate-spin"
          style={{ borderColor: 'var(--border)', borderTopColor: 'var(--accent)' }} />
      </div>
    )
  }

  const tasks = home.remaining_tasks ?? home.total_tasks ?? 0
  const etaText = home.display_text ?? ''

  return (
    <div className="page" style={{ maxWidth: 720, animation: 'fadeSlideIn 0.35s ease forwards' }}>
      {/* ═══ Header ═══ */}
      <header style={{ marginBottom: '1.75rem' }}>
        <p className="text-[12px] font-medium mb-1" style={{ color: 'var(--text-tertiary)' }}>
          {new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })}
        </p>
        <h1 className="text-[26px] font-bold tracking-tight" style={{ color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
          {greeting()}
        </h1>
        <p className="text-[13px] mt-1" style={{ color: 'var(--text-secondary)' }}>
          今天要学什么？
        </p>
      </header>

      {/* ═══ Main task card ═══ */}
      <div style={{
        backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-xl)', padding: '1.75rem', marginBottom: '1.25rem',
      }}>
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>今日学习</span>
          {home.active_book?.book_name && (
            <button onClick={() => navigate('/dictionary')}
              className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full"
              style={{ backgroundColor: 'var(--accent-subtle)', color: 'var(--accent)', border: 'none', cursor: 'pointer' }}>
              {home.active_book.book_name}
            </button>
          )}
        </div>
        <p className="text-[32px] font-bold tracking-tight mb-1" style={{ color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
          {tasks === 0 ? '今天的任务已完成' : `还有 ${tasks} 个学习任务`}
        </p>
        <p className="text-[13px] mb-5" style={{ color: 'var(--text-tertiary)' }}>
          {tasks === 0 ? '去学习分析看看你的进步，或导入新材料继续学习。' : `预计 ${etaText}`}
        </p>
        <button onClick={() => navigate('/study')}
          style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
            padding: '0.8rem', borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--accent)', color: '#fff', border: 'none', cursor: 'pointer',
            fontSize: '0.9375rem', fontWeight: 600,
          }}>
          <Zap size={18} /> {tasks === 0 ? '再学一轮' : '开始学习'} <ArrowRight size={16} />
        </button>
      </div>

      {/* ═══ Stat tiles ═══ */}
      <div className="grid grid-cols-4 gap-2.5 mb-1.5">
        <StatTile icon={BookOpen} label="新词" value={home.new_words ?? 0} color="var(--accent)" />
        <StatTile icon={Target} label="待复习" value={home.review_due ?? 0} color="var(--warning)" />
        <StatTile icon={AlertTriangle} label="高风险" value={home.high_risk ?? 0} color="var(--danger)" />
        <StatTile icon={Flame} label="连续" value={`${home.streak_days ?? 0}天`} color="var(--success)" />
      </div>

      {/* ═══ AI Learning Insight ═══ */}
      <div style={{
        backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', padding: '1.1rem 1.25rem', marginTop: '1.25rem', marginBottom: '1.25rem',
      }}>
        <div className="flex items-center gap-2 mb-2">
          <Sparkles size={14} style={{ color: 'var(--accent)' }} />
          <span className="text-[12px] font-semibold" style={{ color: 'var(--text-primary)' }}>AI 学习洞察</span>
        </div>
        {insightLoading ? (
          <p className="text-[13px]" style={{ color: 'var(--text-tertiary)' }}>正在分析你的学习数据…</p>
        ) : insight?.ai_available ? (
          <>
            <p className="text-[13px] leading-relaxed mb-2" style={{ color: 'var(--text-secondary)' }}>{insight.insight}</p>
            <button onClick={() => navigate('/analytics')}
              className="flex items-center gap-1 text-[12px] font-semibold"
              style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              查看分析 <ChevronRight size={13} />
            </button>
          </>
        ) : insight?.insufficient_data ? (
          <p className="text-[13px]" style={{ color: 'var(--text-tertiary)' }}>
            完成几次学习后，WordMaster 会生成更可靠的学习洞察。
          </p>
        ) : (
          <p className="text-[13px]" style={{ color: 'var(--text-tertiary)' }}>
            AI 服务未配置或暂不可用。基础学习与 FSRS 复习不受影响。
          </p>
        )}
      </div>

      {/* ═══ Quick entries ═══ */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        <EntryRow icon={Layers} title="AI 材料分析" desc="从文章提取重点词汇，生成词书" onClick={() => navigate('/material')} />
        <EntryRow icon={BookMarked} title="错词本" desc="查看日常与游戏中的错误词" onClick={() => navigate('/mistakes')} />
        <EntryRow icon={BookOpen} title="词书管理" desc="管理词书与词典" onClick={() => navigate('/dictionary')} />
        <EntryRow icon={GraduationCap} title="教师 Preview" desc="查看班级学习情况（演示数据）" onClick={() => navigate('/teacher')} />
      </div>

      {/* ═══ Version ═══ */}
      <div className="text-center mt-8 pb-4">
        <span className="text-[11px] font-medium tracking-wider" style={{ color: 'var(--text-tertiary)', letterSpacing: '0.04em' }}>
          WordMaster AI
        </span>
      </div>
    </div>
  )
}

function StatTile({ icon: Icon, label, value, color }) {
  return (
    <div style={{
      backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-md)', padding: '0.8rem 0.5rem',
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.3rem',
    }}>
      <Icon size={15} style={{ color }} />
      <div className="text-lg font-bold tracking-tight" style={{ color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>{value}</div>
      <div className="text-[10px] font-medium" style={{ color: 'var(--text-tertiary)' }}>{label}</div>
    </div>
  )
}

function EntryRow({ icon: Icon, title, desc, onClick }) {
  return (
    <button onClick={onClick}
      className="flex items-center gap-3.5 p-3.5 rounded-xl transition-all hover:opacity-80"
      style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)', cursor: 'pointer', textAlign: 'left' }}>
      <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'var(--accent-subtle)' }}>
        <Icon size={17} style={{ color: 'var(--accent)' }} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{title}</div>
        <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{desc}</div>
      </div>
      <ChevronRight size={16} style={{ color: 'var(--text-tertiary)' }} />
    </button>
  )
}
