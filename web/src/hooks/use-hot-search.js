import { useState, useCallback } from 'react'
import { useRequest } from './use-request'
import { trendingService } from '../services/trending'
import { getCurrentUser } from '../services/auth'
import { useApp, HISTORY_TYPES } from '../contexts/AppContext'

const PLATFORMS_LIST = [
  { id: 'baidu', name: '百度新闻', icon: '📰' },
  { id: 'weibo', name: '微博热搜', icon: '📱' },
  { id: 'zhihu', name: '知乎热榜', icon: '🧠' },
  { id: 'douyin', name: '抖音热榜', icon: '🎵' },
  { id: 'xiaohongshu', name: '小红书', icon: '📖' },
]

export function useHotSearch() {
  const [keyword, setKeyword] = useState('')
  const [platforms, setPlatforms] = useState(['baidu', 'weibo', 'zhihu', 'douyin', 'xiaohongshu'])
  const [days, setDays] = useState(7)
  const { data, loading, error, run } = useRequest(trendingService.search)
  const { addHistory } = useApp()
  const currentUser = getCurrentUser()

  const search = useCallback(() => {
    if (!keyword.trim()) return
    if (platforms.length === 0) return
    run(keyword, { platforms, days }).then(result => {
      addHistory(HISTORY_TYPES.HOT_SEARCH, { keyword, platforms, days, result })
    }).catch(() => {})
  }, [keyword, platforms, days, run, addHistory])

  const togglePlatform = useCallback((id) => {
    setPlatforms(prev => prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id])
  }, [])

  const exportData = useCallback(async (format) => {
    if (!keyword.trim()) return
    try {
      await trendingService.export(keyword, format)
    } catch (err) {
      alert(`导出失败: ${err.message}`)
    }
  }, [keyword])

  return {
    keyword, setKeyword,
    platforms, togglePlatform,
    days, setDays,
    result: data, loading, error,
    search, exportData,
    currentUser, platformsList: PLATFORMS_LIST,
  }
}
