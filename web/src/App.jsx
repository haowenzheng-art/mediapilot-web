/**
 * MediaPilot 主应用组件
 *
 * 职责：
 * - 管理全局状态（登录、主题、页面切换）
 * - 处理滚动动画和页面导航
 * - 整合 Hero 页面和内容页面
 */
import { useState } from 'react'
import { AnimatePresence } from 'framer-motion'

import HeroSection from './pages/HeroSection'
import ContentPage from './components/layout/ContentPage'
import LoginPage from './pages/LoginPage'
import AIChat from './components/ai/AIChat'

import TABS, { ROUTE_PATHS } from './routes'
import { getCurrentUser, logout } from './services/auth'

const DEFAULT_TAB = ROUTE_PATHS.SHOOT_SCRIPT

function App() {
  const [activeTab, setActiveTab] = useState(DEFAULT_TAB)
  const [isHeroPage, setIsHeroPage] = useState(true)
  const [currentUser, setCurrentUser] = useState(() => getCurrentUser())
  const [showLoginModal, setShowLoginModal] = useState(false)

  const handleFeatureClick = (tabId) => {
    setActiveTab(tabId)
    setIsHeroPage(false)
  }

  const scrollToHero = () => {
    setIsHeroPage(true)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleLogin = (user) => {
    setCurrentUser(user)
    if (user.isAdmin) {
      import('./services/api').then(({ setAIEnabled }) => {
        setAIEnabled(true)
      })
    }
  }

  const handleLogout = () => {
    logout()
    setCurrentUser(null)
    import('./services/api').then(({ setAIEnabled }) => {
      setAIEnabled(false)
    })
  }

  return (
    <div className="app">
      <AnimatePresence mode="wait">
        {isHeroPage ? (
          <HeroSection
            key="hero"
            currentUser={currentUser}
            onLoginClick={() => setShowLoginModal(true)}
            onFeatureClick={handleFeatureClick}
          />
        ) : (
          <ContentPage
            key="content"
            tabs={TABS}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            currentUser={currentUser}
            onLoginClick={() => setShowLoginModal(true)}
            onLogout={handleLogout}
            onLogoClick={scrollToHero}
          />
        )}
      </AnimatePresence>

      {/* 登录弹窗 */}
      <AnimatePresence>
        {showLoginModal && (
          <div
            className="modal-overlay"
            onClick={() => setShowLoginModal(false)}
            style={{
              background: 'rgba(0, 0, 0, 0.3)',
              backdropFilter: 'blur(20px) saturate(180%)',
              WebkitBackdropFilter: 'blur(20px) saturate(180%)',
            }}
          >
            <div
              className="modal-content"
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'var(--bg-primary)',
                border: 'none',
                borderRadius: '16px',
                boxShadow: 'rgba(0,0,0,0.12) 0px 8px 24px 0px',
              }}
            >
              <div
                className="modal-header"
                style={{
                  borderBottom: '1px solid rgba(0,0,0,0.06)',
                }}
              >
                <h2 className="modal-title">登录</h2>
                <button
                  className="modal-close"
                  onClick={() => setShowLoginModal(false)}
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-tertiary)',
                    fontSize: '16px',
                    cursor: 'pointer',
                    transition: 'opacity 0.2s ease',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.opacity = '0.6'}
                  onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
                >
                  ✕
                </button>
              </div>
              <div className="modal-body">
                <LoginPage
                  onLogin={(user) => {
                    handleLogin(user)
                    setShowLoginModal(false)
                  }}
                  onClose={() => setShowLoginModal(false)}
                />
              </div>
            </div>
          </div>
        )}
      </AnimatePresence>

      <AIChat />
    </div>
  )
}

export default App
