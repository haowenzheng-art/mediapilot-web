/**
 * 话题历史 Hook
 */
import { useState, useCallback } from 'react'
import { topicHistoryService } from '../services/topic-history'

const TIME_RANGES = [
  { id: '7', name: '最近7天' },
  { id: '30', name: '最近30天' },
  { id: '90', name: '最近90天' },
  { id: '365', name: '最近1年' }
]

export function useTopicHistory() {
  const [topics, setTopics] = useState([])
  const [selectedTopic, setSelectedTopic] = useState(null)
  const [trendData, setTrendData] = useState([])
  const [topicContents, setTopicContents] = useState([])
  const [topicHotspots, setTopicHotspots] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // 获取话题列表
  const fetchTopics = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const data = await topicHistoryService.getTopics()
      if (data.success) {
        setTopics(data.data.topics || [])
      } else {
        setError(data.message || '获取话题列表失败')
      }
    } catch (err) {
      setError('获取话题列表失败，请稍后重试')
      console.error('获取话题列表失败:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // 获取话题详情
  const fetchTopicDetail = useCallback(async (topicId) => {
    setLoading(true)
    setError(null)

    try {
      const data = await topicHistoryService.getTopicDetail(topicId)
      if (data.success) {
        setSelectedTopic(data.data)
        return data.data
      } else {
        setError(data.message || '获取话题详情失败')
        return null
      }
    } catch (err) {
      setError('获取话题详情失败，请稍后重试')
      console.error('获取话题详情失败:', err)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  // 获取话题趋势
  const fetchTopicTrend = useCallback(async (topicId, startDate, endDate) => {
    setLoading(true)
    setError(null)

    try {
      const data = await topicHistoryService.getTopicTrend(topicId, startDate, endDate)
      if (data.success) {
        setTrendData(data.data.trend || [])
        return data.data.trend || []
      } else {
        setError(data.message || '获取趋势数据失败')
        return []
      }
    } catch (err) {
      setError('获取趋势数据失败，请稍后重试')
      console.error('获取趋势数据失败:', err)
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  // 获取话题关联内容
  const fetchTopicContents = useCallback(async (topicId, page = 1, pageSize = 20) => {
    setLoading(true)
    setError(null)

    try {
      const data = await topicHistoryService.getTopicContents(topicId, page, pageSize)
      if (data.success) {
        setTopicContents(data.data.contents || [])
        return data.data
      } else {
        setError(data.message || '获取关联内容失败')
        return null
      }
    } catch (err) {
      setError('获取关联内容失败，请稍后重试')
      console.error('获取关联内容失败:', err)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  // 获取话题关联热点
  const fetchTopicHotspots = useCallback(async (topicId) => {
    setLoading(true)
    setError(null)

    try {
      const data = await topicHistoryService.getTopicHotspots(topicId)
      if (data.success) {
        setTopicHotspots(data.data.hotspots || [])
        return data.data.hotspots || []
      } else {
        setError(data.message || '获取关联热点失败')
        return []
      }
    } catch (err) {
      setError('获取关联热点失败，请稍后重试')
      console.error('获取关联热点失败:', err)
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  // 创建话题
  const createTopic = useCallback(async (data) => {
    setLoading(true)
    setError(null)

    try {
      const response = await topicHistoryService.createTopic(data)
      if (response.success) {
        await fetchTopics()
        return true
      } else {
        setError(response.message || '创建话题失败')
        return false
      }
    } catch (err) {
      setError('创建话题失败，请稍后重试')
      console.error('创建话题失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [fetchTopics])

  // 更新话题
  const updateTopic = useCallback(async (topicId, data) => {
    setLoading(true)
    setError(null)

    try {
      const response = await topicHistoryService.updateTopic(topicId, data)
      if (response.success) {
        await fetchTopics()
        return true
      } else {
        setError(response.message || '更新话题失败')
        return false
      }
    } catch (err) {
      setError('更新话题失败，请稍后重试')
      console.error('更新话题失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [fetchTopics])

  // 删除话题
  const deleteTopic = useCallback(async (topicId) => {
    setLoading(true)
    setError(null)

    try {
      const response = await topicHistoryService.deleteTopic(topicId)
      if (response.success) {
        await fetchTopics()
        setSelectedTopic(null)
        return true
      } else {
        setError(response.message || '删除话题失败')
        return false
      }
    } catch (err) {
      setError('删除话题失败，请稍后重试')
      console.error('删除话题失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [fetchTopics])

  // 选择话题并加载相关数据
  const selectTopic = useCallback(async (topicId, timeRange = '7') => {
    const days = parseInt(timeRange)
    const endDate = new Date().toISOString().split('T')[0]
    const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

    await fetchTopicDetail(topicId)
    await fetchTopicTrend(topicId, startDate, endDate)
    await fetchTopicContents(topicId)
    await fetchTopicHotspots(topicId)
  }, [fetchTopicDetail, fetchTopicTrend, fetchTopicContents, fetchTopicHotspots])

  return {
    topics, setTopics,
    selectedTopic, setSelectedTopic,
    trendData, setTrendData,
    topicContents, setTopicContents,
    topicHotspots, setTopicHotspots,
    loading, error, setError,
    fetchTopics,
    fetchTopicDetail,
    fetchTopicTrend,
    fetchTopicContents,
    fetchTopicHotspots,
    createTopic,
    updateTopic,
    deleteTopic,
    selectTopic,
    timeRanges: TIME_RANGES
  }
}