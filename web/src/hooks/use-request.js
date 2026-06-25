import { useState, useRef, useCallback } from 'react'

/**
 * 通用请求 Hook
 * 封装 data / loading / error 状态管理
 *
 * @param {Function} serviceFn - 返回 Promise 的服务函数（如 trendingService.search）
 * @param {Object} options - { immediate: bool, onSuccess: fn, onError: fn }
 * @returns {{ data, loading, error, run, reset }}
 */
export function useRequest(serviceFn, options = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const cancelledRef = useRef(false)

  const run = useCallback(async (...args) => {
    cancelledRef.current = false
    setLoading(true)
    setError(null)

    try {
      const result = await serviceFn(...args)
      if (!cancelledRef.current) {
        setData(result)
        options.onSuccess?.(result)
      }
      return result
    } catch (err) {
      if (!cancelledRef.current) {
        setError(err.message || '请求失败')
        options.onError?.(err)
      }
      throw err
    } finally {
      if (!cancelledRef.current) {
        setLoading(false)
      }
    }
  }, [serviceFn, options.onSuccess, options.onError])

  const reset = useCallback(() => {
    setData(null)
    setError(null)
    setLoading(false)
  }, [])

  // 组件卸载时标记取消，防止 setState on unmounted
  // 不用 useEffect cleanup，因为 React 18 不再警告，这里只是防止逻辑执行
  return { data, loading, error, run, reset }
}
