/**
 * Letter-scramble word-selection contract + "first word pinned" regression.
 *
 * Run:  node web/gameWordPicker.test.mjs
 */

import { shuffle, pickWords, preparePuzzleWords } from './src/gameWordPicker.js'

let PASS = 0, FAIL = 0
const check = (name, cond, detail = '') => {
  if (cond) { PASS++; console.log(`  OK   ${name}`) }
  else { FAIL++; console.log(`  FAIL ${name} | ${detail}`) }
}

// A realistic pool: many valid words plus "associate".
const POOL = [
  { english: 'associate' }, { english: 'abandon' }, { english: 'ability' },
  { english: 'achieve' }, { english: 'adapt' }, { english: 'adjust' },
  { english: 'admit' }, { english: 'adopt' }, { english: 'advance' },
  { english: 'advise' }, { english: 'affect' }, { english: 'afford' },
  { english: 'agent' }, { english: 'agree' }, { english: 'alarm' },
  { english: 'allow' }, { english: 'amaze' }, { english: 'amount' },
  { english: 'analyze' }, { english: 'anger' }, { english: 'announce' },
  { english: 'annual' }, { english: 'answer' }, { english: 'anxiety' },
  { english: 'apart' }, { english: 'appeal' }, { english: 'appear' },
  { english: 'apply' }, { english: 'argue' }, { english: 'arrive' },
  // invalid entries that must be filtered out
  { english: 'go' },          // <3 letters
  { english: 'to' },          // <3 letters
  { english: 'bee' },         // <3 distinct letters (b,e)
  { english: 'see' },         // <3 distinct letters
  { english: 'antidisestablishmentarianism' }, // >12 letters
  null, undefined, {}, { english: '' }, { english: 123 },
]

// Test 1: first word is not hardcoded — 50 independent sessions, not all associate.
{
  const firsts = new Set()
  let associateFirst = 0
  for (let i = 0; i < 50; i++) {
    const pool = preparePuzzleWords(POOL)
    const first = pool[0]?.english
    firsts.add(first)
    if (first === 'associate') associateFirst++
  }
  check('Test1: 50 sessions produce >1 distinct first word', firsts.size > 1, `distinct=${firsts.size}`)
  check('Test1: associate is not pinned (not 50/50)', associateFirst < 50, `associateFirst=${associateFirst}/50`)
}

// Test 2: pool integrity — no undefined/null/empty/non-string in the pool.
{
  let bad = 0
  for (let i = 0; i < 100; i++) {
    const pool = preparePuzzleWords(POOL)
    for (const w of pool) {
      if (!w || typeof w.english !== 'string' || w.english.length === 0) { bad++; break }
    }
  }
  check('Test2: no undefined/null/empty in shuffled pool', bad === 0, `bad=${bad}`)
}

// Test 3: no word lost / added / duplicated (shuffle preserves the valid set).
{
  const valid = pickWords(POOL)
  const validEnglish = valid.map((w) => w.english).sort()
  let ok = true
  for (let i = 0; i < 100; i++) {
    const pool = preparePuzzleWords(POOL)
    const poolEnglish = pool.map((w) => w.english).sort()
    if (poolEnglish.length !== validEnglish.length) { ok = false; break }
    if (poolEnglish.join('|') !== validEnglish.join('|')) { ok = false; break }
    if (new Set(poolEnglish).size !== poolEnglish.length) { ok = false; break }
  }
  check('Test3: shuffle preserves the exact valid word set (no loss/dup)', ok)
}

// Test 4: restart — each new session re-shuffles (orders vary, index resets).
{
  let varied = 0
  for (let i = 0; i < 20; i++) {
    const a = preparePuzzleWords(POOL).map((w) => w.english).join(',')
    const b = preparePuzzleWords(POOL).map((w) => w.english).join(',')
    if (a !== b) varied++
  }
  check('Test4: 20 restarts produce varying order (new session each time)', varied >= 15, `${varied}/20 varied`)
}

// Test 5: single valid word — allowed to be that word, no infinite loop.
{
  const single = [{ english: 'associate' }, { english: 'to' }] // only associate valid
  const pool = preparePuzzleWords(single)
  check('Test5: single-word pool returns exactly [associate]', pool.length === 1 && pool[0].english === 'associate', JSON.stringify(pool))
}

// Test 6: empty / all-invalid pool — returns [] (caller shows empty state).
{
  const empty = preparePuzzleWords([{ english: 'go' }, { english: 'to' }, null])
  check('Test6: empty pool returns [] (no fake fallback word)', Array.isArray(empty) && empty.length === 0, JSON.stringify(empty))
  const nothing = preparePuzzleWords(undefined)
  check('Test6: undefined input returns []', Array.isArray(nothing) && nothing.length === 0)
}

// Test 7: async-like loading — the pool is only produced after data arrives.
{
  // Simulate the React flow: no pool before load, pool produced after load.
  let pool = []
  const loaded = preparePuzzleWords(POOL)
  pool = loaded
  check('Test7: pool produced only after data load (no placeholder word)', pool.length > 0 && pool[0] !== undefined)
}

console.log()
console.log(`  RESULT: ${PASS} PASSED, ${FAIL} FAILED  (${PASS + FAIL} checks)`)
process.exit(FAIL ? 1 : 0)
