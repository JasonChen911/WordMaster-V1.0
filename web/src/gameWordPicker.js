/**
 * Shared word-selection helpers for the mini-games.
 *
 * Both the letter-scramble (字母拼词) and fill-blank games must build a
 * *shuffled* question pool and then walk it sequentially, so the first
 * question is drawn by the exact same logic as every later question — never a
 * hardcoded/fallback word and never a deterministic "words[0]".
 */

/** Fisher-Yates shuffle — returns a new array, never mutates the input. */
export function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

/**
 * Filter the raw word list to those usable for the letter-scramble game:
 * only a–z letters (≥3 distinct), and 3–12 letters long.
 */
export function pickWords(words) {
  return (words || []).filter((w) => {
    if (!w || typeof w.english !== 'string') return false
    const clean = w.english.toLowerCase().replace(/[^a-z]/g, '')
    if (clean.length < 3 || clean.length > 12) return false
    const unique = new Set(clean)
    return unique.size >= 3
  })
}

/**
 * Build a fresh, shuffled question pool for a new game session.
 *
 * Every new session calls this once and then advances by index, so the first
 * word and all subsequent words share the same draw logic (shuffled pool →
 * currentIndex=0 → sequential). Returns [] when the pool is empty so the
 * caller can render a proper empty state instead of a fake word.
 */
export function preparePuzzleWords(words) {
  return shuffle(pickWords(words))
}
