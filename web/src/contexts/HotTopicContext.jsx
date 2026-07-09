import { createContext, useContext, useState, useCallback } from 'react'

/**
 * HotTopicContext — 跨页面传递"当前激活的热点"。
 *
 * 用法：
 * - 在 HotSearchPage 热点卡点"去生成口播文案"时，setActiveHotTopic(hotTopic) + 触发 tab 切换
 * - 在 CopywritingPage / ShootScriptPage 启动时读 activeHotTopic，自动填 topic，并把 hot_topic_id 提交给后端
 * - 在 ContentLibraryPage 显示内容关联的 hot_topic（来自数据库的 hot_topic_id/title/source）
 */
const HotTopicContext = createContext()

export function HotTopicProvider({ children }) {
  const [activeHotTopic, setActiveHotTopicState] = useState(null)

  const setActiveHotTopic = useCallback((ht) => {
    setActiveHotTopicState(ht)
  }, [])

  const clearActiveHotTopic = useCallback(() => {
    setActiveHotTopicState(null)
  }, [])

  return (
    <HotTopicContext.Provider
      value={{ activeHotTopic, setActiveHotTopic, clearActiveHotTopic }}
    >
      {children}
    </HotTopicContext.Provider>
  )
}

export function useHotTopic() {
  return useContext(HotTopicContext)
}

export default HotTopicContext
