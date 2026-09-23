import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Sparkles, Loader2, FileText, Upload, Wand2, CheckSquare,
  Square, BookPlus, CheckCircle2, AlertTriangle, Star,
} from 'lucide-react'
import { api } from '../api'

const SAMPLE_TEXT = `Artificial intelligence is transforming the way students learn. Today, intelligent tutoring systems can analyze a learner's strengths and weaknesses, then recommend personalized study plans. This approach challenges the traditional one-size-fits-all classroom model.

Researchers argue that the most important skill is not memorizing facts, but learning how to approach complex problems critically. Students who adapt quickly to new technology often gain a significant advantage. However, some educators worry that relying too much on algorithms may discourage independent thinking.

To address these concerns, schools should encourage a balanced approach: use AI to support learning, but preserve the human elements of teaching. After all, education is about more than efficiency — it is about cultivating curiosity and judgment.`

export default function MaterialImport() {
  const navigate = useNavigate()
  const [text, setText] = useState('')
  const [bookName, setBookName] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [candidates, setCandidates] = useState([])
  const [aiAvailable, setAiAvailable] = useState(true)
  const [documentSummary, setDocumentSummary] = useState('')
  const [note, setNote] = useState('')
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(() => new Set())
  const [importing, setImporting] = useState(false)
  const [imported, setImported] = useState(null)
  const fileRef = useRef(null)

  const handleAnalyze = async () => {
    if (!text.trim()) { setError('请先粘贴或上传学习材料。'); return }
    setAnalyzing(true); setError(null); setCandidates([]); setImported(null)
    setSelected(new Set())
    try {
      const r = await api.analyzeMaterial(text, 30)
      if (r.error) { setError(r.error) }
      else {
        setCandidates(r.candidates || [])
        setAiAvailable(!!r.ai_available)
        setDocumentSummary(r.document_summary || '')
        setNote(r.note || '')
        if (!r.bookName && !bookName.trim()) {
          setBookName('AI 学习词书')
        }
      }
    } catch (e) {
      setError('分析失败：' + (e.message || '请稍后重试。'))
    } finally { setAnalyzing(false) }
  }

  const handleFile = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      setText(String(reader.result || ''))
      if (!bookName.trim()) setBookName(file.name.replace(/\.[^.]+$/, ''))
    }
    reader.readAsText(file)
  }

  const toggle = (word) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(word)) next.delete(word)
      else next.add(word)
      return next
    })
  }

  const selectAll = () => setSelected(new Set(candidates.map((c) => c.word)))
  const clearAll = () => setSelected(new Set())

  const handleImport = async () => {
    const chosen = candidates.filter((c) => selected.has(c.word))
    if (chosen.length === 0) { setError('请至少选择一个单词。'); return }
    setImporting(true); setError(null)
    try {
      const r = await api.importMaterial(bookName.trim() || 'AI 词书', chosen)
      if (r.error) { setError(r.error) }
      else {
        setImported(r)
      }
    } catch (e) {
      setError('导入失败：' + (e.message || '请稍后重试。'))
    } finally { setImporting(false) }
  }

  const importanceColor = (v) => v >= 0.85 ? 'var(--danger)' : v >= 0.7 ? 'var(--warning)' : 'var(--accent)'

  return (
    <div className="page" style={{ maxWidth: 780, animation: 'fadeSlideIn 0.35s ease forwards' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1.5rem' }}>
        <button onClick={() => navigate('/dictionary')} className="ios-icon-button" aria-label="Back"><ArrowLeft size={19} /></button>
        <div>
          <h1 className="text-lg font-bold tracking-tight" style={{ color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>AI 材料分析</h1>
          <p className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>从文章提取重点词汇，生成专属词书</p>
        </div>
      </div>

      {/* Success state */}
      {imported && (
        <div style={{
          padding: '1.5rem', borderRadius: 'var(--radius-xl)',
          backgroundColor: 'var(--success-subtle)', border: '1px solid var(--success)',
          marginBottom: '1.25rem', textAlign: 'center',
        }}>
          <CheckCircle2 size={36} style={{ color: 'var(--success)', margin: '0 auto 0.75rem' }} />
          <h2 className="text-lg font-bold mb-1" style={{ color: 'var(--text-primary)' }}>词书已生成</h2>
          <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
            《{imported.book_name}》共 {imported.imported} 个单词，已进入学习队列。
          </p>
          <div style={{ display: 'flex', gap: '0.6rem', justifyContent: 'center' }}>
            <button onClick={() => navigate('/study')}
              className="ios-button ios-button-primary" style={{ borderRadius: 'var(--radius-md)' }}>开始学习</button>
            <button onClick={() => navigate('/dictionary')}
              className="ios-button ios-button-secondary" style={{ borderRadius: 'var(--radius-md)' }}>词书管理</button>
          </div>
        </div>
      )}

      {/* Input card */}
      {!imported && (
        <div style={{
          backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-xl)', padding: '1.25rem', marginBottom: '1.25rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
            <label className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-tertiary)' }}>
              学习材料（TXT / Markdown / 纯文本）
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button onClick={() => fileRef.current?.click()}
                className="flex items-center gap-1 text-[11px] font-semibold"
                style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer' }}>
                <Upload size={12} /> 上传文件
              </button>
              <button onClick={() => { setText(SAMPLE_TEXT); if (!bookName.trim()) setBookName('AI 与教育示例') }}
                className="flex items-center gap-1 text-[11px] font-semibold"
                style={{ color: 'var(--text-tertiary)', background: 'none', border: 'none', cursor: 'pointer' }}>
                <Wand2 size={12} /> 示例
              </button>
            </div>
          </div>
          <input ref={fileRef} type="file" accept=".txt,.md,.markdown,.text" hidden onChange={handleFile} />
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            placeholder="在此粘贴英语文章，或上传 TXT / Markdown 文件…"
            style={{
              width: '100%', padding: '0.75rem', borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
              color: 'var(--text-primary)', fontSize: '0.8125rem', lineHeight: 1.7,
              fontFamily: 'inherit', resize: 'vertical', outline: 'none',
            }}
          />
          <button onClick={handleAnalyze} disabled={analyzing}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
              marginTop: '0.75rem', padding: '0.7rem', borderRadius: 'var(--radius-md)',
              backgroundColor: analyzing ? 'var(--surface-tertiary)' : 'var(--accent)',
              color: analyzing ? 'var(--text-tertiary)' : '#fff', border: 'none',
              cursor: analyzing ? 'wait' : 'pointer', fontSize: '0.875rem', fontWeight: 600,
            }}>
            {analyzing ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
            {analyzing ? 'AI 正在分析材料…' : 'AI 分析材料，提取重点词汇'}
          </button>
        </div>
      )}

      {/* Error / note */}
      {error && (
        <div style={{
          padding: '0.9rem 1rem', borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--danger-subtle)', border: '1px solid var(--danger)',
          color: 'var(--danger)', fontSize: '0.8125rem', marginBottom: '1rem',
        }}>{error}</div>
      )}
      {note && !error && (
        <div style={{
          padding: '0.9rem 1rem', borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--surface-tertiary)', border: '1px solid var(--border)',
          color: 'var(--text-tertiary)', fontSize: '0.75rem', marginBottom: '1rem',
        }}>
          <AlertTriangle size={12} style={{ display: 'inline', marginRight: 4, color: 'var(--warning)' }} />
          {note}
        </div>
      )}

      {/* Candidates */}
      {candidates.length > 0 && !imported && (
        <div style={{
          backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-xl)', padding: '1.25rem',
        }}>
          {documentSummary && (
            <div style={{
              padding: '0.6rem 0.9rem', marginBottom: '0.85rem', borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--accent-subtle)', border: '1px solid color-mix(in srgb, var(--accent) 18%, transparent)',
            }}>
              <p className="text-[11px] font-semibold mb-0.5" style={{ color: 'var(--accent)' }}>AI 材料摘要</p>
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{documentSummary}</p>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
              {aiAvailable ? 'AI 推荐重点词' : '候选词汇（本地识别）'}（{selected.size}/{candidates.length}）
            </h3>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button onClick={selectAll} className="text-[11px] font-semibold" style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer' }}>全选</button>
              <button onClick={clearAll} className="text-[11px] font-semibold" style={{ color: 'var(--text-tertiary)', background: 'none', border: 'none', cursor: 'pointer' }}>全不选</button>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: 380, overflowY: 'auto' }}>
            {candidates.map((c) => {
              const isSel = selected.has(c.word)
              return (
                <button key={c.word} onClick={() => toggle(c.word)}
                  style={{
                    display: 'flex', alignItems: 'flex-start', gap: '0.75rem', width: '100%',
                    padding: '0.7rem 0.85rem', borderRadius: 'var(--radius-md)', textAlign: 'left',
                    backgroundColor: isSel ? 'var(--accent-subtle)' : 'var(--surface)',
                    border: isSel ? '1px solid var(--accent)' : '1px solid var(--border)',
                    cursor: 'pointer', transition: 'all 0.15s ease',
                  }}>
                  {isSel ? <CheckSquare size={16} style={{ color: 'var(--accent)', flexShrink: 0, marginTop: 2 }} />
                    : <Square size={16} style={{ color: 'var(--text-tertiary)', flexShrink: 0, marginTop: 2 }} />}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{c.word}</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 1, fontSize: '10px', color: importanceColor(c.importance) }}>
                        <Star size={10} fill={importanceColor(c.importance)} /> {Math.round((c.importance ?? 0) * 100)}%
                      </span>
                      {c.difficulty && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ backgroundColor: 'var(--surface-tertiary)', color: 'var(--text-tertiary)' }}>
                          {c.difficulty}
                        </span>
                      )}
                    </div>
                    {(c.meaning_zh || c.meaning) && <p className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{c.meaning_zh || c.meaning}</p>}
                    {c.reason && <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>{c.reason}</p>}
                    {c.example && <p className="text-[11px] mt-0.5 italic" style={{ color: 'var(--text-tertiary)' }}>"{c.example}"</p>}
                    {c.tags?.length > 0 && (
                      <div className="flex gap-1 mt-1">
                        {c.tags.map((t) => (
                          <span key={t} className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ backgroundColor: 'var(--accent-subtle)', color: 'var(--accent)' }}>{t}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </button>
              )
            })}
          </div>

          {/* Book name + import */}
          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.6rem' }}>
            <input value={bookName} onChange={(e) => setBookName(e.target.value)}
              placeholder="词书名称"
              style={{
                flex: 1, padding: '0.6rem 0.85rem', borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
                color: 'var(--text-primary)', fontSize: '0.8125rem', fontFamily: 'inherit', outline: 'none',
              }} />
            <button onClick={handleImport} disabled={importing || selected.size === 0}
              className="flex items-center gap-1.5"
              style={{
                padding: '0.6rem 1.1rem', borderRadius: 'var(--radius-md)',
                backgroundColor: selected.size > 0 && !importing ? 'var(--accent)' : 'var(--surface-tertiary)',
                color: selected.size > 0 && !importing ? '#fff' : 'var(--text-tertiary)', border: 'none',
                cursor: selected.size > 0 && !importing ? 'pointer' : 'default',
                fontSize: '0.8125rem', fontWeight: 600,
              }}>
              {importing ? <Loader2 size={15} className="animate-spin" /> : <BookPlus size={15} />}
              {importing ? '导入中…' : '生成词书'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
