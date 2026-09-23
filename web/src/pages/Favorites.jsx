import { useState, useEffect } from 'react'
import { Star, Volume2, CheckCircle2, BookOpen, Sparkles } from 'lucide-react'
import { api } from '../api'
import AIPanel from '../components/AIPanel'

export default function Favorites() {
  const [words, setWords] = useState([])
  const [loading, setLoading] = useState(true)
  const [aiWord, setAiWord] = useState(null)

  const fetchFavorites = () => {
    setLoading(true)
    api.getFavorites()
      .then(setWords)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchFavorites() }, [])

  const handleToggleFavorite = async (wordId) => {
    try {
      await api.toggleFavorite(wordId)
      setWords((prev) => prev.filter((w) => w.id !== wordId))
    } catch (e) { console.error(e) }
  }

  const speakWord = (word, lang = 'en-US') => {
    if (!window.speechSynthesis) return
    speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(word)
    utterance.lang = lang
    utterance.rate = 0.88
    speechSynthesis.speak(utterance)
  }

  return (
    <div className="page animate-fade-in">
      <h1 className="text-2xl font-bold tracking-tight mb-1" style={{ color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
        收藏单词
      </h1>
      <p className="text-sm mb-6" style={{ color: 'var(--text-tertiary)' }}>
        {words.length > 0 ? `${words.length} 个收藏单词` : '你收藏的所有单词'}
      </p>

      {loading && (
        <div className="flex justify-center py-12">
          <div
            className="w-5 h-5 border-2 rounded-full animate-spin"
            style={{ borderColor: 'var(--border)', borderTopColor: 'var(--text-primary)' }}
          />
        </div>
      )}

      {!loading && words.length === 0 && (
        <div className="text-center py-16">
          <BookOpen size={40} className="mx-auto mb-4" style={{ color: 'var(--text-tertiary)' }} />
          <p className="text-sm mb-1" style={{ color: 'var(--text-secondary)' }}>还没有收藏的单词</p>
          <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
            在学习或搜索时点击星标即可收藏
          </p>
        </div>
      )}

      <div className="space-y-2">
        {words.map((word) => (
          <div key={word.id}>
            <div className="card-interactive flex items-start justify-between gap-4 group">
              <div
                className="flex-1 min-w-0"
                onClick={() => setAiWord(aiWord?.id === word.id ? null : word)}
              >
                <div className="flex items-center gap-2 mb-0.5">
                  <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {word.english}
                  </h3>
                  {word.is_mastered && <CheckCircle2 size={15} style={{ color: 'var(--success)' }} />}
                  <button
                    onClick={(e) => { e.stopPropagation(); speakWord(word.english) }}
                    className="p-1 rounded transition-all opacity-0 group-hover:opacity-100 hover:bg-[var(--surface-tertiary)]"
                    style={{ color: 'var(--text-tertiary)' }}
                  >
                    <Volume2 size={13} />
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); setAiWord(word) }}
                    className="p-1 rounded transition-all opacity-0 group-hover:opacity-100 hover:bg-[var(--surface-tertiary)]"
                    style={{ color: 'var(--text-tertiary)' }}
                    title="AI 解释"
                  >
                    <Sparkles size={13} />
                  </button>
                </div>
                <p className="text-xs mb-0.5" style={{ color: 'var(--text-tertiary)' }}>{word.phonetic}</p>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{word.chinese}</p>
                <p className="text-xs mt-1 italic line-clamp-1" style={{ color: 'var(--text-tertiary)' }}>
                  {word.example_en}
                </p>

                {/* Proficiency */}
                {word.proficiency > 0 && (
                  <div className="flex items-center gap-1.5 mt-2">
                    {[1, 2, 3, 4, 5].map((lvl) => (
                      <div
                        key={lvl}
                        className="w-2.5 h-1 rounded-full"
                        style={{
                          backgroundColor: lvl <= word.proficiency ? 'var(--text-primary)' : 'var(--border)',
                        }}
                      />
                    ))}
                  </div>
                )}
              </div>

              <button
                onClick={() => handleToggleFavorite(word.id)}
                className="p-2 rounded-lg transition-all flex-shrink-0"
                style={{ color: '#f59e0b' }}
              >
                <Star size={17} fill="currentColor" />
              </button>
            </div>

            {/* AI Panel */}
            {aiWord?.id === word.id && (
              <div className="mt-2 ml-2 animate-slide-up">
                <AIPanel word={word} onClose={() => setAiWord(null)} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
