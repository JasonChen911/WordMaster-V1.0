import { useState, useEffect, useCallback } from 'react'
import { X } from 'lucide-react'

/**
 * WordMaster Modal — unified animation system.
 *
 * Enter: opacity 0→1, scale 0.95→1 (300ms)
 * Exit:  opacity 1→0, scale 1→0.96 (200ms)
 *
 * Usage:
 *   <Modal open={show} onClose={fn}
 *     title="Title" message="Body text"
 *     confirmLabel="确认" cancelLabel="取消"
 *     onConfirm={fn} danger />
 */

export default function Modal({
  open,
  onClose,
  title,
  message,
  children,
  confirmLabel = '确认',
  cancelLabel = '取消',
  onConfirm,
  danger = false,
}) {
  const [visible, setVisible] = useState(false)
  const [exiting, setExiting] = useState(false)

  useEffect(() => {
    if (open) {
      setVisible(true)
      setExiting(false)
    } else if (visible) {
      setExiting(true)
      const t = setTimeout(() => { setVisible(false); setExiting(false) }, 220)
      return () => clearTimeout(t)
    }
  }, [open])

  const handleClose = useCallback(() => {
    setExiting(true)
    setTimeout(() => { setVisible(false); setExiting(false); onClose?.() }, 220)
  }, [onClose])

  if (!visible) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-6 anim-overlay"
      style={{
        backgroundColor: 'rgba(0,0,0,0.60)',
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
        opacity: exiting ? 0 : undefined,
        transition: 'opacity 0.2s ease',
      }}
      onClick={handleClose}
    >
      <div
        className="rounded-2xl p-6 max-w-sm w-full"
        style={{
          backgroundColor: 'var(--surface-secondary)',
          border: '1px solid var(--border)',
          boxShadow: '0 24px 64px rgba(0,0,0,0.3)',
          animation: exiting
            ? 'animPanelOut 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards'
            : 'animPanelIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold" style={{ color: 'var(--text-primary)' }}>
            {title}
          </h3>
          <button
            onClick={handleClose}
            className="p-1.5 rounded-full transition-all hover:bg-[var(--surface-tertiary)]"
            style={{ color: 'var(--text-tertiary)' }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="mb-6">
          {message && (
            <p className="text-sm leading-relaxed whitespace-pre-line" style={{ color: 'var(--text-secondary)' }}>
              {message}
            </p>
          )}
          {children}
        </div>

        {/* Footer */}
        <div className="flex gap-3 justify-end">
          {cancelLabel && (
            <button
              onClick={handleClose}
              className="px-5 py-2.5 rounded-full text-sm font-semibold transition-all duration-200 hover:bg-[var(--surface-tertiary)] active:scale-95"
              style={{ color: 'var(--text-secondary)', backgroundColor: 'transparent', border: '1px solid var(--border)' }}
            >
              {cancelLabel}
            </button>
          )}
          {onConfirm && (
            <button
              onClick={() => { onConfirm(); handleClose() }}
              className="px-5 py-2.5 rounded-full text-sm font-semibold transition-all duration-200 hover:-translate-y-0.5 active:scale-95"
              style={{
                backgroundColor: danger ? 'var(--danger)' : 'var(--accent)',
                color: '#fff',
                border: 'none',
                boxShadow: danger
                  ? '0 2px 12px rgba(255,59,48,0.35)'
                  : '0 2px 12px rgba(0,113,227,0.35)',
              }}
            >
              {confirmLabel}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

/** Simple alert-style modal (no cancel, just confirm) */
export function AlertModal({ open, onClose, title, message }) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      message={message}
      confirmLabel="确定"
      cancelLabel=""
      onConfirm={onClose}
    />
  )
}
