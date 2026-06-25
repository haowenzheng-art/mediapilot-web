import { useState, useCallback, useRef } from 'react'

/**
 * 流式请求 Hook
 * 处理 SSE 流式响应的增量拼接
 *
 * @param {Function} streamFn - 返回 async generator 的服务函数（如 aiService.chatStream）
 * @returns {{ streamData, isStreaming, error, run, reset, abort }}
 */
export function useStreamRequest(streamFn) {
  const [streamData, setStreamData] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const run = useCallback(async (...args) => {
    setIsStreaming(true)
    setError(null)
    setStreamData('')

    try {
      const stream = streamFn(...args)
      let accumulated = ''

      for await (const chunk of stream) {
        accumulated += chunk
        setStreamData(accumulated)
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message || '流式请求失败')
      }
    } finally {
      setIsStreaming(false)
    }
  }, [streamFn])

  const abort = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
  }, [])

  const reset = useCallback(() => {
    setStreamData('')
    setError(null)
    setIsStreaming(false)
  }, [])

  return { streamData, isStreaming, error, run, reset, abort }
}
