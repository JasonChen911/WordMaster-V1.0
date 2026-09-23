import { AlertTriangle, RefreshCw, Home, ChevronDown, ChevronUp } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

/**
 * ErrorFallback — friendly error screen shown when ErrorBoundary catches an error.
 *
 * Designed to match WordMaster's iOS / Apple Design Language visual system.
 * Uses CSS custom properties (--surface, --text-primary, etc.) so it respects
 * the current light / dark theme.
 */
export default function ErrorFallback({ error, onReset }) {
  const navigate = useNavigate()
  const [showDetail, setShowDetail] = useState(false)

  const errorMessage = error?.message || String(error ?? 'Unknown error')

  const handleGoHome = () => {
    onReset?.()
    navigate('/', { replace: true })
  }

  const handleReload = () => {
    onReset?.()
    window.location.reload()
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-6"
      style={{ backgroundColor: 'var(--surface)' }}
    >
      <div
        className="rounded-2xl p-8 max-w-md w-full text-center animate-scale-in"
        style={{
          backgroundColor: 'var(--surface-secondary)',
          border: '1px solid var(--border)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
        }}
      >
        {/* Icon */}
        <div
          className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-5"
          style={{ backgroundColor: 'var(--warning-subtle)' }}
        >
          <AlertTriangle size={30} style={{ color: 'var(--warning)' }} />
        </div>

        {/* Title */}
        <h2
          className="text-lg font-bold mb-2"
          style={{ color: 'var(--text-primary)' }}
        >
          页面出现了问题
        </h2>

        {/* Description */}
        <p
          className="text-sm mb-6 leading-relaxed"
          style={{ color: 'var(--text-secondary)' }}
        >
          应用在渲染时遇到了意外错误。你的学习数据是安全的，请尝试以下操作。
        </p>

        {/* Error detail (collapsible) */}
        <div className="mb-6">
          <button
            onClick={() => setShowDetail(!showDetail)}
            className="flex items-center justify-center gap-1.5 mx-auto text-xs font-medium transition-all hover:opacity-70"
            style={{ color: 'var(--text-tertiary)' }}
          >
            {showDetail ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            错误详情
          </button>
          {showDetail && (
            <div
              className="rounded-xl p-3 mt-2 text-left text-xs font-mono whitespace-pre-wrap break-all"
              style={{
                backgroundColor: 'var(--surface-tertiary)',
                color: 'var(--text-tertiary)',
                maxHeight: '150px',
                overflow: 'auto',
              }}
            >
              {errorMessage}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={handleGoHome}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 hover:-translate-y-0.5 active:scale-95"
            style={{
              backgroundColor: 'var(--surface-tertiary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border)',
            }}
          >
            <Home size={15} />
            回首页
          </button>
          <button
            onClick={handleReload}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold text-white transition-all duration-200 hover:-translate-y-0.5 active:scale-95"
            style={{
              backgroundColor: 'var(--accent)',
              border: 'none',
            }}
          >
            <RefreshCw size={15} />
            刷新页面
          </button>
        </div>
      </div>
    </div>
  )
}
