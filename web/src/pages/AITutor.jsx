import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Send, Sparkles, Settings } from 'lucide-react'

// ═══════════════════════════════════════════════════════════════
// Crystalline Literacy — AI Tutor
// All AI calling logic preserved. Only render layer changed.
// ═══════════════════════════════════════════════════════════════

const TUTORS = {
  emma: {
    name: 'Emma',
    role: '英语老师',
    emoji: '👩‍🏫',
    bg: '#6366f1',
    description: '解释单词用法、例句分析、语法讲解',
    system:
      '你叫Emma，是一名耐心的英语老师。你帮助中国学生理解英语单词的用法、例句和语法。用中文回答，英文部分标注。回答简洁有条理。',
    suggestions: ['解释 "abandon" 的用法', '这个例句是什么意思？', '如何区分近义词？', '推荐适合我的学习材料'],
  },
  alex: {
    name: 'Alex',
    role: '词汇教练',
    emoji: '🧑‍🎓',
    bg: '#10b981',
    description: '学习计划制定、复习进度分析',
    system:
      '你叫Alex，是一名专业的词汇学习教练。你帮助学生制定学习计划、分析复习进度、提供学习方法建议。用中文回答，简洁实用。',
    suggestions: ['帮我制定学习计划', '分析我的薄弱点', '如何高效背单词？', '推荐记忆方法'],
  },
  sophia: {
    name: 'Sophia',
    role: '雅思导师',
    emoji: '👩‍💼',
    bg: '#f59e0b',
    description: '雅思高频词汇、口语话题、写作表达',
    system:
      '你叫Sophia，是一名雅思考试导师。你专注于雅思高频词汇、口语话题和写作表达。用中文回答，提供考试技巧。回答专业且鼓舞人心。',
    suggestions: ['雅思口语常见话题', '写作高分词汇推荐', '阅读长难句分析', '听力场景词汇'],
  },
}

export default function AITutor() {
  const navigate = useNavigate()
  const [tutor, setTutor] = useState('emma')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef(null)

  const activeTutor = TUTORS[tutor]

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || loading) return

    const userMsg = { role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const apiMessages = [
        { role: 'system', content: activeTutor.system },
        ...messages.map(m => ({ role: m.role, content: m.content })),
        { role: 'user', content: text },
      ]

      const r = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: apiMessages }),
      })
      const d = await r.json()
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: d.reply || '抱歉，请稍后重试。' },
      ])
    } catch (e) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: '网络错误，请检查 API 配置后重试。' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestionClick = (text) => {
    setInput(text)
    setTimeout(() => {
      const inputEl = document.querySelector('#ai-tutor-input')
      inputEl?.focus()
    }, 50)
  }

  return (
    <div className="page animate-fade-in" style={{ maxWidth: 680 }}>
      {/* ═══ Header ═══ */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: '1.5rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <button onClick={() => navigate('/')} className="ios-icon-button" aria-label="Back">
            <ArrowLeft size={19} />
          </button>
          <div>
            <h1 className="text-lg font-bold tracking-tight" style={{
              color: 'var(--text-primary)', letterSpacing: '-0.02em',
            }}>AI 学习助手</h1>
            <p className="text-[11px] font-medium" style={{ color: 'var(--text-tertiary)' }}>
              与专属导师对话，获取个性化学习指导
            </p>
          </div>
        </div>
        <button onClick={() => navigate('/settings/ai')}
          className="ios-icon-button" title="AI 设置"
          style={{ color: 'var(--text-tertiary)' }}>
          <Settings size={17} />
        </button>
      </div>

      {/* ═══ Tutor Selector ═══ */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
        {Object.entries(TUTORS).map(([key, t]) => {
          const isActive = tutor === key
          return (
            <button
              key={key}
              onClick={() => { setTutor(key); setMessages([]) }}
              style={{
                flex: 1,
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.4rem',
                padding: '0.75rem 0.5rem',
                borderRadius: 'var(--radius-lg)',
                backgroundColor: isActive ? 'var(--surface-secondary)' : 'transparent',
                border: isActive
                  ? `1.5px solid ${t.bg}`
                  : '1.5px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.25s cubic-bezier(0.22, 0.61, 0.36, 1)',
                boxShadow: isActive
                  ? `0 2px 12px color-mix(in srgb, ${t.bg} 18%, transparent)`
                  : 'none',
              }}
              onMouseEnter={e => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = 'var(--surface-secondary)'
                  e.currentTarget.style.borderColor = 'var(--border)'
                }
              }}
              onMouseLeave={e => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = 'transparent'
                  e.currentTarget.style.borderColor = 'transparent'
                }
              }}>
              <div style={{
                width: 40, height: 40, borderRadius: '50%',
                backgroundColor: isActive ? `color-mix(in srgb, ${t.bg} 14%, transparent)` : 'var(--surface-tertiary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.25rem',
                transition: 'background-color 0.25s ease',
              }}>
                {t.emoji}
              </div>
              <div>
                <div className="text-[12px] font-bold tracking-tight"
                  style={{ color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                  {t.name}
                </div>
                <div className="text-[10px] font-medium"
                  style={{ color: isActive ? t.bg : 'var(--text-tertiary)' }}>
                  {t.role}
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* ═══ Chat Area ═══ */}
      <div style={{
        borderRadius: 'var(--radius-xl)',
        backgroundColor: 'var(--surface-secondary)',
        border: '1px solid var(--border)',
        overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
      }}>
        {/* ── Chat Top Bar ── */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.65rem',
          padding: '0.65rem 1rem',
          borderBottom: '1px solid var(--border)',
          backgroundColor: 'var(--surface)',
        }}>
          <div style={{
            width: 34, height: 34, borderRadius: '50%',
            backgroundColor: `color-mix(in srgb, ${activeTutor.bg} 16%, transparent)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1rem',
          }}>
            {activeTutor.emoji}
          </div>
          <div style={{ flex: 1 }}>
            <div className="text-[13px] font-bold tracking-tight"
              style={{ color: 'var(--text-primary)' }}>{activeTutor.name}</div>
            <div className="text-[10px] font-medium"
              style={{ color: 'var(--text-tertiary)' }}>{activeTutor.role} · {activeTutor.description.slice(0, 14)}...</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{
              width: 7, height: 7, borderRadius: '50%',
              backgroundColor: 'var(--success)',
              boxShadow: '0 0 6px var(--success)',
            }} />
            <span className="text-[10px] font-medium" style={{ color: 'var(--text-tertiary)' }}>在线</span>
          </div>
        </div>

        {/* ── Messages ── */}
        <div style={{
          padding: '1rem', maxHeight: 400, overflowY: 'auto', minHeight: 300,
          backgroundColor: 'var(--surface)',
        }}>
          {/* Empty state */}
          {messages.length === 0 && (
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              paddingTop: '2rem', paddingBottom: '1.5rem',
            }}>
              <div style={{
                width: 64, height: 64, borderRadius: '50%',
                backgroundColor: `color-mix(in srgb, ${activeTutor.bg} 14%, transparent)`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '2rem', marginBottom: '0.75rem',
              }}>
                {activeTutor.emoji}
              </div>
              <p className="text-sm font-semibold mb-1"
                style={{ color: 'var(--text-primary)' }}>
                {activeTutor.name} · {activeTutor.role}
              </p>
              <p className="text-xs mb-4 leading-relaxed text-center"
                style={{ color: 'var(--text-tertiary)', maxWidth: 320 }}>
                {activeTutor.description}
              </p>
              <div style={{
                display: 'flex', flexWrap: 'wrap', gap: '0.4rem',
                justifyContent: 'center', maxWidth: 380,
              }}>
                {activeTutor.suggestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => handleSuggestionClick(q)}
                    style={{
                      padding: '0.4rem 0.85rem',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--surface-tertiary)',
                      color: 'var(--text-secondary)',
                      border: '1px solid var(--border)',
                      cursor: 'pointer',
                      fontSize: '0.6875rem', fontWeight: 500,
                      transition: 'all 0.2s ease',
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.backgroundColor = `color-mix(in srgb, ${activeTutor.bg} 10%, var(--surface-tertiary))`
                      e.currentTarget.style.borderColor = `color-mix(in srgb, ${activeTutor.bg} 25%, transparent)`
                      e.currentTarget.style.color = 'var(--text-primary)'
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.backgroundColor = 'var(--surface-tertiary)'
                      e.currentTarget.style.borderColor = 'var(--border)'
                      e.currentTarget.style.color = 'var(--text-secondary)'
                    }}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Message list */}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`msg-enter ${m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}`}
              style={{ marginBottom: '0.55rem' }}>
              {m.role === 'assistant' && (
                <div style={{
                  width: 26, height: 26, borderRadius: '50%',
                  backgroundColor: `color-mix(in srgb, ${activeTutor.bg} 16%, transparent)`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.8rem', marginRight: '0.45rem', marginTop: 2, flexShrink: 0,
                }}>
                  {activeTutor.emoji}
                </div>
              )}
              <div
                style={{
                  maxWidth: '78%',
                  padding: '0.55rem 0.9rem',
                  borderRadius: m.role === 'user'
                    ? 'var(--radius-md) 4px var(--radius-md) var(--radius-md)'
                    : '4px var(--radius-md) var(--radius-md) var(--radius-md)',
                  backgroundColor: m.role === 'user' ? 'var(--accent)' : 'var(--surface-tertiary)',
                  color: m.role === 'user' ? '#fff' : 'var(--text-primary)',
                  fontSize: '0.8125rem', lineHeight: 1.6,
                  whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                }}>
                {m.content}
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {loading && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '0.55rem',
              marginBottom: '0.55rem',
            }}>
              <div style={{
                width: 26, height: 26, borderRadius: '50%',
                backgroundColor: `color-mix(in srgb, ${activeTutor.bg} 16%, transparent)`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.8rem',
              }}>
                {activeTutor.emoji}
              </div>
              <div style={{
                padding: '0.55rem 0.9rem',
                borderRadius: '4px var(--radius-md) var(--radius-md) var(--radius-md)',
                backgroundColor: 'var(--surface-tertiary)',
                display: 'flex', alignItems: 'center', gap: '0.5rem',
              }}>
                <div className="thinking-dots"><span /><span /><span /></div>
                <span className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>思考中...</span>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* ── Input Bar ── */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.5rem',
          padding: '0.65rem 0.85rem',
          borderTop: '1px solid var(--border)',
          backgroundColor: 'var(--surface-secondary)',
        }}>
          <input
            id="ai-tutor-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder={`向 ${activeTutor.name} 提问...`}
            disabled={loading}
            style={{
              flex: 1, padding: '0.55rem 0.85rem',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
              fontSize: '0.8125rem', fontFamily: 'inherit',
              outline: 'none',
              transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
            }}
            onFocus={e => {
              e.target.style.borderColor = 'var(--accent)'
              e.target.style.boxShadow = '0 0 0 3px var(--accent-subtle)'
            }}
            onBlur={e => {
              e.target.style.borderColor = 'var(--border)'
              e.target.style.boxShadow = 'none'
            }}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            style={{
              flexShrink: 0, width: 36, height: 36,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: input.trim() ? 'var(--accent)' : 'var(--surface-tertiary)',
              color: input.trim() ? '#fff' : 'var(--text-tertiary)',
              border: 'none', cursor: input.trim() ? 'pointer' : 'default',
              transition: 'all 0.2s ease',
              opacity: loading && !input.trim() ? 0.3 : 1,
              boxShadow: input.trim() ? '0 2px 8px color-mix(in srgb, var(--accent) 30%, transparent)' : 'none',
            }}>
            <Send size={15} />
          </button>
        </div>
      </div>

      {/* ═══ Footer ═══ */}
      <p style={{
        textAlign: 'center', marginTop: '0.75rem',
        fontSize: '10px', fontWeight: 500,
        color: 'var(--text-tertiary)', opacity: 0.55,
      }}>
        由 DeepSeek API 驱动 · 对话内容仅用于学习指导
      </p>
    </div>
  )
}
