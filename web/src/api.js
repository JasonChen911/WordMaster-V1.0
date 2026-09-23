const API_BASE = '/api'

// Default request timeout. The backend already enforces its own AI timeouts
// (30s chat / 90s reading); these frontend values are slightly longer so the
// UI surfaces a clean "timeout" message instead of an unhandled hang.
const DEFAULT_TIMEOUT = 40000

async function request(url, options = {}) {
  const { timeout = DEFAULT_TIMEOUT, ...fetchOptions } = options

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)

  try {
    const res = await fetch(`${API_BASE}${url}`, {
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      ...fetchOptions,
    })
    if (!res.ok) {
      let detail = `API error: ${res.status}`
      try {
        const body = await res.json()
        if (body && body.detail) detail = typeof body.detail === 'string' ? body.detail : detail
      } catch (_) { /* ignore body parse failure */ }
      throw new Error(detail)
    }
    return await res.json()
  } catch (e) {
    if (e.name === 'AbortError') {
      throw new Error('请求超时，请稍后重试。')
    }
    throw e
  } finally {
    clearTimeout(timer)
  }
}

export const api = {
  // Dashboard
  getDashboard: (bookId = null) => {
    const params = bookId ? `?book_id=${bookId}` : ''
    return request(`/dashboard${params}`)
  },
  getHome: () => request('/home'),

  // Words
  getTodayWords: (bookId = null) => {
    const params = bookId ? `?book_id=${bookId}` : ''
    return request(`/words/today${params}`)
  },
  getStudyQueue: (bookId = null, count = 20) => {
    const params = new URLSearchParams()
    if (bookId) params.set('book_id', String(bookId))
    params.set('count', String(count))
    return request(`/words/study-queue?${params}`)
  },
  getWord: (id) => request(`/words/${id}`),
  getWordFsrs: (id) => request(`/words/${id}/fsrs`),
  getAllWords: () => request('/words/all'),

  // Study
  recordStudy: (wordId, result, secondsSpent = 0, sessionId = '', responseTimeMs = 0) =>
    request('/study', {
      method: 'POST',
      body: JSON.stringify({ word_id: wordId, result, seconds_spent: secondsSpent, session_id: sessionId, response_time_ms: responseTimeMs }),
    }),

  // Learning events (exercise / confusion / reading answers)
  recordEvent: (event) => request('/events', {
    method: 'POST',
    body: JSON.stringify(event),
  }),

  resetProgress: (bookId = null) => {
    const params = bookId ? `?book_id=${bookId}` : ''
    return request(`/study/reset${params}`, { method: 'POST' })
  },

  toggleFavorite: (wordId) =>
    request(`/words/${wordId}/favorite`, { method: 'POST' }),

  // Stats
  getStats: () => request('/stats'),
  getWeeklyStats: () => request('/stats/weekly'),
  getErrorWords: () => request('/stats/errors'),

  // Search
  search: (q, favoriteOnly = false, masteredOnly = false) => {
    const params = new URLSearchParams({ q })
    if (favoriteOnly) params.set('favorite_only', 'true')
    if (masteredOnly) params.set('mastered_only', 'true')
    return request(`/search?${params}`)
  },

  getFavorites: () => request('/favorites'),

  // AI
  explainWord: (english, chinese) =>
    request('/ai/explain', {
      method: 'POST',
      body: JSON.stringify({ english, chinese }),
    }),

  explainWordDetail: (word) =>
    request('/word/explain', {
      method: 'POST',
      body: JSON.stringify({ word }),
    }),

  analyzeErrors: (errorWords) =>
    request('/ai/analyze-errors', {
      method: 'POST',
      body: JSON.stringify({ error_words: errorWords }),
    }),

  getAIStatus: () => request('/ai/status'),

  getQuiz: (quizType = 'multiple_choice', count = 5) =>
    request(`/ai/quiz?quiz_type=${quizType}&count=${count}`, { method: 'POST' }),

  getReport: () => request('/ai/report', { method: 'POST' }),

  // Reading (backend may take up to ~90s)
  generateReading: (params) => request('/ai/generate-reading', { method: 'POST', body: JSON.stringify(params), timeout: 100000 }),

  // AI Config
  getAIConfigStatus: () => request('/ai/config-status'),
  saveAIKey: (apiKey) => request('/ai/save-key', {
    method: 'POST',
    body: JSON.stringify({ api_key: apiKey }),
  }),
  testAIConnection: () => request('/ai/test-connection', { method: 'POST' }),

  // Audio — Edge Neural TTS
  getAudioUrl: (word, { voice = 'us', speed = 1.0 } = {}) =>
    `/api/audio/${encodeURIComponent(word)}?voice=${voice}&speed=${speed}`,

  getAudioStatus: (word, voice = 'us', speed = 1.0) =>
    request(`/audio/${encodeURIComponent(word)}/status?voice=${voice}&speed=${speed}`),

  getVoices: () => request('/audio/voices'),

  getAudioCacheStats: () => request('/audio/cache/stats'),

  clearAudioCache: () => request('/audio/cache', { method: 'DELETE' }),

  // Import raw data
  importRaw: (content, bookName, fileFormat = 'txt') =>
    fetch(`/api/dictionary/import/raw?book_name=${encodeURIComponent(bookName)}&file_format=${fileFormat}`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: content,
    }).then(r => r.json()),

  // Dictionary (MDX) + Books
  searchDictionary: (q, limit = 50, bookId = null) => {
    const params = new URLSearchParams({ q, limit: String(limit) })
    if (bookId) params.set('book_id', String(bookId))
    return request(`/dictionary/search?${params}`)
  },
  getDictionaryWord: (word, bookId = null) => {
    let url = `/dictionary/word/${encodeURIComponent(word)}`
    if (bookId) url += `?book_id=${bookId}`
    return request(url)
  },
  importDictionary: (filepath, bookName = '') => {
    const params = new URLSearchParams()
    params.set('filepath', filepath)
    if (bookName) params.set('book_name', bookName)
    return request(`/dictionary/import?${params}`, { method: 'POST' })
  },
  getImportProgress: (bookId) => request(`/dictionary/import/progress?book_id=${bookId}`),
  getDictionaryStats: () => request('/dictionary/stats'),
  getDictionaryEntries: (page = 1, perPage = 50, bookId = null) => {
    const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
    if (bookId) params.set('book_id', String(bookId))
    return request(`/dictionary/entries?${params}`)
  },
  clearDictionary: (bookId = 0) => {
    return request(`/dictionary/clear?book_id=${bookId}`, { method: 'DELETE' })
  },
  // Books
  listBooks: () => request('/books'),
  getActiveBook: () => request('/books/active'),
  activateBook: (bookId) => request(`/books/${bookId}/activate`, { method: 'POST' }),
  deleteBook: (bookId) => request(`/books/${bookId}`, { method: 'DELETE' }),
  getBookProgress: (bookId) => request(`/books/${bookId}/progress`),
  // Games
  getGamesWords: (count = 20, bookId = null) => {
    const params = new URLSearchParams({ count: String(count) })
    if (bookId) params.set('book_id', String(bookId))
    return request(`/games/words?${params}`)
  },

  // Combined search
  searchAll: (q, bookId = null) => {
    const params = new URLSearchParams({ q })
    if (bookId) params.set('book_id', String(bookId))
    return request(`/search/all?${params}`)
  },

  // Material Engine (AI 材料 → 词表)
  analyzeMaterial: (text, maxWords = 30) =>
    request('/material/analyze', {
      method: 'POST',
      body: JSON.stringify({ text, max_words: maxWords }),
      timeout: 70000,
    }),
  importMaterial: (bookName, words) =>
    request('/material/import', {
      method: 'POST',
      body: JSON.stringify({ book_name: bookName, words }),
    }),

  // AI example sentence (level-aware, cached)
  getExample: (word, level = 'CET4', force = false) =>
    request(`/ai/example?word=${encodeURIComponent(word)}&level=${encodeURIComponent(level)}&force=${force ? '1' : '0'}`, { timeout: 40000 }),

  // AI learning analysis (为什么总记不住)
  analyzeWordStruggle: (wordText, summary) =>
    request('/ai/word-analysis', {
      method: 'POST',
      body: JSON.stringify({ word: wordText, summary }),
      timeout: 40000,
    }),

  // AI exercises
  generateExercises: (words, exerciseType = 'multiple_choice', count = 5) =>
    request('/ai/exercises', {
      method: 'POST',
      body: JSON.stringify({ words, exercise_type: exerciseType, count }),
      timeout: 50000,
    }),

  // Learning insights (real stats) + confusion sets
  getInsights: () => request('/insights'),
  getConfusionSets: () => request('/confusion'),
  toggleConfusion: (setId) => request(`/confusion/${setId}/toggle`, { method: 'POST' }),
  getAIInsights: () => request('/ai/insights', { method: 'POST', timeout: 40000 }),

  // Reading → vocabulary loop
  addReadingWord: (word, meaning, example, sourceDocument, sourceSentence) =>
    request('/reading/add-word', {
      method: 'POST',
      body: JSON.stringify({ word, meaning, example, source_document: sourceDocument, source_sentence: sourceSentence }),
    }),
  getWordSource: (wordId) => request(`/words/${wordId}/source`),

  // Teacher MVP
  getTeacherOverview: () => request('/teacher/overview'),
  getTeacherReport: () => request('/teacher/report', { method: 'POST', timeout: 40000 }),
  createCourse: (name, description, bookId) =>
    request('/teacher/courses', {
      method: 'POST',
      body: JSON.stringify({ name, description, book_id: bookId }),
    }),

  // Mistake book (错词本)
  getMistakes: (source = 'all') => request(`/mistakes?source=${source}`),
  getMistakeStats: () => request('/mistakes/stats'),
  recordMistake: (word, source, mistakeType = '') =>
    request('/mistakes', {
      method: 'POST',
      body: JSON.stringify({ word, source, mistake_type: mistakeType }),
    }),
  addMistakeToReview: (wordId) => request(`/mistakes/${wordId}/review`, { method: 'POST' }),
  removeMistake: (wordId) => request(`/mistakes/${wordId}`, { method: 'DELETE' }),
}
