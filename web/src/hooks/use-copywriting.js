/**
 * 口播文案 Hook
 */
import { useState, useCallback, useEffect } from 'react'
import { copywritingService } from '../services/copywriting'
import { useReasoningStreamRequest } from './use-reasoning-stream-request'

const MODES = [
  { id: 'from_zero', name: '从0到1', description: '输入话题，从头生成' },
  { id: 'hotspot', name: '热点框架', description: '使用热点内容框架生成' },
  { id: 'rewrite', name: '改写', description: '改写已有文案' }
]

const REWRITE_DIRECTIONS = [
  { id: 'more_colloquial', name: '更口语化', icon: '💬' },
  { id: 'add_emotion', name: '加情绪', icon: '😊' },
  { id: 'add_opinion', name: '加观点', icon: '💡' }
]

const REASONING_STORAGE_KEY = 'copywriting:enable_reasoning'

function readEnableReasoning() {
  try {
    const v = localStorage.getItem(REASONING_STORAGE_KEY)
    return v === null ? true : v === '1'  // 默认开启
  } catch {
    return true
  }
}

export function useCopywriting() {
  const [mode, setMode] = useState('from_zero')
  const [persona, setPersona] = useState('')
  const [personas, setPersonas] = useState([])
  const [topic, setTopic] = useState('')
  // C1: 跨页面跳转携带的热点元数据（来自 HotTopicContext）
  const [hotTopic, setHotTopic] = useState(null)
  const [hotspotContent, setHotspotContent] = useState('')
  const [originalText, setOriginalText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // 深度思考开关（持久化到 localStorage）
  const [enableReasoning, setEnableReasoningState] = useState(readEnableReasoning)
  const setEnableReasoning = useCallback((val) => {
    setEnableReasoningState(val)
    try {
      localStorage.setItem(REASONING_STORAGE_KEY, val ? '1' : '0')
    } catch {}
  }, [])

  // 流式生成：reasoning + content 双字段累积
  // streamFn 始终传全部 args，让 enableReasoning 由 generate 内部决定（避免 streamFn 引用变化）
  const streamFn = useCallback(
    (m, p, params, options) => copywritingService.generateStream(m, p, params, options),
    []
  )
  const {
    reasoning,
    content,
    reasoningSupported,
    meta,
    isStreaming,
    error: streamError,
    run: runStream,
    reset: resetStream,
  } = useReasoningStreamRequest(streamFn)

  // 获取人设列表
  const fetchPersonas = useCallback(async () => {
    try {
      const data = await copywritingService.getPersonas()
      if (data.success) {
        setPersonas(data.data.personas || [])
      }
    } catch (err) {
      console.error('获取人设列表失败:', err)
    }
  }, [])

  // 流式生成文案
  const generate = useCallback(async () => {
    if (!persona.trim()) {
      setError('请输入人设')
      return
    }

    // 根据模式验证参数
    const params = {}
    if (mode === 'from_zero' && !topic.trim()) {
      setError('请输入话题')
      return
    }
    if (mode === 'hotspot' && !hotspotContent.trim()) {
      setError('请粘贴热点内容')
      return
    }
    if (mode === 'rewrite' && !originalText.trim()) {
      setError('请粘贴原文')
      return
    }

    if (mode === 'from_zero') {
      params.topic = topic
    } else if (mode === 'hotspot') {
      params.hotspot_content = hotspotContent
    } else if (mode === 'rewrite') {
      params.original_text = originalText
    }

    // C1: 携带热点关联（让内容库反查可拿到 hot_topic_id）
    if (hotTopic) {
      params.hot_topic_id = hotTopic.id
      params.hot_topic_title = hotTopic.title
      params.hot_topic_source = hotTopic.source
    }

    setLoading(true)
    setError(null)
    setResult(null)
    resetStream()

    try {
      await runStream(mode, persona, params, { enableReasoning })
      // runStream 完成后 result 在 streamFn 内部 meta.parsed 里已生成
      // 这里通过 meta hook 已经能拿到，但更直接是等 runStream 后从 hook meta 取
    } catch (err) {
      setError('生成失败，请稍后重试')
      console.error('生成文案失败:', err)
    } finally {
      setLoading(false)
    }
  }, [mode, persona, topic, hotspotContent, originalText, hotTopic, runStream, enableReasoning, resetStream])

  // 流式完成（meta.final=true）后从 meta.parsed 写入 result state
  // 用 useEffect 监听 meta 变化
  useEffect(() => {
    if (meta?.final && meta?.parsed) {
      setResult(meta.parsed)
    }
  }, [meta])

  // 改写文案（保留原阻塞逻辑，避免流式改造范围爆炸）
  const rewrite = useCallback(async (direction) => {
    if (!result?.id) {
      return
    }

    setLoading(true)
    setError(null)

    try {
      const data = await copywritingService.rewrite(result.id, direction)
      if (data.success) {
        setResult(data.data)
      } else {
        setError(data.message || '改写失败')
      }
    } catch (err) {
      setError('改写失败，请稍后重试')
      console.error('改写文案失败:', err)
    } finally {
      setLoading(false)
    }
  }, [result])

  // 创建人设
  const createPersona = useCallback(async (personaDescription) => {
    try {
      const data = await copywritingService.createPersona(personaDescription)
      if (data.success) {
        await fetchPersonas()
        setPersona(personaDescription)
        return true
      }
      return false
    } catch (err) {
      console.error('创建人设失败:', err)
      return false
    }
  }, [fetchPersonas])

  // 删除人设
  const deletePersona = useCallback(async (personaId) => {
    try {
      const data = await copywritingService.deletePersona(personaId)
      if (data.success) {
        await fetchPersonas()
      }
    } catch (err) {
      console.error('删除人设失败:', err)
    }
  }, [fetchPersonas])

  // 选择人设
  const selectPersona = useCallback((personaDescription) => {
    setPersona(personaDescription)
  }, [])

  // 复制结果
  const copyResult = useCallback(() => {
    if (!result) return

    const text = `标题：${result.title}

钩子：
${result.hooks.map((h, i) => `${i + 1}. ${h}`).join('\n')}

文案：
${result.content}`

    navigator.clipboard.writeText(text).then(() => {
      alert('已复制到剪贴板')
    }).catch(() => {
      alert('复制失败，请手动复制')
    })
  }, [result])

  return {
    mode, setMode,
    persona, setPersona,
    personas, setPersonas,
    topic, setTopic,
    hotspotContent, setHotspotContent,
    originalText, setOriginalText,
    hotTopic, setHotTopic,  // C1
    result, setResult,
    loading, error, setError,
    // 流式相关
    enableReasoning, setEnableReasoning,
    reasoning, content, reasoningSupported,
    isStreaming,
    streamError,
    generate,
    rewrite,
    createPersona,
    deletePersona,
    selectPersona,
    copyResult,
    modes: MODES,
    rewriteDirections: REWRITE_DIRECTIONS
  }
}
