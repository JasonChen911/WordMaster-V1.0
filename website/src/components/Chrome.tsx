import { useState, useEffect, type ReactNode } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { motion, useScroll, useSpring, AnimatePresence, useReducedMotion } from 'motion/react'
import { ArrowRight, Download, Menu, Moon, Sun, X } from 'lucide-react'

const nav = [
  { label: '首页', to: '/' },
  { label: '功能', to: '/#features' },
  { label: '下载', to: '/download/' },
  { label: '更新日志', to: '/changelog/' },
]

export default function Chrome({ children }: { children: ReactNode }) {
  const [dark, setDark] = useState(document.documentElement.dataset.theme === 'dark')
  const [menuOpen, setMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const location = useLocation()
  const reduceMotion = useReducedMotion()
  const { scrollYProgress } = useScroll()
  const progress = useSpring(scrollYProgress, { stiffness: 120, damping: 28 })

  useEffect(() => setMenuOpen(false), [location.pathname, location.hash])
  useEffect(() => {
    const update = () => setScrolled(window.scrollY > 18)
    update()
    window.addEventListener('scroll', update, { passive: true })
    return () => window.removeEventListener('scroll', update)
  }, [])
  const toggleTheme = () => {
    const next = !dark
    setDark(next)
    document.documentElement.dataset.theme = next ? 'dark' : 'light'
    localStorage.setItem('wordmaster-site-theme', next ? 'dark' : 'light')
  }

  return <>
    <a className="skip-link" href="#main-content">跳到主要内容</a>
    <motion.div className="scroll-progress" style={{ scaleX: progress }} aria-hidden="true" />
    <header className={`site-header ${scrolled ? 'is-scrolled' : ''}`}>
      <div className="nav-shell">
        <Link to="/" className="brand" aria-label="WordMaster 首页" onClick={() => window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' })}>
          <img src="/images/wordmaster-logo.webp" alt="" width="32" height="32" />
          <span>WordMaster</span>
        </Link>
        <nav className="desktop-nav" aria-label="主导航">
          {nav.map(item => <NavLink key={item.label} to={item.to} end={item.to === '/'} onClick={item.to === '/' ? () => window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' }) : undefined}
            className={({ isActive }) => isActive && !item.to.includes('#') ? 'nav-active' : ''}>{item.label}</NavLink>)}
          <a href="https://github.com/JasonChen911/WordMaster-V1.0" target="_blank" rel="noopener noreferrer">GitHub</a>
        </nav>
        <div className="nav-actions">
          <button className="theme-toggle" onClick={toggleTheme} aria-label={dark ? '切换浅色模式' : '切换深色模式'} title={dark ? '浅色模式' : '深色模式'}>
            {dark ? <Sun size={17} /> : <Moon size={17} />}
          </button>
          <Link className="nav-download" to="/download/"><Download size={15} /> 下载软件</Link>
          <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)} aria-expanded={menuOpen} aria-label="打开导航菜单">
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>
      <AnimatePresence>
        {menuOpen && <motion.nav className="mobile-nav" aria-label="移动端导航"
          initial={reduceMotion ? false : { opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.22 }}>
          {nav.map(item => <Link key={item.label} to={item.to} onClick={item.to === '/' ? () => window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' }) : undefined}>{item.label}<ArrowRight size={16} /></Link>)}
          <a href="https://github.com/JasonChen911/WordMaster-V1.0" target="_blank" rel="noopener noreferrer">GitHub 源码 <ArrowRight size={16} /></a>
        </motion.nav>}
      </AnimatePresence>
    </header>
    <div id="main-content">{children}</div>
    <footer className="site-footer">
      <div className="container footer-grid">
        <div className="footer-brand">
          <Link to="/" className="brand"><img src="/images/wordmaster-logo.webp" alt="" width="30" height="30" /><span>WordMaster</span></Link>
          <p>让每一次记忆，都更有价值。</p>
          <small>© 2026 JasonChen · v0.1.0 Beta</small>
        </div>
        <div><strong>探索</strong><Link to="/#features">功能</Link><Link to="/#intelligence">AI Tutor</Link><Link to="/#memory">记忆引擎</Link></div>
        <div><strong>获取</strong><Link to="/download/">Windows 下载</Link><Link to="/changelog/">更新日志</Link><a href="/license/">当前使用协议</a></div>
        <div><strong>项目</strong><Link to="/#about">关于</Link><Link to="/#source">源码状态</Link><a href="https://github.com/JasonChen911/WordMaster-V1.0" target="_blank" rel="noopener noreferrer">GitHub 源码</a></div>
      </div>
    </footer>
  </>
}
