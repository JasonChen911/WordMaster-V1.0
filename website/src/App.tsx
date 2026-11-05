import { useEffect } from 'react'
import { useLocation, Routes, Route } from 'react-router-dom'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import Chrome from './components/Chrome'
import Home from './pages/Home'
import DownloadPage from './pages/DownloadPage'
import ChangelogPage from './pages/ChangelogPage'

export default function App() {
  const location = useLocation()
  const reduceMotion = useReducedMotion()
  useEffect(() => {
    const pages: Record<string, { title: string; description: string }> = {
      '/': { title: 'WordMaster — 让每一次记忆，都更有价值', description: 'WordMaster：融合 AI 学习辅导与 FSRS 间隔重复的 Windows 英语学习软件。让每一次记忆，都更有价值。' },
      '/download/': { title: '下载 WordMaster — Windows 安装包', description: '下载 WordMaster v0.1.0 Beta Windows 安装包，查看安装说明、系统要求和版本信息。' },
      '/changelog/': { title: '更新日志 — WordMaster', description: '查看 WordMaster v0.1.0 Beta 的已实现功能与更新记录。' },
    }
    const page = pages[location.pathname] ?? pages['/']
    document.title = page.title
    document.querySelector('meta[name="description"]')?.setAttribute('content', page.description)
    document.querySelector('meta[property="og:title"]')?.setAttribute('content', page.title)
    document.querySelector('meta[property="og:description"]')?.setAttribute('content', page.description)
  }, [location.pathname])
  useEffect(() => {
    if (location.hash) {
      requestAnimationFrame(() => document.getElementById(location.hash.slice(1))?.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth' }))
    } else {
      window.scrollTo({ top: 0, behavior: 'auto' })
    }
  }, [location.pathname, location.hash, reduceMotion])

  return <Chrome>
    <AnimatePresence mode="wait" initial={false}>
      <motion.main key={location.pathname}
        initial={reduceMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={reduceMotion ? undefined : { opacity: 0, y: -8 }}
        transition={{ duration: 0.28, ease: [0.22, 0.61, 0.36, 1] }}>
        <Routes location={location}>
          <Route path="/" element={<Home />} />
          <Route path="/download/" element={<DownloadPage />} />
          <Route path="/changelog/" element={<ChangelogPage />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </motion.main>
    </AnimatePresence>
  </Chrome>
}
