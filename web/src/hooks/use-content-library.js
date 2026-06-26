/**
 * 内容库 Hook
 */
import { useState, useCallback, useEffect } from 'react'
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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchContents = useCallback(async (filters = {}, page = 1, pageSize = 20) => {
    setLoading(true)
    setError(null)
    try {
      const data = await contentLibraryService.getContents(filters, page, pageSize)
      if (data.success) {
        setContents(data.data.contents || [])
        setTotal(data.data.count ?? data.data.total ?? 0)
      } else {
        setError(data.message || '获取内容列表失败')
      }
    } catch (err) {
      setError(err.message || '获取内容列表失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchContentDetail = useCallback(async (contentId) => {
    setLoading(true)
    setError(null)
    try {
      const data = await contentLibraryService.getContentDetail(contentId)
      if (data.success) return data.data
      setError(data.message || '获取内容详情失败')
      return null
    } catch (err) {
      setError(err.message || '获取内容详情失败，请稍后重试')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const deleteContent = useCallback(async (contentId) => {
    setLoading(true)
    setError(null)
    try {
      const data = await contentLibraryService.deleteContent(contentId)
      if (data.success) {
        setContents(prev => prev.filter(c => c.id !== contentId))
        setTotal(prev => Math.max(0, prev - 1))
        return true
      }
      setError(data.message || '删除内容失败')
      return false
    } catch (err) {
      setError(err.message || '删除内容失败，请稍后重试')
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  // 按类型聚合统计——后端没提供 /stats 端点，用列表数据本地算
  const computeStats = useCallback((list) => {
    const stats = { total: list.length, scripts: 0, copywritings: 0, videos: 0, audios: 0 }
    for (const c of list) {
      if (c.content_type === 'script') stats.scripts++
      else if (c.content_type === 'copywriting') stats.copywritings++
      else if (c.content_type === 'video') stats.videos++
      else if (c.content_type === 'audio') stats.audios++
    }
    return stats
  }, [])

  return {
    contents, setContents,
    total, setTotal,
    stats: computeStats(contents),
    loading, error, setError,
    fetchContents,
    fetchContentDetail,
    deleteContent,
    computeStats,
    contentTypes: CONTENT_TYPES
  }
}
