import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Send, Sparkles, Settings, History, Plus, Trash2 } from 'lucide-react'
import { cleanTutorReply } from '../tutorText'
import Modal from '../components/Modal'
import emmaPortrait from '../assets/tutors/emma.webp'
import alexPortrait from '../assets/tutors/alex.webp'
import sophiaPortrait from '../assets/tutors/sophia.webp'

const REPLY_GUIDE = '请先直接回答核心问题，再给最多3条可执行要点。每条尽量一句话；只有确有必要才举例。不要寒暄、重复问题、长篇铺垫，不要使用Markdown星号、标题符号或代码块。'

async function historyRequest(path, options) {
  const response = await fetch(`/api/ai/tutor/conversations${path}`, {
    headers: { 'Content-Type': 'application/json' }, ...options,
  })
  if (!response.ok) throw new Error(`对话记录请求失败 (${response.status})`)
  return response.json()
}

function TutorAvatar({ tutor, size, style }) {
  return <img
    src={tutor.portrait}
    alt={`${tutor.name} 导师头像`}
    width={size}
    height={size}
    style={{ width: size, height: size, borderRadius: '50%', objectFit: 'cover', flexShrink: 0, ...style }}
  />
}

// ═══════════════════════════════════════════════════════════════
// Crystalline Literacy — AI Tutor
// All AI calling logic preserved. Only render layer changed.
// ═══════════════════════════════════════════════════════════════

const TUTORS = {
  emma: {
    name: 'Emma',
    role: '英语老师',
    portrait: emmaPortrait,
    bg: '#6366f1',
    description: '解释单词用法、例句分析、语法讲解',
    system:
      '你叫Emma，是一名耐心的英语老师。你帮助中国学生理解英语单词的用法、例句和语法。用中文回答，英文部分标注。回答简洁有条理。',
    suggestions: ['解释 "abandon" 的用法', '这个例句是什么意思？', '如何区分近义词？', '推荐适合我的学习材料'],
  },
  alex: {
    name: 'Alex',
    role: '词汇教练',
    portrait: alexPortrait,
    bg: '#10b981',
    description: '学习计划制定、复习进度分析',
    system:
      '你叫Alex，是一名专业的词汇学习教练。你帮助学生制定学习计划、分析复习进度、提供学习方法建议。用中文回答，简洁实用。',
    suggestions: ['帮我制定学习计划', '分析我的薄弱点', '如何高效背单词？', '推荐记忆方法'],
  },
  sophia: {
    name: 'Sophia',
    role: '雅思导师',
    portrait: sophiaPortrait,
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
  const [conversations, setConversations] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [historyLoading, setHistoryLoading] = useState(true)
  const [saveError, setSaveError] = useState('')
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [animatedMessageIndex, setAnimatedMessageIndex] = useState(null)
  const chatScrollRef = useRef(null)

  const activeTutor = TUTORS[tutor]

  useEffect(() => {
    const scroller = chatScrollRef.current
    if (!scroller) return
    scroller.scrollTo({ top: scroller.scrollHeight, behavior: 'smooth' })
    if (animatedMessageIndex === null) return
    const scrollTimer = setTimeout(() => {
      scroller.scrollTo({ top: scroller.scrollHeight, behavior: 'smooth' })
    }, 420)
    return () => clearTimeout(scrollTimer)
  }, [messages, animatedMessageIndex])

  useEffect(() => {
    if (animatedMessageIndex === null) return
    const timer = setTimeout(() => setAnimatedMessageIndex(null), 460)
    return () => clearTimeout(timer)
  }, [animatedMessageIndex])

  useEffect(() => {
    let cancelled = false
    setHistoryLoading(true)
    setMessages([])
    setAnimatedMessageIndex(null)
    setConversationId(null)
    setConversations([])
    setSaveError('')
    const load = async () => {
      try {
        const list = await historyRequest(`?tutor=${tutor}`)
        if (cancelled) return
        setConversations(list.items)
        if (list.items.length) {
          const detail = await historyRequest(`/${list.items[0].id}?tutor=${tutor}`)
          if (cancelled) return
          setConversationId(detail.id)
          setMessages(detail.messages)
        }
      } catch (e) {
        if (!cancelled) setSaveError('无法读取已保存的对话，请稍后重试。')
      } finally {
        if (!cancelled) setHistoryLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [tutor])

  const openConversation = async (id) => {
    if (loading || historyLoading || id === conversationId) return
    setHistoryLoading(true)
    setSaveError('')
    try {
      const detail = await historyRequest(`/${id}?tutor=${tutor}`)
      setConversationId(detail.id)
      setMessages(detail.messages)
      setAnimatedMessageIndex(null)
      setHistoryOpen(false)
    } catch (e) {
      setSaveError('无法打开这段对话，请稍后重试。')
    } finally {
      setHistoryLoading(false)
    }
  }

  const newConversation = () => {
    if (loading || historyLoading) return
    setConversationId(null)
    setMessages([])
    setAnimatedMessageIndex(null)
    setInput('')
    setSaveError('')
    setHistoryOpen(false)
  }

  const deleteConversation = async (item) => {
    if (!item || loading || historyLoading) return
    setHistoryLoading(true)
    setSaveError('')
    try {
      await historyRequest(`/${item.id}?tutor=${tutor}`, { method: 'DELETE' })
      const remaining = conversations.filter(conversation => conversation.id !== item.id)
      setConversations(remaining)
      if (conversationId === item.id) {
        setAnimatedMessageIndex(null)
        setConversationId(null)
        setMessages([])
        if (remaining.length) {
          const detail = await historyRequest(`/${remaining[0].id}?tutor=${tutor}`)
          setConversationId(detail.id)
          setMessages(detail.messages)
        }
      }
    } catch (e) {
      setSaveError('删除对话失败，请重试。')
    } finally {
      setHistoryLoading(false)
    }
  }

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || loading || historyLoading) return

    const userMsg = { role: 'user', content: text }
    setLoading(true)
    setSaveError('')

    try {
      let id = conversationId
      if (!id) {
        const created = await historyRequest('', {
          method: 'POST', body: JSON.stringify({ tutor }),
        })
        id = created.id
        setConversationId(id)
        setConversations(prev => [created, ...prev])
      }
      await historyRequest(`/${id}/messages`, {
        method: 'POST', body: JSON.stringify({ tutor, ...userMsg }),
      })
      setAnimatedMessageIndex(messages.length)
      setMessages(prev => [...prev, userMsg])
      setInput('')

      const apiMessages = [
        { role: 'system', content: `${activeTutor.system} ${REPLY_GUIDE}` },
        ...messages.slice(-30).map(m => ({ role: m.role, content: m.content })),
        { role: 'user', content: text },
      ]

      const r = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: apiMessages }),
      })
      if (!r.ok) throw new Error('AI 请求失败')
      const d = await r.json()
      const assistantMsg = { role: 'assistant', content: cleanTutorReply(d.reply) || '抱歉，请稍后重试。' }
      setAnimatedMessageIndex(messages.length + 1)
      setMessages(prev => [
        ...prev,
        assistantMsg,
      ])
      await historyRequest(`/${id}/messages`, {
        method: 'POST', body: JSON.stringify({ tutor, ...assistantMsg }),
      })
      const list = await historyRequest(`?tutor=${tutor}`)
      setConversations(list.items)
    } catch (e) {
      setSaveError('对话或回复未能完整保存。请检查连接后重试。')
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
              onClick={() => { if (!loading && !historyLoading) setTutor(key) }}
              disabled={loading || historyLoading}
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
              <TutorAvatar tutor={t} size={40} style={{
                border: `2px solid ${isActive ? t.bg : 'transparent'}`,
              }} />
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

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <button type="button" onClick={() => setHistoryOpen(value => !value)}
          disabled={loading || historyLoading}
          className="flex items-center gap-1.5 text-xs font-medium"
          style={{ color: 'var(--text-secondary)', cursor: 'pointer' }}>
          <History size={15} /> 历史对话 ({conversations.length})
        </button>
        <button type="button" onClick={newConversation}
          disabled={loading || historyLoading}
          className="flex items-center gap-1.5 text-xs font-medium"
          style={{ color: 'var(--accent)', cursor: 'pointer', marginLeft: 'auto' }}>
          <Plus size={15} /> 新建对话
        </button>
      </div>
      {historyOpen && <div style={{
        display: 'grid', gap: '0.35rem', maxHeight: 180, overflowY: 'auto',
        padding: '0.4rem', marginBottom: '0.75rem', borderRadius: 'var(--radius-md)',
        backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
      }}>
        {conversations.length === 0 && <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>暂无历史对话</span>}
        {conversations.map(item => <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <button type="button" onClick={() => openConversation(item.id)}
            disabled={loading || historyLoading}
            className="text-xs text-left truncate"
            style={{
              flex: 1, minWidth: 0, padding: '0.55rem 0.7rem', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
              backgroundColor: item.id === conversationId ? 'var(--accent-subtle)' : 'var(--surface)',
              color: 'var(--text-primary)',
            }} title={item.title}>{item.title}</button>
          <button type="button" onClick={() => setDeleteTarget(item)}
            disabled={loading || historyLoading}
            aria-label={`删除对话：${item.title}`} title="删除这段对话"
            style={{ padding: '0.55rem', color: 'var(--danger)', cursor: 'pointer' }}>
            <Trash2 size={15} />
          </button>
        </div>)}
      </div>}
      {saveError && <p role="alert" className="text-xs mb-3" style={{ color: 'var(--danger)' }}>{saveError}</p>}

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
          <TutorAvatar tutor={activeTutor} size={34} />
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
        <div ref={chatScrollRef} style={{
          padding: '1rem', maxHeight: 400, overflowY: 'auto', minHeight: 300,
          backgroundColor: 'var(--surface)',
        }}>
          {/* Empty state */}
          {messages.length === 0 && (
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              paddingTop: '2rem', paddingBottom: '1.5rem',
            }}>
              <TutorAvatar tutor={activeTutor} size={64} style={{ marginBottom: '0.75rem' }} />
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
              className={animatedMessageIndex === i ? 'chat-message-enter' : ''}
              style={{ marginBottom: '0.55rem' }}>
              <div className={`chat-message-inner flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {m.role === 'assistant' && (
                  <TutorAvatar tutor={activeTutor} size={26} style={{ marginRight: '0.45rem', marginTop: 2 }} />
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
            </div>
          ))}

          {/* Loading indicator */}
          {loading && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '0.55rem',
              marginBottom: '0.55rem',
            }}>
              <TutorAvatar tutor={activeTutor} size={26} />
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
        由 DeepSeek API 驱动 · 对话记录保存在本机
      </p>
      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)}
        title="删除导师对话？"
        message={deleteTarget ? `“${deleteTarget.title}”及其中的消息会从本机永久删除。` : ''}
        confirmLabel="删除" onConfirm={() => deleteConversation(deleteTarget)} danger />
    </div>
  )
}
