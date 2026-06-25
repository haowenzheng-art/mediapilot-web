/**
 * 内容页组件
 *
 * 包含 Header、Tabs 标签导航和页面内容切换
 */
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect } from 'react'
import Header from './Header'
import Tabs from './Tabs'
import Footer from '../Footer'

import HotSearchPage from '../../pages/insight/HotSearchPage'
import CopywritingPage from '../../pages/content/CopywritingPage'
import ShootScriptPage from '../../pages/content/ShootScriptPage'
import SubscriptionPage from '../../pages/content/SubscriptionPage'
import ContentLibraryPage from '../../pages/content/ContentLibraryPage'
import TopicHistoryPage from '../../pages/content/TopicHistoryPage'
import TranscriptionPage from '../../pages/content/TranscriptionPage'
import VideoAnalysisPage from '../../pages/content/VideoAnalysisPage'
import TemplatesPage from '../../pages/content/TemplatesPage'

export default function ContentPage({ tabs, activeTab, onTabChange, currentUser, onLoginClick, onLogout, onLogoClick }) {
  // 监听自定义标签页切换事件
  useEffect(() => {
    const handleTabChange = (e) => {
      onTabChange(e.detail)
    }
    window.addEventListener('tab-change', handleTabChange)
    return () => window.removeEventListener('tab-change', handleTabChange)
  }, [onTabChange])
  const renderContent = () => {
    switch (activeTab) {
      case 'trending':
        return <HotSearchPage />
      case 'copywriting':
        return <CopywritingPage />
      case 'shoot-script':
        return <ShootScriptPage />
      case 'subscription':
        return <SubscriptionPage />
      case 'content-library':
        return <ContentLibraryPage />
      case 'topic-history':
        return <TopicHistoryPage />
      case 'transcription':
        return <TranscriptionPage />
      case 'video-analysis':
        return <VideoAnalysisPage />
      case 'templates':
        return <TemplatesPage />
      default:
        return (
          <div style={{
            maxWidth: '800px',
            margin: '0 auto',
            padding: '48px 24px',
          }}>
            <div className="card">
              <h2 style={{
                fontSize: '18px',
                fontWeight: '600',
                marginBottom: '16px',
              }}>
                功能开发中
              </h2>
              <p style={{
                fontSize: '14px',
                color: 'var(--text-secondary)',
              }}>
                该功能正在开发中，敬请期待！
              </p>
            </div>
          </div>
        )
    }
  }

  return (
    <div className="content-page" style={{
      background: 'var(--page-gradient)',
      minHeight: '100vh',
    }}>
      <Header currentUser={currentUser} onLoginClick={onLoginClick} onLogout={onLogout} onLogoClick={onLogoClick} />

      <Tabs tabs={tabs} activeTab={activeTab} onTabChange={onTabChange} />

      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          className="page-content"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
          style={{ padding: '120px 24px' }}
        >
          {renderContent()}
        </motion.div>
      </AnimatePresence>

      <Footer />
    </div>
  )
}
