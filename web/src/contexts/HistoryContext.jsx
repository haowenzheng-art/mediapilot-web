import { createContext, useContext, useState, useEffect } from 'react'

const HISTORY_TYPES = {
  HOT_SEARCH: 'hot_search',
  COMPETITORS: 'competitors',
  SCRIPT: 'script',
  PLATFORM_DATA: 'platform_data'
}

const HistoryContext = createContext()

export function HistoryProvider({ children }) {
  const [history, setHistory] = useState(() => {
    const saved = localStorage.getItem('mediapilot-history')
    return saved ? JSON.parse(saved) : []
  })

  useEffect(() => {
    localStorage.setItem('mediapilot-history', JSON.stringify(history))
  }, [history])

  const addHistory = (type, data) => {
    const item = { id: Date.now(), type, data, timestamp: new Date().toISOString() }
    setHistory(prev => [item, ...prev])
  }

  const deleteHistory = (id) => {
    setHistory(prev => prev.filter(item => item.id !== id))
  }

  const clearHistory = () => {
    setHistory([])
  }

  const getHistoryByType = (type) => {
    return history.filter(item => item.type === type)
  }

  return (
    <HistoryContext.Provider value={{ history, addHistory, deleteHistory, clearHistory, getHistoryByType }}>
      {children}
    </HistoryContext.Provider>
  )
}

export function useHistory() {
  return useContext(HistoryContext)
}

export { HISTORY_TYPES }
