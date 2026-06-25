/**
 * 拍摄脚本 Hook
 */
import { useState, useCallback } from 'react'
import { shootScriptService } from '../services/shoot-script'

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

export function useShootScript() {
  const [topic, setTopic] = useState('')
  const [platform, setPlatform] = useState('douyin')
  const [duration, setDuration] = useState(60)
  const [style, setStyle] = useState('energetic')
  const [persona, setPersona] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // 生成脚本
  const generate = useCallback(async () => {
    if (!topic.trim()) {
      setError('请输入话题')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // B 站不支持自定义时长，传 null 让后端走默认
      const dur = platform === 'bilibili' ? null : duration
      const data = await shootScriptService.generate(topic, platform, style, persona, dur)
      if (data.success) {
        setResult(data.data)
      } else {
        setError(data.message || '生成失败')
      }
    } catch (err) {
      setError('生成失败，请稍后重试')
      console.error('生成拍摄脚本失败:', err)
    } finally {
      setLoading(false)
    }
  }, [topic, platform, style, persona, duration])

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
    result, setResult,
    loading, error, setError,
    generate,
    exportScript,
    regenerate,
    copyScript,
    platforms: PLATFORMS,
    durations: DURATIONS,
    styles: STYLES
  }
}
