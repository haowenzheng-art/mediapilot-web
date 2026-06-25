/**
 * 话题订阅 Hook
 */
import { useState, useCallback } from 'react'
import { subscriptionService } from '../services/subscription'

const FREQUENCIES = [
  { id: 'daily', name: '每天', description: '每天推送一次' },
  { id: 'every_3_days', name: '每3天', description: '每3天推送一次' }
]

export function useSubscription() {
  const [subscriptions, setSubscriptions] = useState([])
  const [pushRecords, setPushRecords] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // 获取订阅列表
  const fetchSubscriptions = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const data = await subscriptionService.getSubscriptions()
      if (data.success) {
        setSubscriptions(data.data.subscriptions || [])
      } else {
        setError(data.message || '获取订阅列表失败')
      }
    } catch (err) {
      setError('获取订阅列表失败，请稍后重试')
      console.error('获取订阅列表失败:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // 创建订阅
  const createSubscription = useCallback(async (topic, description, frequency) => {
    if (!topic.trim()) {
      setError('请输入话题')
      return false
    }

    setLoading(true)
    setError(null)

    try {
      const data = await subscriptionService.createSubscription(topic, description, frequency)
      if (data.success) {
        await fetchSubscriptions()
        return true
      } else {
        setError(data.message || '创建订阅失败')
        return false
      }
    } catch (err) {
      setError('创建订阅失败，请稍后重试')
      console.error('创建订阅失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [fetchSubscriptions])

  // 更新订阅
  const updateSubscription = useCallback(async (subscriptionId, updates) => {
    setLoading(true)
    setError(null)

    try {
      const data = await subscriptionService.updateSubscription(subscriptionId, updates)
      if (data.success) {
        await fetchSubscriptions()
        return true
      } else {
        setError(data.message || '更新订阅失败')
        return false
      }
    } catch (err) {
      setError('更新订阅失败，请稍后重试')
      console.error('更新订阅失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [fetchSubscriptions])

  // 删除订阅
  const deleteSubscription = useCallback(async (subscriptionId) => {
    setLoading(true)
    setError(null)

    try {
      const data = await subscriptionService.deleteSubscription(subscriptionId)
      if (data.success) {
        await fetchSubscriptions()
        return true
      } else {
        setError(data.message || '删除订阅失败')
        return false
      }
    } catch (err) {
      setError('删除订阅失败，请稍后重试')
      console.error('删除订阅失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [fetchSubscriptions])

  // 暂停订阅
  const pauseSubscription = useCallback(async (subscriptionId) => {
    setLoading(true)
    setError(null)

    try {
      const data = await subscriptionService.pauseSubscription(subscriptionId)
      if (data.success) {
        await fetchSubscriptions()
        return true
      } else {
        setError(data.message || '暂停订阅失败')
        return false
      }
    } catch (err) {
      setError('暂停订阅失败，请稍后重试')
      console.error('暂停订阅失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [fetchSubscriptions])

  // 恢复订阅
  const resumeSubscription = useCallback(async (subscriptionId) => {
    setLoading(true)
    setError(null)

    try {
      const data = await subscriptionService.resumeSubscription(subscriptionId)
      if (data.success) {
        await fetchSubscriptions()
        return true
      } else {
        setError(data.message || '恢复订阅失败')
        return false
      }
    } catch (err) {
      setError('恢复订阅失败，请稍后重试')
      console.error('恢复订阅失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [fetchSubscriptions])

  // 获取推送记录
  const fetchPushRecords = useCallback(async (unreadOnly = false) => {
    setLoading(true)
    setError(null)

    try {
      const data = await subscriptionService.getPushRecords(unreadOnly)
      if (data.success) {
        setPushRecords(data.data.records || [])
      } else {
        setError(data.message || '获取推送记录失败')
      }
    } catch (err) {
      setError('获取推送记录失败，请稍后重试')
      console.error('获取推送记录失败:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // 标记为已读
  const markAsRead = useCallback(async (recordId) => {
    try {
      const data = await subscriptionService.markAsRead(recordId)
      if (data.success) {
        // 更新本地状态
        setPushRecords(prev => prev.map(r =>
          r.id === recordId ? { ...r, status: 'read', readAt: new Date() } : r
        ))
        setUnreadCount(prev => Math.max(0, prev - 1))
      }
    } catch (err) {
      console.error('标记已读失败:', err)
    }
  }, [])

  // 获取未读数量
  const fetchUnreadCount = useCallback(async () => {
    try {
      const data = await subscriptionService.getUnreadCount()
      if (data.success) {
        setUnreadCount(data.data.count || 0)
      }
    } catch (err) {
      console.error('获取未读数量失败:', err)
    }
  }, [])

  return {
    subscriptions, setSubscriptions,
    pushRecords, setPushRecords,
    unreadCount, setUnreadCount,
    loading, error, setError,
    fetchSubscriptions,
    createSubscription,
    updateSubscription,
    deleteSubscription,
    pauseSubscription,
    resumeSubscription,
    fetchPushRecords,
    markAsRead,
    fetchUnreadCount,
    frequencies: FREQUENCIES
  }
}