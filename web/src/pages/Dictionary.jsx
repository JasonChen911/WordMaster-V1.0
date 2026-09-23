import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Upload, Database, Trash2, Search, RefreshCw, BookOpen, ChevronLeft, ChevronRight,
  FileText, CheckCircle2, AlertTriangle, X, FolderOpen, Play, Loader2, Volume2,
  Download, FileUp, Plus, BookMarked, Clock, BarChart3, RotateCcw, Sparkles,
} from 'lucide-react'
import { api } from '../api'
import Modal, { AlertModal } from '../components/Modal'

const PER_PAGE = 50

/** Format supported by the importer */
const FORMATS = {
  txt: { label: 'TXT (Tab分隔)', ext: '.txt', mime: 'text/plain' },
  csv: { label: 'CSV (逗号分隔)', ext: '.csv', mime: 'text/csv' },
  json: { label: 'JSON', ext: '.json', mime: 'application/json' },
}

/** Confirmation dialog component */
function ConfirmDialog({ open, title, message, onConfirm, onCancel }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ backgroundColor: 'rgba(0,0,0,0.60)', backdropFilter: 'blur(10px)' }}
      onClick={onCancel}>
      <div className="animate-scale-in rounded-2xl p-6 mx-4 max-w-sm w-full"
        style={{ backgroundColor: 'var(--surface-secondary)', border: '1px solid var(--border)' }}
        onClick={(e) => e.stopPropagation()}>
        <h3 className="text-base font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>{title}</h3>
        <p className="text-sm mb-6" style={{ color: 'var(--text-secondary)' }}>{message}</p>
        <div className="flex gap-3 justify-end">
          <button onClick={onCancel} className="btn-secondary text-sm px-4 py-2">取消</button>
          <button onClick={onConfirm} className="text-sm px-4 py-2 rounded-xl font-medium"
            style={{ backgroundColor: 'var(--danger)', color: '#fff' }}>确认删除</button>
        </div>
      </div>
    </div>
  )
}

export default function Dictionary() {
  const navigate = useNavigate()
  const [books, setBooks] = useState([])
  const [bookProgress, setBookProgress] = useState({})
  const [activeBook, setActiveBook] = useState(null)
  const [entries, setEntries] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState(null)
  const [importError, setImportError] = useState(null)
  const [importFormat, setImportFormat] = useState('txt')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [tab, setTab] = useState('books')
  const [deleteTarget, setDeleteTarget] = useState(null)  // book to delete
  const [showResetModal, setShowResetModal] = useState(false)
  const [alertMsg, setAlertMsg] = useState(null)
  const fileInputRef = useRef(null)

  // ── Load data ──
  const fetchBooks = useCallback(async () => {
    try {
      const data = await api.listBooks()
      const booksList = data.books || []
      setBooks(booksList)
      // Load progress for each book
      const progressMap = {}
      await Promise.all(booksList.map(async (b) => {
        try {
          const resp = await fetch(`/api/books/${b.id}/progress`).then(r => r.json())
          if (!resp.error) progressMap[b.id] = resp
        } catch (e) { /* ignore */ }
      }))
      setBookProgress(progressMap)
    } catch (e) { console.error(e) }
  }, [])

  const fetchActiveBook = useCallback(async () => {
    try {
      const data = await api.getActiveBook()
      if (data.book) setActiveBook(data.book)
    } catch (e) { console.error(e) }
  }, [])

  const fetchEntries = useCallback(async () => {
    if (!activeBook?.id) return
    setLoading(true)
    try {
      const data = await api.getDictionaryEntries(page, PER_PAGE, activeBook.id)
      setEntries(data.entries || [])
      setTotal(data.total || 0)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [page, activeBook])

  useEffect(() => { fetchBooks(); fetchActiveBook() }, [])
  useEffect(() => { fetchEntries() }, [fetchEntries])

  const totalPages = Math.max(1, Math.ceil(total / PER_PAGE))

  // ── Book actions ──
  const handleActivateBook = async (bookId) => {
    try {
      await api.activateBook(bookId)
      await fetchBooks()
      const resp = await fetch('/api/books/active').then(r => r.json())
      if (resp.book) setActiveBook(resp.book)
      setPage(1)
    } catch (e) { console.error(e) }
  }

  const handleDeleteBook = async (book) => {
    if (book.is_builtin) return
    setDeleteTarget(book)
  }

  const doReset = async () => {
    setShowResetModal(false)
    if (!activeBook) return
    try {
      await api.resetProgress(activeBook.id)
      setAlertMsg('学习进度已重置！')
      fetchBooks()
    } catch (e) {
      setAlertMsg('重置失败: ' + (e.message || '未知错误'))
    }
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    const book = deleteTarget
    setDeleteTarget(null)
    try {
      const result = await api.deleteBook(book.id)
      if (result.error) throw new Error(result.error)
      await fetchBooks()
      if (activeBook?.id === book.id) {
        setActiveBook(null)
        setEntries([])
        fetchActiveBook()
      }
    } catch (e) { console.error(e) }
  }

  // ── File import ──
  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    // Auto-detect format
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (FORMATS[ext]) setImportFormat(ext)

    setImporting(true)
    setImportError(null)
    setImportResult(null)
    try {
      // Decode the file as UTF-8 first; fall back to GBK for legacy Chinese
      // word lists so 中文词书 encoded in GBK import correctly instead of
      // producing mojibake or failing silently.
      const buf = await file.arrayBuffer()
      let content
      try {
        content = new TextDecoder('utf-8', { fatal: true }).decode(buf)
      } catch {
        content = new TextDecoder('gbk').decode(buf)
      }

      const fmt = FORMATS[ext] ? ext : 'txt'
      const name = file.name.replace(/\.[^.]+$/, '')
      const resp = await fetch(`/api/dictionary/import/raw?book_name=${encodeURIComponent(name)}&file_format=${fmt}`, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain' },
        body: content,
      })
      const data = await resp.json()
      if (data.error) {
        setImportError(data.error)
      } else {
        setImportResult(data)
        await fetchBooks()
      }
    } catch (e) {
      setImportError('导入失败: ' + (e.message || '未知错误'))
    } finally {
      setImporting(false)
    }
    // Reset input for re-selection
    e.target.value = ''
  }

  // ── Search ──
  const handleSearch = async () => {
    if (!searchQuery.trim()) { setSearchResults(null); return }
    setSearchLoading(true)
    try {
      const data = await api.searchDictionary(searchQuery, 50, activeBook?.id)
      setSearchResults(data)
    } catch (e) { console.error(e) }
    finally { setSearchLoading(false) }
  }

  const speakWord = (word) => {
    if (!window.speechSynthesis || !word) return
    speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(String(word).trim())
    utterance.lang = 'en-US'
    utterance.rate = 0.88
    speechSynthesis.speak(utterance)
  }

  // ── Render helper ──
  const Badge = ({ children, color, bg }) => (
    <span className="badge" style={{ color: color || 'var(--text-secondary)', backgroundColor: bg || 'var(--surface-tertiary)' }}>
      {children}
    </span>
  )

  return (
    <div className="page animate-fade-in">
      <h1 className="text-2xl font-bold tracking-tight mb-1" style={{ color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
        词库管理
      </h1>
      <p className="text-sm mb-6" style={{ color: 'var(--text-tertiary)' }}>
        {activeBook
          ? `当前词书: ${activeBook.book_name} · ${activeBook.word_count?.toLocaleString()} 词`
          : '管理你的词库和词典'}
      </p>

      {/* ═══ AI 材料分析入口 ═══ */}
      <button onClick={() => navigate('/material')}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: '0.75rem',
          padding: '0.9rem 1rem', marginBottom: '1rem', borderRadius: 'var(--radius-lg)',
          backgroundColor: 'var(--accent-subtle)', border: '1px solid color-mix(in srgb, var(--accent) 22%, transparent)',
          cursor: 'pointer', textAlign: 'left',
        }}>
        <div style={{ width: 36, height: 36, borderRadius: '10px', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--accent)' }}>
          <Sparkles size={18} style={{ color: '#fff' }} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>AI 材料分析</div>
          <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>从文章提取重点词汇，一键生成词书</div>
        </div>
      </button>

      {/* ═══ Tabs ═══ */}
      <div className="flex gap-1 mb-6 p-1 rounded-xl" style={{ backgroundColor: 'var(--surface-tertiary)' }}>
        {[
          { key: 'books', icon: BookMarked, label: '词书' },
          { key: 'browse', icon: Search, label: '浏览' },
          { key: 'import', icon: FileUp, label: '导入' },
        ].map(({ key, icon: Icon, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all"
            style={{
              backgroundColor: tab === key ? 'var(--surface-secondary)' : 'transparent',
              color: tab === key ? 'var(--text-primary)' : 'var(--text-tertiary)',
              boxShadow: tab === key ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
            }}>
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      {/* ═══════════════════════ BOOKS TAB ═══════════════════════ */}
      {tab === 'books' && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
            {books.map((book) => {
              const isActive = activeBook?.id === book.id || book.is_active
              return (
                <div key={book.id}
                  className="card-interactive relative"
                  style={{
                    borderColor: isActive ? 'var(--accent)' : 'var(--border)',
                    borderWidth: isActive ? '2px' : '1px',
                  }}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                      style={{ backgroundColor: isActive ? 'var(--accent-subtle)' : 'var(--surface-tertiary)' }}>
                      <BookOpen size={18} style={{ color: isActive ? 'var(--accent)' : 'var(--text-tertiary)' }} />
                    </div>
                    {isActive && <Badge color="var(--accent)" bg="var(--accent-subtle)">使用中</Badge>}
                  </div>
                  <h3 className="text-sm font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
                    {book.book_name}
                  </h3>
                  <div className="flex items-center gap-3 text-xs mb-3" style={{ color: 'var(--text-tertiary)' }}>
                    <span className="flex items-center gap-1"><Database size={11} /> {book.word_count?.toLocaleString()} 词</span>
                    {book.file_name && <span className="flex items-center gap-1"><FileText size={11} /> {book.file_name}</span>}
                  </div>
                  <div className="flex gap-2">
                    {!isActive && (
                      <button onClick={() => handleActivateBook(book.id)}
                        className="flex items-center gap-1.5 text-xs py-2 px-4 rounded-xl font-medium flex-1 justify-center transition-all"
                        style={{ backgroundColor: 'var(--accent)', color: '#fff' }}>
                        <Play size={12} /> 启用
                      </button>
                    )}
                    {isActive && (
                      <div className="text-xs py-2 px-4 rounded-xl font-medium flex-1 text-center"
                        style={{ backgroundColor: 'var(--surface-tertiary)', color: 'var(--text-secondary)' }}>
                        <CheckCircle2 size={12} className="inline mr-1" />当前词书
                      </div>
                    )}
                    {!book.is_builtin && (
                      <button onClick={() => handleDeleteBook(book)}
                        className="p-2 rounded-xl hover:bg-[var(--danger-subtle)] transition-all"
                        style={{ color: 'var(--text-tertiary)' }} title="删除">
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                  {/* Progress bar */}
                  {bookProgress[book.id] && (
                    <div className="mt-3 pt-3 border-t" style={{ borderColor: 'var(--border)' }}>
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px]" style={{ color: 'var(--text-tertiary)' }}>学习进度</span>
                          {bookProgress[book.id].review_due > 0 && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                              style={{ backgroundColor: 'var(--accent-subtle)', color: 'var(--accent)' }}>
                              {bookProgress[book.id].review_due} 待复习
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] font-medium" style={{ color: 'var(--text-primary)' }}>
                          {bookProgress[book.id].studied_words}/{bookProgress[book.id].total_words} · {bookProgress[book.id].progress_percent}%
                        </span>
                      </div>
                      <div className="progress" style={{ height: 4 }}>
                        <div className="progress-fill" style={{ width: `${bookProgress[book.id].progress_percent}%` }} />
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Delete confirmation dialog */}
          <ConfirmDialog
            open={!!deleteTarget}
            title="确认删除词书"
            message={`是否删除该词书「${deleteTarget?.book_name}」？该词书独有的单词、学习记录和复习计划也会同时删除，不会影响其他词书。此操作不可撤销。`}
            onConfirm={confirmDelete}
            onCancel={() => setDeleteTarget(null)}
          />

          {/* Quick stats */}
          {activeBook && (
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>词书统计</h3>
                <button
                  onClick={() => setShowResetModal(true)}
                  className="flex items-center gap-1.5 text-xs py-1.5 px-3 rounded-full font-medium transition-all hover:opacity-80"
                  style={{ backgroundColor: 'var(--danger-subtle)', color: 'var(--danger)' }}>
                  <RotateCcw size={12} />
                  重置进度
                </button>
              </div>
              <div className="grid grid-cols-4 gap-3 text-center">
                <div>
                  <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{activeBook.word_count?.toLocaleString()}</div>
                  <div className="stat-label">总词汇</div>
                </div>
                <div>
                  <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                    {bookProgress[activeBook.id]?.studied_words?.toLocaleString() ?? '-'}
                  </div>
                  <div className="stat-label">已学习</div>
                </div>
                <div>
                  <div className="text-lg font-bold" style={{ color: 'var(--accent)' }}>
                    {bookProgress[activeBook.id]?.review_due?.toLocaleString() ?? '-'}
                  </div>
                  <div className="stat-label">待复习</div>
                </div>
                <div>
                  <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{books.length}</div>
                  <div className="stat-label">词书数量</div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* ═══════════════════════ BROWSE TAB ═══════════════════════ */}
      {tab === 'browse' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
              浏览词条 {total > 0 && <span className="font-normal" style={{ color: 'var(--text-tertiary)' }}>({total.toLocaleString()})</span>}
            </h3>
            <div className="flex items-center gap-2">
              <input type="text" value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="搜索单词..."
                className="input py-1.5 text-xs w-36" />
              <button onClick={handleSearch} className="btn-ghost p-2"><Search size={15} /></button>
            </div>
          </div>

          {/* Search results */}
          {searchResults && (
            <div className="mb-4 animate-slide-up">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>找到 {searchResults.total} 个结果</p>
                <button onClick={() => { setSearchResults(null); setSearchQuery('') }}
                  className="p-1" style={{ color: 'var(--text-tertiary)' }}><X size={14} /></button>
              </div>
              <div className="space-y-1 max-h-80 overflow-y-auto">
                {(searchResults.results || []).map((r) => (
                  <div key={r.id} className="p-2.5 rounded-lg flex items-center justify-between"
                    style={{ backgroundColor: 'var(--surface-tertiary)' }}>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{r.word}</span>
                        {r.phonetic && <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{r.phonetic}</span>}
                      </div>
                      {r.definition_cn && <p className="text-xs mt-0.5 line-clamp-1" style={{ color: 'var(--text-secondary)' }}>{r.definition_cn}</p>}
                    </div>
                    <button onClick={() => speakWord(r.word)}
                      className="p-1.5 rounded-lg hover:bg-[var(--surface)]" style={{ color: 'var(--text-tertiary)' }}>
                      <Volume2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Entry list */}
          {!activeBook && (
            <div className="text-center py-12">
              <BookOpen size={36} className="mx-auto mb-3" style={{ color: 'var(--text-tertiary)' }} />
              <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>请先在"词书"标签中选择一本词书</p>
            </div>
          )}

          {activeBook && loading && (
            <div className="flex justify-center py-8">
              <RefreshCw size={20} className="animate-spin" style={{ color: 'var(--text-tertiary)' }} />
            </div>
          )}

          {activeBook && !loading && !searchResults && entries.length === 0 && (
            <div className="text-center py-12">
              <BookOpen size={36} className="mx-auto mb-3" style={{ color: 'var(--text-tertiary)' }} />
              <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>词书为空，请导入词汇</p>
            </div>
          )}

          {activeBook && !loading && !searchResults && entries.length > 0 && (
            <>
              <div className="space-y-1">
                {entries.map((e) => (
                  <div key={e.id} className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-[var(--surface-tertiary)] transition-colors">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{e.word}</span>
                        {e.phonetic && <span className="text-xs truncate" style={{ color: 'var(--text-tertiary)' }}>{e.phonetic}</span>}
                      </div>
                      {e.definition && (
                        <p className="text-xs truncate" style={{ color: 'var(--text-secondary)' }}>{e.definition}</p>
                      )}
                    </div>
                    <button onClick={() => speakWord(e.word)}
                      className="p-1.5 rounded-lg hover:bg-[var(--surface)] ml-2 transition-colors"
                      style={{ color: 'var(--text-tertiary)' }}>
                      <Volume2 size={13} />
                    </button>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-3 mt-4 pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}
                    className="btn-ghost p-2 disabled:opacity-30"><ChevronLeft size={16} /></button>
                  <span className="text-xs tabular-nums" style={{ color: 'var(--text-tertiary)' }}>{page} / {totalPages}</span>
                  <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
                    className="btn-ghost p-2 disabled:opacity-30"><ChevronRight size={16} /></button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ═══════════════════════ IMPORT TAB ═══════════════════════ */}
      {tab === 'import' && (
        <div className="space-y-6">
          {/* Format info cards */}
          <div className="grid grid-cols-3 gap-3">
            {Object.entries(FORMATS).map(([key, fmt]) => (
              <div key={key}
                className={`card-interactive text-center ${importFormat === key ? '' : ''}`}
                style={{ borderColor: importFormat === key ? 'var(--accent)' : 'var(--border)' }}
                onClick={() => setImportFormat(key)}>
                <FileText size={20} className="mx-auto mb-2" style={{ color: importFormat === key ? 'var(--accent)' : 'var(--text-tertiary)' }} />
                <div className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>{fmt.label}</div>
                <div className="text-[10px] mt-1" style={{ color: 'var(--text-tertiary)' }}>{fmt.ext}</div>
              </div>
            ))}
          </div>

          {/* Upload area */}
          <div
            className="card-interactive flex flex-col items-center justify-center gap-4 py-12 cursor-pointer border-dashed"
            style={{ borderStyle: 'dashed', borderColor: 'var(--border-strong)' }}
            onClick={() => fileInputRef.current?.click()}>
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
              style={{ backgroundColor: 'var(--surface-tertiary)' }}>
              <FileUp size={28} style={{ color: 'var(--text-tertiary)' }} />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>
                点击选择文件
              </p>
              <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                支持 {importFormat.toUpperCase()} 格式 · 文件名将作为词书名称
              </p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.csv,.json"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {/* Format example */}
          <div className="card">
            <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
              {importFormat.toUpperCase()} 格式示例
            </h3>
            <pre className="text-xs p-4 rounded-xl overflow-x-auto" style={{
              backgroundColor: 'var(--surface-tertiary)',
              color: 'var(--text-secondary)',
              fontFamily: 'var(--font-mono, monospace)',
              lineHeight: 1.8,
            }}>
              {importFormat === 'txt' && 'word\tphonetic\tchinese\texample_en\texample_cn\nabandon\t/əˈbændən/\t放弃\tHe abandoned his plan.\t他放弃了计划。\nability\t/əˈbɪləti/\t能力\tShe has great ability.\t她很有能力。'}
              {importFormat === 'csv' && 'word,phonetic,chinese,example_en,example_cn\nabandon,/əˈbændən/,放弃,He abandoned his plan.,他放弃了计划。\nability,/əˈbɪləti/,能力,She has great ability.,她很有能力。'}
              {importFormat === 'json' && '[\n  {\n    "word": "abandon",\n    "phonetic": "/əˈbændən/",\n    "chinese": "放弃",\n    "example_en": "He abandoned his plan.",\n    "example_cn": "他放弃了计划。"\n  },\n  {\n    "word": "ability",\n    "phonetic": "/əˈbɪləti/",\n    "chinese": "能力"\n  }\n]'}
            </pre>
          </div>

          {/* Import progress & result */}
          {importing && (
            <div className="card animate-slide-up text-center">
              <Loader2 size={24} className="animate-spin mx-auto mb-3" style={{ color: 'var(--accent)' }} />
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>正在导入词库...</p>
            </div>
          )}

          {importError && (
            <div className="p-4 rounded-xl animate-slide-up" style={{ backgroundColor: 'var(--danger-subtle)' }}>
              <div className="flex items-center gap-2">
                <AlertTriangle size={14} style={{ color: 'var(--danger)' }} />
                <span className="text-sm" style={{ color: 'var(--danger)' }}>{importError}</span>
              </div>
            </div>
          )}

          {importResult && (
            <div className="p-6 rounded-2xl animate-slide-up text-center" style={{ backgroundColor: 'var(--success-subtle)' }}>
              <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-3"
                style={{ backgroundColor: 'var(--success)', color: '#fff' }}>
                <CheckCircle2 size={28} />
              </div>
              <h3 className="text-lg font-bold mb-1" style={{ color: 'var(--text-primary)' }}>导入成功！</h3>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="text-center">
                  <div className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{importResult.book_name}</div>
                  <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>词书名称</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{importResult.imported?.toLocaleString()}</div>
                  <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>导入单词</div>
                </div>
              </div>
              <button onClick={() => { setImportResult(null); setTab('books') }}
                className="btn-primary mt-4 text-sm">
                查看词书
              </button>
            </div>
          )}
        </div>
      )}

      {/* Reset confirm modal */}
      <Modal
        open={showResetModal}
        onClose={() => setShowResetModal(false)}
        title="重置学习进度？"
        message={'确定要重置「' + (activeBook?.book_name || '') + '」的学习进度吗？\n\n这将清除该词书的所有学习记录、记忆状态和复习进度。\n\n词书和单词数据会保留。'}
        confirmLabel="确认重置"
        cancelLabel="取消"
        onConfirm={doReset}
        danger
      />

      <AlertModal
        open={!!alertMsg}
        onClose={() => setAlertMsg(null)}
        title="提示"
        message={alertMsg || ''}
      />
    </div>
  )
}
