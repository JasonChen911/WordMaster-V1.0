import { NavLink, useLocation } from 'react-router-dom'
import { BarChart3, Search, Home, Settings, Sparkles, FileText, Gamepad2, GraduationCap } from 'lucide-react'

const navItems = [
  { to: '/', icon: Home, label: '首页' },
  { to: '/search', icon: Search, label: '搜索' },
  { to: '/games', icon: Gamepad2, label: '游戏' },
  { to: '/ai-tutor', icon: Sparkles, label: 'AI导师' },
  { to: '/reading', icon: FileText, label: '阅读' },
  { to: '/analytics', icon: BarChart3, label: '分析' },
  { to: '/teacher', icon: GraduationCap, label: '教师Preview' },
  { to: '/settings', icon: Settings, label: '设置' },
]

export default function Navbar() {
  const location = useLocation()

  const linkClass = (to) => {
    const isActive = location.pathname === to
    return `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
      isActive
        ? 'text-[var(--text-primary)]'
        : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-tertiary)]'
    }`
  }

  const mobileLinkClass = (to) => {
    const isActive = location.pathname === to
    return `p-2 rounded-lg transition-all duration-200 ${
      isActive
        ? 'text-[var(--text-primary)]'
        : 'text-[var(--text-tertiary)]'
    }`
  }

  return (
    <nav
      className="sticky top-0 z-50 border-b"
      style={{
        backgroundColor: 'color-mix(in srgb, var(--surface) 92%, transparent)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderColor: 'var(--border)',
      }}
    >
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex items-center justify-between h-14">
          <NavLink to="/" className="flex items-center gap-2.5 group select-none">
            <img
              src="/logo.png"
              alt="WordMaster"
              className="w-8 h-8 rounded-lg object-contain transition-all duration-200 group-hover:scale-105"
              style={{ backgroundColor: 'var(--text-primary)' }}
            />
            <span className="font-bold text-base tracking-tight hidden sm:block"
              style={{ color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>WordMaster</span>
          </NavLink>

          <div className="hidden sm:flex items-center gap-0.5">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink key={to} to={to} className={linkClass(to)}><Icon size={16} />{label}</NavLink>
            ))}
          </div>

          <div className="flex sm:hidden items-center gap-0">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink key={to} to={to} className={mobileLinkClass(to)} aria-label={label}><Icon size={19} /></NavLink>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}
