/**
 * 口播文案 Hook
 */
import { useState, useCallback } from 'react'
import { copywritingService } from '../services/copywriting'

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

export function useCopywriting() {
  const [mode, setMode] = useState('from_zero')
  const [persona, setPersona] = useState('')
  const [personas, setPersonas] = useState([])
  const [topic, setTopic] = useState('')
  const [hotspotContent, setHotspotContent] = useState('')
  const [originalText, setOriginalText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

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

  // 生成文案
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

    setLoading(true)
    setError(null)

    try {
      const data = await copywritingService.generate(mode, persona, params)
      if (data.success) {
        setResult(data.data)
      } else {
        setError(data.message || '生成失败')
      }
    } catch (err) {
      setError('生成失败，请稍后重试')
      console.error('生成文案失败:', err)
    } finally {
      setLoading(false)
    }
  }, [mode, persona, topic, hotspotContent, originalText])

  // 改写文案
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
    result, setResult,
    loading, error, setError,
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
