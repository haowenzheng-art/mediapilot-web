import { createContext, useContext, useState, useEffect } from 'react'

// 创建上下文
const AppContext = createContext()

// 历史记录类型
const HISTORY_TYPES = {
  HOT_SEARCH: 'hot_search',
  COMPETITORS: 'competitors',
  SCRIPT: 'script',
  TEMPLATE: 'template'
}

export function AppProvider({ children }) {
  // 历史记录
  const [history, setHistory] = useState(() => {
    const saved = localStorage.getItem('mediapilot-history')
    return saved ? JSON.parse(saved) : []
  })

  // 日历备注
  const [calendarNotes, setCalendarNotes] = useState(() => {
    const saved = localStorage.getItem('mediapilot-calendar-notes')
    return saved ? JSON.parse(saved) : {}
  })

  // 当前选中的内容（用于模块间传递）
  const [selectedContent, setSelectedContent] = useState(null)

  // 保存历史记录到 localStorage
  useEffect(() => {
    localStorage.setItem('mediapilot-history', JSON.stringify(history))
  }, [history])

  // 保存日历备注到 localStorage
  useEffect(() => {
    localStorage.setItem('mediapilot-calendar-notes', JSON.stringify(calendarNotes))
  }, [calendarNotes])

  // 添加历史记录
  const addHistory = (type, data) => {
    const item = {
      id: Date.now(),
      type,
      data,
      timestamp: new Date().toISOString()
    }
    setHistory(prev => [item, ...prev])
  }

  // 删除历史记录
  const deleteHistory = (id) => {
    setHistory(prev => prev.filter(item => item.id !== id))
  }

  // 清空历史记录
  const clearHistory = () => {
    setHistory([])
  }

  // 获取某类型的历史记录
  const getHistoryByType = (type) => {
    return history.filter(item => item.type === type)
  }

  // 保存日历备注
  const saveCalendarNote = (dateKey, note) => {
    setCalendarNotes(prev => ({
      ...prev,
      [dateKey]: note
    }))
  }

  // 获取日历备注
  const getCalendarNote = (dateKey) => {
    return calendarNotes[dateKey] || ''
  }

  return (
    <AppContext.Provider value={{
      history,
      addHistory,
      deleteHistory,
      clearHistory,
      getHistoryByType,
      calendarNotes,
      saveCalendarNote,
      getCalendarNote,
      selectedContent,
      setSelectedContent
    }}>
      {children}
    </AppContext.Provider>
  )
}

// Hook 用于在组件中使用上下文
export function useApp() {
  return useContext(AppContext)
}

export { HISTORY_TYPES }
