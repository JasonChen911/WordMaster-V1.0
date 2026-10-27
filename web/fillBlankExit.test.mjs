/**
 * FillBlank "退出" (exit) vs "再来一轮" (restart) separation — regression guard.
 *
 * The reported bug: clicking "退出" in 挖空填词 did not leave the game, it
 * reloaded / re-initialised it (the top-left back button and the Escape key were
 * both wired to handleRestart — the same handler as "再来一轮"). This test
 * statically asserts the source keeps exit and restart fully separated.
 *
 * Run:  node web/fillBlankExit.test.mjs
 */

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const here = path.dirname(fileURLToPath(import.meta.url))
const src = readFileSync(path.join(here, 'src', 'components', 'FillBlank.jsx'), 'utf8')
const lines = src.split('\n')

let PASS = 0, FAIL = 0
const check = (name, cond, detail = '') => {
  if (cond) { PASS++; console.log(`  OK   ${name}`) }
  else { FAIL++; console.log(`  FAIL ${name} | ${detail}`) }
}

// ── 1. handleExit and handleRestart are two distinct handlers ──
check('handleExit is defined', /\bconst handleExit\s*=\s*\(\)\s*=>/.test(src))
check('handleRestart is defined', /\bconst handleRestart\s*=\s*\(\)\s*=>/.test(src))

// ── 2. handleExit performs full cleanup then leaves ──
const exitBody = (src.match(/const handleExit\s*=\s*\(\)\s*=>\s*\{([\s\S]*?)\n  \}/) || [])[1] || ''
check('handleExit calls onBack() (leaves the game)', /onBack\(\)/.test(exitBody), 'must call onBack to unmount')
check('handleExit stops TTS (stopTts)', /stopTts\(\)/.test(exitBody))
check('handleExit clears interval timer (letterTimer)', /clearInterval\(letterTimer/.test(exitBody))
check('handleExit clears auto-advance timeout', /clearTimeout\(autoAdvanceTimer/.test(exitBody))
check('handleExit invalidates in-flight fetch (roundRef++)', /roundRef\.current\+\+/.test(exitBody))
check('handleExit marks session exited (exitedRef=true)', /exitedRef\.current\s*=\s*true/.test(exitBody))

// ── 3. No back button / icon-button is ever wired to handleRestart ──
const iconButtonRestart = lines.filter(l => /ios-icon-button/.test(l) && /handleRestart/.test(l))
check('no ios-icon-button (back arrow) is wired to handleRestart', iconButtonRestart.length === 0, `offenders: ${iconButtonRestart.length}`)

const backAriaRestart = lines.filter(l => /aria-label="Back"/.test(l) && /handleRestart/.test(l))
check('no aria-label="Back" button is wired to handleRestart', backAriaRestart.length === 0, `offenders: ${backAriaRestart.length}`)

// ── 4. The playing-phase back arrow uses handleExit ──
check('playing back arrow (aria-label="Back") uses handleExit',
  lines.some(l => /aria-label="Back"/.test(l) && /onClick=\{handleExit\}/.test(l)))

// ── 5. Escape exits (never restarts) in both playing and done phases ──
const keydownFn = (src.match(/const handleKeyDown\s*=\s*\(e\)\s*=>\s*\{([\s\S]*?)\n  \}/) || [])[1] || ''
const escBranch = keydownFn.split("e.key === 'Escape'")[1] || ''
check('playing-phase Escape calls handleExit (not handleRestart)',
  /handleExit\(\)/.test(escBranch) && !/handleRestart\(\)/.test(escBranch))

const doneHandler = (src.match(/if \(phase !== 'done'\) return[\s\S]*?const handler = \(e\) => \{([\s\S]*?)\n    \}/) || [])[1] || ''
const doneEsc = doneHandler.split("e.key === 'Escape'")[1] || ''
check('done-phase Escape calls handleExit (not handleRestart)',
  /handleExit\(\)/.test(doneEsc) && !/handleRestart\(\)/.test(doneEsc))

// ── 6. "再来一轮" still restarts (restart is preserved, not removed) ──
check('"再来一轮" button still calls handleRestart',
  lines.some(l => /onClick=\{handleRestart\}/.test(l)))

// ── 7. loadGameWords drops stale async results after exit / newer round ──
const loadBody = (src.match(/const loadGameWords\s*=\s*async \(book\)\s*=>\s*\{([\s\S]*?)\n  \}\n/) || [])[1] || ''
check('loadGameWords bumps a monotonic round id', /\bconst round = \+\+roundRef\.current/.test(loadBody))
check('loadGameWords guards after await (exitedRef/roundRef)',
  /if \(exitedRef\.current \|\| roundRef\.current !== round\) return/.test(loadBody))

console.log()
console.log(`  RESULT: ${PASS} PASSED, ${FAIL} FAILED  (${PASS + FAIL} checks)`)
process.exit(FAIL ? 1 : 0)
