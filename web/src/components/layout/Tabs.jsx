/**
 * 标签页导航组件
 *
 * 显示所有功能标签页，支持切换
 */
import { motion } from 'framer-motion'

export default function Tabs({ tabs, activeTab, onTabChange }) {
  return (
    <nav className="tabs">
      <div className="tabs-list">
        {tabs.map((tab) => (
          <motion.button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.95 }}
          >
            {tab.icon} {tab.name}
          </motion.button>
        ))}
      </div>
    </nav>
  )
}
