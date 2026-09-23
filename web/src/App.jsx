import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import PageLoader from './components/PageLoader'
import ErrorBoundary from './components/ErrorBoundary'
import ThemeBackground from './theme/ThemeBackground'

// ── Page-level lazy imports ──────────────────────────────────
const Dashboard  = lazy(() => import('./pages/Dashboard'))
const Study      = lazy(() => import('./pages/Study'))
const Analytics  = lazy(() => import('./pages/Analytics'))
const Search     = lazy(() => import('./pages/Search'))
const Favorites  = lazy(() => import('./pages/Favorites'))
const Dictionary = lazy(() => import('./pages/Dictionary'))
const Settings   = lazy(() => import('./pages/Settings'))
const AISettings = lazy(() => import('./pages/AISettings'))
const AITutor    = lazy(() => import('./pages/AITutor'))
const Reading    = lazy(() => import('./pages/Reading'))
const Agreement  = lazy(() => import('./pages/Agreement'))
const About      = lazy(() => import('./pages/About'))
const Games      = lazy(() => import('./pages/Games'))
const MaterialImport = lazy(() => import('./pages/MaterialImport'))
const Teacher = lazy(() => import('./pages/Teacher'))
const MistakeBook = lazy(() => import('./pages/MistakeBook'))

export default function App() {
  return (
    <div className="min-h-screen" style={{
      backgroundColor: 'var(--background, var(--surface))',
      transition: 'var(--theme-transition)',
    }}>
      <ThemeBackground />
      <Navbar />
      <main style={{ position: 'relative', zIndex: 1 }}>
        <ErrorBoundary>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/study" element={<Study />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/search" element={<Search />} />
            <Route path="/favorites" element={<Favorites />} />
            <Route path="/dictionary" element={<Dictionary />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/settings/ai" element={<AISettings />} />
            <Route path="/ai-tutor" element={<AITutor />} />
            <Route path="/reading" element={<Reading />} />
            <Route path="/agreement" element={<Agreement />} />
            <Route path="/about" element={<About />} />
            <Route path="/games" element={<Games />} />
            <Route path="/material" element={<MaterialImport />} />
            <Route path="/teacher" element={<Teacher />} />
            <Route path="/mistakes" element={<MistakeBook />} />
          </Routes>
        </Suspense>
        </ErrorBoundary>
      </main>
    </div>
  )
}
