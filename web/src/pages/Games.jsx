import { useState } from 'react'
import { ArrowLeft, Gamepad2, Shuffle, Type } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import WordPuzzle from '../components/WordPuzzle'
import FillBlank from '../components/FillBlank'

export default function Games() {
  const navigate = useNavigate()
  const [game, setGame] = useState(null) // null | 'puzzle' | 'fillblank'

  if (game === 'puzzle') {
    return <WordPuzzle onBack={() => setGame(null)} />
  }

  if (game === 'fillblank') {
    return <FillBlank onBack={() => setGame(null)} />
  }

  return (
    <div className="page" style={{ paddingTop: '2rem' }}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <button onClick={() => navigate('/')} className="ios-icon-button" aria-label="Back">
          <ArrowLeft size={19} />
        </button>
        <Gamepad2 size={22} style={{ color: 'var(--accent)' }} />
        <h1 className="text-xl font-bold tracking-tight" style={{ color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>
          小游戏
        </h1>
      </div>

      {/* Game Cards */}
      <div className="grid gap-4 sm:grid-cols-2">
        {/* Puzzle Game */}
        <button
          onClick={() => setGame('puzzle')}
          className="text-left p-6 rounded-2xl transition-all duration-300 hover:-translate-y-1"
          style={{
            backgroundColor: 'var(--surface-secondary)',
            border: '1px solid var(--border)',
            boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
          }}
        >
          <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
            style={{ backgroundColor: 'var(--accent-subtle)' }}>
            <Shuffle size={22} style={{ color: 'var(--accent)' }} />
          </div>
          <h3 className="text-base font-bold mb-1.5 tracking-tight" style={{ color: 'var(--text-primary)' }}>
            字母拼词
          </h3>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--text-tertiary)' }}>
            根据中文提示，将打乱的字母拖拽排序组成正确单词。
          </p>
        </button>

        {/* Fill Blank Game */}
        <button
          onClick={() => setGame('fillblank')}
          className="text-left p-6 rounded-2xl transition-all duration-300 hover:-translate-y-1"
          style={{
            backgroundColor: 'var(--surface-secondary)',
            border: '1px solid var(--border)',
            boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
          }}
        >
          <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
            style={{ backgroundColor: 'var(--accent-subtle)' }}>
            <Type size={22} style={{ color: 'var(--accent)' }} />
          </div>
          <h3 className="text-base font-bold mb-1.5 tracking-tight" style={{ color: 'var(--text-primary)' }}>
            挖空填词
          </h3>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--text-tertiary)' }}>
            根据例句和中文提示，填入正确的英文单词。
          </p>
        </button>
      </div>

      {/* Info footer */}
      <div className="mt-10 text-center">
        <p className="text-xs" style={{ color: 'var(--text-tertiary)', opacity: 0.5 }}>
          游戏数据来自当前词书 · 不影响学习记录
        </p>
      </div>
    </div>
  )
}
