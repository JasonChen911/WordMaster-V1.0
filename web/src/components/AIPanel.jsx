import { useState, useEffect } from 'react'
import { Sparkles, X, ChevronDown, ChevronRight, ExternalLink, Loader2 } from 'lucide-react'
import { api } from '../api'

export default function AIPanel({ word, onClose }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expanded, setExpanded] = useState({})

  useEffect(() => {
    if (!word) return
    setLoading(true)
    setError(null)
    api.explainWord(word.english, word.chinese)
      .then((res) => {
        setData(res)
        setExpanded({ examples: true, root: true, tip: true })
      })
      .catch((err) => {
        setError('AI 服务暂不可用')
        console.error(err)
      })
      .finally(() => setLoading(false))
  }, [word])

  const toggle = (key) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div
      className="animate-slide-up rounded-2xl overflow-hidden"
      style={{
        backgroundColor: 'var(--surface-secondary)',
        border: '1px solid var(--border)',
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-5 py-3.5"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <div className="flex items-center gap-2">
          <Sparkles size={16} style={{ color: 'var(--text-primary)' }} />
          <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
            AI 单词解析
          </span>
          <span
            className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded"
            style={{ backgroundColor: 'var(--surface-tertiary)', color: 'var(--text-tertiary)' }}
          >
            AI
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg transition-all hover:bg-[var(--surface-tertiary)]"
          style={{ color: 'var(--text-tertiary)' }}
        >
          <X size={15} />
        </button>
      </div>

      {/* Content */}
      <div className="p-5">
        {loading && (
          <div className="flex items-center gap-3 py-6 justify-center">
            <Loader2 size={18} className="animate-spin" style={{ color: 'var(--text-tertiary)' }} />
            <span className="text-sm" style={{ color: 'var(--text-tertiary)' }}>AI 正在分析...</span>
          </div>
        )}

        {error && (
          <div className="py-4 text-center">
            <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>{error}</p>
            <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
              请在 设置 → AI 服务 中配置 API Key
            </p>
          </div>
        )}

        {data && !loading && (
          <div className="space-y-3">
            {/* Simple explanation */}
            {data.simple_explanation_cn && (
              <div>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                  {data.simple_explanation_cn}
                </p>
              </div>
            )}

            {/* Word root */}
            {data.word_root && (
              <CollapsibleSection
                title="词根词缀"
                expanded={expanded.root}
                onToggle={() => toggle('root')}
              >
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                  {data.word_root}
                </p>
              </CollapsibleSection>
            )}

            {/* Memory tip */}
            {data.memory_tip && (
              <CollapsibleSection
                title="记忆技巧"
                expanded={expanded.tip}
                onToggle={() => toggle('tip')}
              >
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                  {data.memory_tip}
                </p>
              </CollapsibleSection>
            )}

            {/* Extra examples */}
            {data.example_sentences && data.example_sentences.length > 0 && (
              <CollapsibleSection
                title={`更多例句 (${data.example_sentences.length})`}
                expanded={expanded.examples}
                onToggle={() => toggle('examples')}
              >
                <div className="space-y-2">
                  {data.example_sentences.map((ex, i) => (
                    <div
                      key={i}
                      className="p-2.5 rounded-lg"
                      style={{ backgroundColor: 'var(--surface-tertiary)' }}
                    >
                      <p className="text-xs italic leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                        {ex.en}
                      </p>
                      <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
                        {ex.cn}
                      </p>
                    </div>
                  ))}
                </div>
              </CollapsibleSection>
            )}

            {/* AI notice */}
            {!data.ai_available && (
              <p className="text-[10px] mt-3" style={{ color: 'var(--text-tertiary)' }}>
                ⚡ AI 服务未配置，显示默认提示。可在 设置 → AI 服务 中配置 API Key 以启用完整功能。
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function CollapsibleSection({ title, expanded, onToggle, children }) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="flex items-center gap-1.5 w-full text-left py-1 group"
        style={{ color: 'var(--text-secondary)' }}
      >
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <span className="text-xs font-semibold uppercase tracking-wider">{title}</span>
      </button>
      {expanded && <div className="mt-2 ml-5 pl-3 border-l-2" style={{ borderColor: 'var(--border)' }}>{children}</div>}
    </div>
  )
}
