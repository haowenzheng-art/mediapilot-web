/**
 * 拍摄脚本 Hook
 */
import { useState, useCallback, useEffect } from 'react'
import { shootScriptService } from '../services/shoot-script'
import { useReasoningStreamRequest } from './use-reasoning-stream-request'

const PLATFORMS = [
  { id: 'douyin', name: '抖音', icon: '📱', description: '竖屏短视频，可选 60/120/180 秒' },
  { id: 'xiaohongshu', name: '小红书', icon: '📕', description: '竖屏，可选 60/120/180 秒' },
  { id: 'bilibili', name: 'B站', icon: '📺', description: '横屏 5-10 分钟，深度' }
]

const DURATIONS = [
  { id: 60,  name: '60 秒',  description: '短平快，5 个分镜' },
  { id: 120, name: '120 秒', description: '叙事感，8 个分镜' },
  { id: 180, name: '180 秒', description: '完整故事，10 个分镜' }
]

const STYLES = [
  { id: 'energetic', name: '激情热血', icon: '🔥', description: '充满能量，号召力强' },
  { id: 'relaxed', name: '轻松幽默', icon: '😊', description: '有趣风趣，轻松愉快' },
  { id: 'professional', name: '专业分析', icon: '💼', description: '数据驱动，专业严谨' }
]

const REASONING_STORAGE_KEY = 'shoot_script:enable_reasoning'

function readEnableReasoning() {
  try {
    const v = localStorage.getItem(REASONING_STORAGE_KEY)
    return v === null ? true : v === '1'
  } catch {
    return true
  }
}

export function useShootScript() {
  const [topic, setTopic] = useState('')
  // C1: 跨页面跳转携带的热点元数据（来自 HotTopicContext）
  const [hotTopic, setHotTopic] = useState(null)
  const [platform, setPlatform] = useState('douyin')
  const [duration, setDuration] = useState(60)
  const [style, setStyle] = useState('energetic')
  const [persona, setPersona] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [enableReasoning, setEnableReasoningState] = useState(readEnableReasoning)
  const setEnableReasoning = useCallback((val) => {
    setEnableReasoningState(val)
    try {
      localStorage.setItem(REASONING_STORAGE_KEY, val ? '1' : '0')
    } catch {}
  }, [])

  const streamFn = useCallback(
    (t, p, st, pe, dur, options) => {
      // C1: 携带热点关联（让内容库反查可拿到 hot_topic_id）
      const mergedOptions = { ...(options || {}) }
      if (hotTopic) {
        mergedOptions.hotTopic = hotTopic  // 传给 service，service 拆字段
      }
      return shootScriptService.generateStream(t, p, st, pe, dur, mergedOptions)
    },
    [hotTopic]
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

  // 生成脚本（流式）
  const generate = useCallback(async () => {
    if (!topic.trim()) {
      setError('请输入话题')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    resetStream()

    try {
      const dur = platform === 'bilibili' ? null : duration
      await runStream(topic, platform, style, persona, dur, { enableReasoning })
    } catch (err) {
      setError('生成失败，请稍后重试')
      console.error('生成拍摄脚本失败:', err)
    } finally {
      setLoading(false)
    }
  }, [topic, platform, style, persona, duration, runStream, enableReasoning, resetStream])

  // 流式完成（meta.final=true）后从 meta.parsed 写入 result state
  useEffect(() => {
    if (meta?.final && meta?.parsed) {
      setResult(meta.parsed)
    }
  }, [meta])

  // 导出脚本
  const exportScript = useCallback(async (format) => {
    if (!result?.id) {
      return
    }

    try {
      await shootScriptService.export(result.id, format)
    } catch (err) {
      setError('导出失败，请稍后重试')
      console.error('导出拍摄脚本失败:', err)
    }
  }, [result])

  // 重新生成
  const regenerate = useCallback(() => {
    generate()
  }, [generate])

  // 复制脚本
  const copyScript = useCallback(() => {
    if (!result) return

    const text = `拍摄脚本 - ${result.topic}\n\n` +
      `平台: ${result.platform}\n` +
      `风格: ${result.style}\n` +
      `预计时长: ${result.estimated_duration}\n\n` +
      `标题: ${result.title}\n\n` +
      `钩子:\n${result.hooks.map((h, i) => `${i + 1}. ${h}`).join('\n')}\n\n` +
      `行动号召: ${result.call_to_action}\n\n` +
      `标签: ${result.tags.join(', ')}\n\n` +
      `分镜头脚本:\n\n` +
      result.shots.map(shot =>
        `镜头${shot.shot_number} [${shot.duration}]\n` +
        `画面: ${shot.visual_description}\n` +
        `台词: ${shot.dialogue}\n` +
        `场景: ${shot.scene_suggestion || ''}\n` +
        `运镜: ${shot.camera_movement || ''}\n`
      ).join('\n')

    navigator.clipboard.writeText(text).then(() => {
      alert('脚本已复制到剪贴板')
    }).catch(() => {
      alert('复制失败，请手动复制')
    })
  }, [result])

  return {
    topic, setTopic,
    platform, setPlatform,
    duration, setDuration,
    style, setStyle,
    persona, setPersona,
    hotTopic, setHotTopic,  // C1
    result, setResult,
    loading, error, setError,
    // 流式相关
    enableReasoning, setEnableReasoning,
    reasoning, content, reasoningSupported,
    isStreaming,
    streamError,
    generate,
    exportScript,
    regenerate,
    copyScript,
    platforms: PLATFORMS,
    durations: DURATIONS,
    styles: STYLES
  }
}
