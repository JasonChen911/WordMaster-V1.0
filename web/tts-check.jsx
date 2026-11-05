// Development-only runtime harness using the actual production button/service.
import React from 'react'
import { createRoot } from 'react-dom/client'
import AudioControl from './src/components/AudioControl'
import { speakWord } from './src/tts'

const originalDebug = console.debug
console.debug = (...args) => {
  originalDebug(...args)
  if (String(args[0]).startsWith('[TTS')) document.getElementById('trace').textContent += args.join(' ') + '\n'
}
const words = ['telegram', 'abandon', 'apple', 'book', 'computer', 'dictionary', 'English', 'learn', 'school', 'voice']
createRoot(document.getElementById('root')).render(<>
  <h1>TTS runtime check</h1>
  {words.map(word => <p key={word}>{word} <AudioControl word={word} /></p>)}
  <button onClick={() => setTimeout(() => speakWord('telegram'), 420)}>Automatic telegram</button>
  <button onClick={() => words.forEach(word => speakWord(word))}>Rapid ten</button>
  <button onClick={() => speakWord('offline')}>Offline fallback</button>
</>)
