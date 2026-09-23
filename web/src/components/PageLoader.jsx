/**
 * PageLoader — Suspense fallback shown while a lazy-loaded page chunk downloads.
 *
 * Designed as a lightweight shimmer that matches WordMaster's iOS design language.
 * No heavy animation — a single pulsing bar is enough to signal "loading" without
 * flashing or jank on fast connections.
 */
export default function PageLoader() {
  return (
    <div
      className="min-h-[60vh] flex flex-col items-center justify-center gap-4"
      style={{ backgroundColor: 'var(--surface)' }}
    >
      {/* Subtle spinner */}
      <div
        className="w-8 h-8 rounded-full border-[3px] animate-spin"
        style={{
          borderColor: 'var(--border)',
          borderTopColor: 'var(--accent)',
        }}
      />

      {/* Label */}
      <span
        className="text-sm font-medium"
        style={{ color: 'var(--text-tertiary)' }}
      >
        加载中...
      </span>
    </div>
  )
}
