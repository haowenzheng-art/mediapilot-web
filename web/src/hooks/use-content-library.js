/**
 * 内容库 Hook
 */
import { useState, useCallback } from 'react'
import { contentLibraryService } from '../services/content-library'

const CONTENT_TYPES = [
  { id: '', name: '全部类型' },
  { id: 'script', name: '拍摄脚本' },
  { id: 'copywriting', name: '口播文案' },
  { id: 'video', name: '视频' },
  { id: 'audio', name: '音频' }
]

export function useContentLibrary() {
  const [contents, setContents] = useState([])
  const [total, setTotal] = useState(0)
  const [stats, setStats] = useState({
    total: 0,
    scripts: 0,
    copywritings: 0,
    videos: 0,
    audios: 0
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // 获取内容列表
  const fetchContents = useCallback(async (filters = {}, page = 1, pageSize = 20) => {
    setLoading(true)
    setError(null)

    try {
      const data = await contentLibraryService.getContents(filters, page, pageSize)
      if (data.success) {
        setContents(data.data.contents || [])
        setTotal(data.data.total || 0)
      } else {
        setError(data.message || '获取内容列表失败')
      }
    } catch (err) {
      setError('获取内容列表失败，请稍后重试')
      console.error('获取内容列表失败:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // 获取内容详情
  const fetchContentDetail = useCallback(async (contentId) => {
    setLoading(true)
    setError(null)

    try {
      const data = await contentLibraryService.getContentDetail(contentId)
      if (data.success) {
        return data.data
      } else {
        setError(data.message || '获取内容详情失败')
        return null
      }
    } catch (err) {
      setError('获取内容详情失败，请稍后重试')
      console.error('获取内容详情失败:', err)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  // 获取关联内容
  const fetchRelatedContents = useCallback(async (contentId) => {
    setLoading(true)
    setError(null)

    try {
      const data = await contentLibraryService.getRelatedContents(contentId)
      if (data.success) {
        return data.data.contents || []
      } else {
        setError(data.message || '获取关联内容失败')
        return []
      }
    } catch (err) {
      setError('获取关联内容失败，请稍后重试')
      console.error('获取关联内容失败:', err)
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  // 更新标签
  const updateTags = useCallback(async (contentId, tags) => {
    setLoading(true)
    setError(null)

    try {
      const data = await contentLibraryService.updateTags(contentId, tags)
      if (data.success) {
        // 更新本地状态
        setContents(prev => prev.map(c =>
          c.id === contentId ? { ...c, tags } : c
        ))
        return true
      } else {
        setError(data.message || '更新标签失败')
        return false
      }
    } catch (err) {
      setError('更新标签失败，请稍后重试')
      console.error('更新标签失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  // 关联话题
  const linkTopic = useCallback(async (contentId, topicId) => {
    setLoading(true)
    setError(null)

    try {
      const data = await contentLibraryService.linkTopic(contentId, topicId)
      if (data.success) {
        // 更新本地状态
        setContents(prev => prev.map(c =>
          c.id === contentId ? { ...c, topics: [...(c.topics || []), { id: topicId }] } : c
        ))
        return true
      } else {
        setError(data.message || '关联话题失败')
        return false
      }
    } catch (err) {
      setError('关联话题失败，请稍后重试')
      console.error('关联话题失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  // 取消关联话题
  const unlinkTopic = useCallback(async (contentId, topicId) => {
    setLoading(true)
    setError(null)

    try {
      const data = await contentLibraryService.unlinkTopic(contentId, topicId)
      if (data.success) {
        // 更新本地状态
        setContents(prev => prev.map(c =>
          c.id === contentId
            ? { ...c, topics: (c.topics || []).filter(t => t.id !== topicId) }
            : c
        ))
        return true
      } else {
        setError(data.message || '取消关联失败')
        return false
      }
    } catch (err) {
      setError('取消关联失败，请稍后重试')
      console.error('取消关联失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  // 删除内容
  const deleteContent = useCallback(async (contentId) => {
    setLoading(true)
    setError(null)

    try {
      const data = await contentLibraryService.deleteContent(contentId)
      if (data.success) {
        // 更新本地状态
        setContents(prev => prev.filter(c => c.id !== contentId))
        setTotal(prev => Math.max(0, prev - 1))
        return true
      } else {
        setError(data.message || '删除内容失败')
        return false
      }
    } catch (err) {
      setError('删除内容失败，请稍后重试')
      console.error('删除内容失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  // 获取统计信息
  const fetchStats = useCallback(async () => {
    try {
      const data = await contentLibraryService.getStats()
      if (data.success) {
        setStats(data.data || {})
      }
    } catch (err) {
      console.error('获取统计信息失败:', err)
    }
  }, [])

  return {
    contents, setContents,
    total, setTotal,
    stats, setStats,
    loading, error, setError,
    fetchContents,
    fetchContentDetail,
    fetchRelatedContents,
    updateTags,
    linkTopic,
    unlinkTopic,
    deleteContent,
    fetchStats,
    contentTypes: CONTENT_TYPES
  }
}