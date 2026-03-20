import { useState, useRef, useEffect } from 'react'
import './index.css'
import './assets/styles/global.css'
import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from './contexts/ThemeContext'
import DynamicBackground from './components/DynamicBackground'
import ThemeSwitcher from './components/ThemeSwitcher'
import AIChat from './components/AIChat'
import Footer from './components/Footer'
import ScriptPage from './pages/ScriptPage'
import SettingsPage from './pages/SettingsPage'
import HotSearchPage from './pages/HotSearchPage'
import CompetitorsPage from './pages/CompetitorsPage'
import CalendarPage from './pages/CalendarPage'
import TemplatesPage from './pages/TemplatesPage'
import TranscriptionPage from './pages/TranscriptionPage'
import AnalyticsPage from './pages/AnalyticsPage'
import HistoryPage from './pages/HistoryPage'

const TABS = [
  { id: 'trending', name: '热点搜索', icon: '🔥' },
  { id: 'competitors', name: '对标账号', icon: '👥' },
  { id: 'script', name: '脚本生成', icon: '✍️' },
  { id: 'transcription', name: '智能转录', icon: '🎙️' },
  { id: 'calendar', name: '发布日历', icon: '📅' },
  { id: 'analytics', name: '数据分析', icon: '📊' },
  { id: 'templates', name: 'AI模板', icon: '📋' },
  { id: 'history', name: '历史记录', icon: '📜' },
  { id: 'settings', name: '设置', icon: '⚙️' },
]

function App() {
  const { currentThemeId } = useTheme()
  const [activeTab, setActiveTab] = useState('script')
  const [isHeroPage, setIsHeroPage] = useState(true)
  const heroRef = useRef(null)
  const contentRef = useRef(null)
  const isScrolling = useRef(false)
  const lastScrollTop = useRef(0)

  useEffect(() => {
    let wheelTimeout = null

    const handleWheel = (e) => {
      if (isScrolling.current) return

      const scrollDelta = e.deltaY
      const now = Date.now()

      // 简单的节流，防止快速连续触发
      if (wheelTimeout && now - wheelTimeout < 50) return
      wheelTimeout = now

      if (isHeroPage && scrollDelta > 30) {
        // 向下滚动，降低阈值让响应更快
        isScrolling.current = true
        setIsHeroPage(false)
        setTimeout(() => {
          isScrolling.current = false
        }, 600)
      } else if (!isHeroPage && scrollDelta < -30) {
        // 向上滚动，降低阈值
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop
        if (scrollTop <= 50) {
          isScrolling.current = true
          setIsHeroPage(true)
          setTimeout(() => {
            isScrolling.current = false
          }, 600)
        }
      }
    }

    const handleKeyDown = (e) => {
      if (isScrolling.current) return

      if (e.key === 'ArrowDown' || e.key === 'PageDown' || e.key === ' ') {
        if (isHeroPage) {
          e.preventDefault()
          isScrolling.current = true
          setIsHeroPage(false)
          setTimeout(() => {
            isScrolling.current = false
          }, 600)
        }
      } else if (e.key === 'ArrowUp' || e.key === 'PageUp') {
        if (!isHeroPage) {
          const scrollTop = window.pageYOffset || document.documentElement.scrollTop
          if (scrollTop <= 50) {
            e.preventDefault()
            isScrolling.current = true
            setIsHeroPage(true)
            setTimeout(() => {
              isScrolling.current = false
            }, 600)
          }
        }
      }
    }

    window.addEventListener('wheel', handleWheel, { passive: true })
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('wheel', handleWheel)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isHeroPage])

  const handleFeatureClick = (tabId) => {
    setActiveTab(tabId)
    setIsHeroPage(false)
  }

  const scrollToHero = () => {
    setIsHeroPage(true)
  }

  return (
    <div className={`app ${currentThemeId}-theme`} data-theme={currentThemeId}>
      <DynamicBackground />

      <motion.div
        className="app-content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <AnimatePresence mode="wait">
          {isHeroPage ? (
            <motion.section
              key="hero"
              ref={heroRef}
              className="hero-cover"
              initial={{ opacity: 0, y: -30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -30 }}
              transition={{ duration: 0.3, type: 'tween' }}
            >
              <div className="hero-content">
                <div className="hero-logo">
                  <span className="hero-logo-icon">🚀</span>
                  <h1 className="hero-logo-text">MediaPilot</h1>
                  <span className="hero-badge">WEB EDITION</span>
                </div>

                <div className="hero-theme-switcher">
                  <ThemeSwitcher />
                </div>

                <h1 className="hero-title">
                  <span className="hero-title-cn">创新改变世界</span>
                  <span className="hero-title-divider">|</span>
                  <span className="hero-title-en">Innovation Changes the World</span>
                </h1>
                <p className="hero-subtitle">
                  MediaPilot —— 让每个人都能打造个人IP
                </p>

                <div className="feature-cards">
                  {[
                    { icon: '🔥', title: '热点搜索', desc: '捕捉行业热点，智能分析趋势', tab: 'trending' },
                    { icon: '✍️', title: '脚本生成', desc: 'AI一键生成爆款短视频脚本', tab: 'script' },
                    { icon: '📅', title: '发布日历', desc: '规划内容排期，不错过任何热点', tab: 'calendar' },
                    { icon: '🔍', title: '账号分析', desc: '拆解对标账号，学习成功逻辑', tab: 'competitors' },
                  ].map((feature, idx) => (
                    <motion.div
                      key={idx}
                      className="feature-card card"
                      whileHover={{
                        scale: 1.05,
                        rotateX: 5,
                        rotateY: 5,
                        boxShadow: '0 25px 50px rgba(0,0,0,0.25)',
                      }}
                      transition={{ type: 'spring', stiffness: 300 }}
                      onClick={() => handleFeatureClick(feature.tab)}
                    >
                      <span className="feature-icon">{feature.icon}</span>
                      <h3 className="feature-title">{feature.title}</h3>
                      <p className="feature-desc">{feature.desc}</p>
                    </motion.div>
                  ))}
                </div>

                <div className="scroll-hint">
                  <span className="scroll-icon">↓</span>
                  <span className="scroll-text">用力向下滑动进入</span>
                </div>
              </div>
            </motion.section>
          ) : (
            <motion.div
              key="content"
              ref={contentRef}
              className="content-page"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 30 }}
              transition={{ duration: 0.3, type: 'tween' }}
            >
              <header className="header">
                <div className="header-content">
                  <div className="logo" onClick={scrollToHero} style={{ cursor: 'pointer' }}>
                    <span className="logo-icon">🚀</span>
                    <h1 className="logo-text">MediaPilot</h1>
                    <span className="badge">WEB EDITION</span>
                  </div>
                </div>
              </header>

              <nav className="tabs">
                <div className="tabs-list">
                  {TABS.map((tab) => (
                    <motion.button
                      key={tab.id}
                      className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                      onClick={() => setActiveTab(tab.id)}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      {tab.icon} {tab.name}
                    </motion.button>
                  ))}
                </div>
              </nav>

              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  className="tab-content page-enter"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  {(() => {
                    switch (activeTab) {
                      case 'trending':
                        return <HotSearchPage />
                      case 'competitors':
                        return <CompetitorsPage />
                      case 'script':
                        return <ScriptPage />
                      case 'transcription':
                        return <TranscriptionPage />
                      case 'calendar':
                        return <CalendarPage />
                      case 'analytics':
                        return <AnalyticsPage />
                      case 'templates':
                        return <TemplatesPage />
                      case 'history':
                        return <HistoryPage />
                      case 'settings':
                        return <SettingsPage />
                      default:
                        return (
                          <div className="p-6 max-w-4xl mx-auto">
                            <div className="card">
                              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                                <span>🚧</span>
                                功能开发中
                              </h2>
                              <p className="text-secondary">
                                该功能正在开发中，敬请期待！
                              </p>
                            </div>
                          </div>
                        )
                    }
                  })()}
                </motion.div>
              </AnimatePresence>

              <Footer />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <AIChat />
    </div>
  )
}

export default App
