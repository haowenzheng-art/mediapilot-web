import { useState, useCallback, useRef } from 'react'

/**
 * 双字段流式 Hook（reasoning + content）
 *
 * 与 use-stream-request 不同：累积两个独立字段（思考过程 + 最终答案）。
 * SSE 事件对象格式（来自 backend/core/ai_service.py generate_stream）：
 *   {"type": "content", "delta": "..."}     最终答案片段
 *   {"type": "reasoning", "delta": "..."}   深度思考片段
 *   {"type": "meta", "meta": {...}}         元数据（reasoning_supported、final 等）
 *   {"type": "error", "delta": "..."}       错误
 *
 * @param {Function} streamFn - async generator（yield 事件对象）
 * @returns {{
 *   reasoning: string,            // 累积的深度思考内容
 *   content: string,              // 累积的最终答案内容
 *   reasoningSupported: boolean,  // 后端是否返回过 reasoning（控制折叠区显隐）
 *   meta: object|null,            // 最后一次 meta 事件（带 parsed/final 等）
 *   isStreaming: boolean,
 *   error: string|null,
 *   run: (...args) => Promise<void>,
 *   reset: () => void,
 *   abort: () => void
 * }}
 */
export function useReasoningStreamRequest(streamFn) {
  const [reasoning, setReasoning] = useState('')
  const [content, setContent] = useState('')
  const [reasoningSupported, setReasoningSupported] = useState(false)
  const [meta, setMeta] = useState(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const run = useCallback(async (...args) => {
    setIsStreaming(true)
    setError(null)
    setReasoning('')
    setContent('')
    setReasoningSupported(false)
    setMeta(null)

    try {
      const stream = streamFn(...args)
      for await (const event of stream) {
        if (!event || typeof event !== 'object') continue
        if (event.type === 'reasoning' && event.delta) {
          setReasoning((prev) => prev + event.delta)
        } else if (event.type === 'content' && event.delta) {
          setContent((prev) => prev + event.delta)
        } else if (event.type === 'meta' && event.meta) {
          if (event.meta.reasoning_supported) {
            setReasoningSupported(true)
          }
          setMeta(event.meta)
        } else if (event.type === 'error') {
          setError(event.delta || '流式生成失败')
        }
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
    setReasoning('')
    setContent('')
    setReasoningSupported(false)
    setMeta(null)
    setError(null)
    setIsStreaming(false)
  }, [])

  return {
    reasoning,
    content,
    reasoningSupported,
    meta,
    isStreaming,
    error,
    run,
    reset,
    abort,
  }
}