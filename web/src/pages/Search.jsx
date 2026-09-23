import { useState, useEffect, useCallback, useRef } from 'react'
import { Search as SearchIcon, Volume2, Sparkles, X, BookOpen, ChevronRight } from 'lucide-react'
import { api } from '../api'
import { speak } from '../tts'

function playWord(word, accent) {
  if (!word) return
  speak(word, { accent: accent === 'uk' ? 'uk' : 'us' })
}

export default function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [selectedWord, setSelectedWord] = useState(null)
  const [selectedLoading, setSelectedLoading] = useState(false)
  const [activeAccent, setActiveAccent] = useState('us')
  const inputRef = useRef(null)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 250)
    return () => clearTimeout(timer)
  }, [query])

  const doSearch = useCallback(async (q) => {
    if (!q.trim()) { setResults([]); setSelectedWord(null); return }
    setLoading(true)
    try {
      const data = await api.searchAll(q)
      const sw = (data.study_words || []).map(w => ({ ...w, _type: 'study' }))
      const dw = (data.dictionary_results || []).map(d => ({
        id: d.id, english: d.word, phonetic: d.phonetic, definition_cn: d.definition_cn,
        definition_en: d.definition_en, part_of_speech: d.part_of_speech,
        example: d.example, example_translation: d.example_translation,
        audio_us: d.audio_us, audio_uk: d.audio_uk,
        synonyms: d.synonyms, antonyms: d.antonyms, _type: 'dictionary', _source: d.source,
      }))
      setResults([...sw, ...dw])
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }, [])

  useEffect(() => { doSearch(debouncedQuery) }, [debouncedQuery, doSearch])
  useEffect(() => { inputRef.current?.focus() }, [])

  const handleSelectWord = async (word) => {
    setSelectedLoading(true)
    setSelectedWord(word)
    setActiveAccent('us')
    // Auto-play US pronunciation
    setTimeout(() => playWord(word.english || word.word, 'us'), 400)
    setSelectedLoading(false)
  }

  const clearSearch = () => { setQuery(''); setResults([]); setSelectedWord(null) }

  return (
    <div className="page animate-fade-in">
      {/* Search bar — glass */}
      <div className="glass rounded-2xl p-4 mb-6 sticky top-16 z-40" style={{ backdropFilter: 'blur(40px)' }}>
        <div className="relative">
          <SearchIcon size={18} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-tertiary)' }} />
          <input ref={inputRef} type="text" value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search English or Chinese..."
            className="input pl-11 pr-11 py-3 text-base border-0 bg-transparent"
            style={{ fontSize: '1.1rem', fontWeight: 400 }}
            autoFocus
          />
          {query && (
            <button onClick={clearSearch} className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-xl hover:bg-[var(--surface-tertiary)]" style={{ color: 'var(--text-tertiary)' }}>
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-12">
          <div className="w-6 h-6 border-2 rounded-full animate-spin" style={{ borderColor: 'var(--border)', borderTopColor: 'var(--accent)' }} />
        </div>
      )}

      {/* Empty state */}
      {!loading && !query && (
        <div className="text-center py-20 animate-scale-in">
          <div className="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-6 glass">
            <BookOpen size={28} style={{ color: 'var(--text-tertiary)' }} />
          </div>
          <p className="text-lg font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Dictionary</p>
          <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>Type a word to look up its meaning</p>
        </div>
      )}

      {/* Professional dictionary view for selected word */}
      {selectedWord && !loading && (
        <div className="animate-slide-up mb-8">
          <div className="glass rounded-3xl p-8" style={{ backdropFilter: 'blur(40px)' }}>
            {/* Word header */}
            <div className="flex items-start justify-between mb-6">
              <div>
                <h1 className="text-4xl font-bold tracking-tight mb-1" style={{ color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
                  {selectedWord.english || selectedWord.word}
                </h1>
                <div className="flex items-center gap-3">
                  {selectedWord.phonetic && (
                    <span className="text-lg" style={{ color: 'var(--text-tertiary)' }}>{selectedWord.phonetic}</span>
                  )}
                  {selectedWord.part_of_speech && (
                    <span className="badge glass" style={{ color: 'var(--accent)', fontSize: '0.7rem' }}>
                      {selectedWord.part_of_speech}
                    </span>
                  )}
                  {selectedWord._source && (
                    <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>📖 {selectedWord._source}</span>
                  )}
                </div>
              </div>
            </div>

            {/* Pronunciation buttons */}
            <div className="flex items-center gap-3 mb-8">
              <button onClick={() => { setActiveAccent('us'); playWord(selectedWord.english || selectedWord.word, 'us') }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${
                  activeAccent === 'us' ? 'glass-shine' : ''
                }`}
                style={{
                  backgroundColor: activeAccent === 'us' ? 'var(--accent)' : 'var(--surface-tertiary)',
                  color: activeAccent === 'us' ? '#fff' : 'var(--text-secondary)',
                }}>
                <Volume2 size={15} /> US <span className="text-xs opacity-70">🇺🇸</span>
              </button>
              <button onClick={() => { setActiveAccent('uk'); playWord(selectedWord.english || selectedWord.word, 'uk') }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${
                  activeAccent === 'uk' ? 'glass-shine' : ''
                }`}
                style={{
                  backgroundColor: activeAccent === 'uk' ? 'var(--accent)' : 'var(--surface-tertiary)',
                  color: activeAccent === 'uk' ? '#fff' : 'var(--text-secondary)',
                }}>
                <Volume2 size={15} /> UK <span className="text-xs opacity-70">🇬🇧</span>
              </button>
            </div>

            {/* Chinese definition */}
            {selectedWord.definition_cn && (
              <div className="mb-6">
                <div className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-tertiary)' }}>释义</div>
                <p className="text-lg leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                  {selectedWord.definition_cn}
                </p>
              </div>
            )}

            {/* Fallback: old Chinese field */}
            {!selectedWord.definition_cn && selectedWord.chinese && (
              <div className="mb-6">
                <div className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-tertiary)' }}>释义</div>
                <p className="text-lg leading-relaxed" style={{ color: 'var(--text-primary)' }}>{selectedWord.chinese}</p>
              </div>
            )}

            {/* English definition */}
            {selectedWord.definition_en && (
              <div className="mb-6">
                <div className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-tertiary)' }}>Definition</div>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{selectedWord.definition_en}</p>
              </div>
            )}

            {/* Examples */}
            {(() => {
              let examples = []
              try {
                if (typeof selectedWord.example === 'string' && selectedWord.example.startsWith('[')) {
                  examples = JSON.parse(selectedWord.example)
                }
              } catch (e) {}
              if (examples.length === 0 && selectedWord.example_en) {
                examples = [{ en: selectedWord.example_en, cn: selectedWord.example_cn || '' }]
              }
              if (examples.length === 0 && selectedWord.example && !selectedWord.example.startsWith('[')) {
                examples = [{ en: selectedWord.example, cn: '' }]
              }
              if (examples.length === 0) return null
              return (
                <div className="mb-6">
                  <div className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--text-tertiary)' }}>例句</div>
                  <div className="space-y-4">
                    {examples.slice(0, 5).map((ex, i) => (
                      <div key={i} className="glass rounded-xl p-4">
                        <p className="text-sm italic leading-relaxed mb-1" style={{ color: 'var(--text-primary)' }}>{ex.en}</p>
                        {ex.cn && <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{ex.cn}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )
            })()}

            {/* Synonyms & Antonyms */}
            {(selectedWord.synonyms || selectedWord.antonyms) && (
              <div className="flex gap-4">
                {selectedWord.synonyms && (
                  <div className="flex-1">
                    <div className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--text-tertiary)' }}>Synonyms</div>
                    <p className="text-sm" style={{ color: 'var(--success)' }}>{selectedWord.synonyms}</p>
                  </div>
                )}
                {selectedWord.antonyms && (
                  <div className="flex-1">
                    <div className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--text-tertiary)' }}>Antonyms</div>
                    <p className="text-sm" style={{ color: 'var(--danger)' }}>{selectedWord.antonyms}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Search results list */}
      {!selectedWord && results.length > 0 && !loading && (
        <div className="space-y-2">
          {results.map((item) => (
            <div key={`${item._type}-${item.id}`}
              onClick={() => handleSelectWord(item)}
              className="glass rounded-2xl p-4 cursor-pointer flex items-center justify-between group animate-scale-in"
              style={{ backdropFilter: 'blur(20px)' }}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>{item.english || item.word}</span>
                  {item.phonetic && <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{item.phonetic}</span>}
                  {item.part_of_speech && <span className="badge" style={{ backgroundColor: 'var(--accent-subtle)', color: 'var(--accent)' }}>{item.part_of_speech}</span>}
                  {item._type === 'dictionary' && <span className="text-[10px]" style={{ color: 'var(--text-tertiary)' }}>📖 {item._source}</span>}
                </div>
                <p className="text-sm mt-0.5 truncate" style={{ color: 'var(--text-secondary)' }}>
                  {item.definition_cn || item.chinese || item.definition_en || ''}
                </p>
              </div>
              <div className="flex items-center gap-2 ml-3">
                <button onClick={(e) => { e.stopPropagation(); playWord(item.english || item.word) }}
                  className="p-2 rounded-xl opacity-0 group-hover:opacity-100 transition-all hover:bg-[var(--surface-tertiary)]" style={{ color: 'var(--accent)' }}>
                  <Volume2 size={16} />
                </button>
                <ChevronRight size={16} style={{ color: 'var(--text-tertiary)' }} />
              </div>
            </div>
          ))}
          <p className="text-xs text-center pt-4" style={{ color: 'var(--text-tertiary)' }}>{results.length} results</p>
        </div>
      )}
    </div>
  )
}
