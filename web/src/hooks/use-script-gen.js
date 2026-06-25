import { useState, useCallback } from 'react'
import { useRequest } from './use-request'
import { contentService } from '../services/content'
import { getCurrentUser } from '../services/auth'

const PLATFORMS = [
  { id: 'douyin', name: '抖音', icon: '🎵' },
  { id: 'xiaohongshu', name: '小红书', icon: '📖' },
  { id: 'bilibili', name: 'B站', icon: '📺' },
]

const STYLES = [
  { id: 'professional', name: '专业风', desc: '严谨、专业权威' },
  { id: 'humorous', name: '幽默风', desc: '轻松、有趣易懂' },
  { id: 'concise', name: '简洁风', desc: '直接、不啰嗦' },
  { id: 'emotional', name: '情感风', desc: '共鸣、情绪打动' },
  { id: 'storytelling', name: '故事风', desc: '叙事、情节完整' },
]

const DURATIONS = [
  { id: 15, name: '15秒' },
  { id: 30, name: '30秒' },
  { id: 60, name: '60秒' },
  { id: 90, name: '90秒' },
  { id: 120, name: '120秒' },
]

export function useScriptGen() {
  const [topic, setTopic] = useState('')
  const [platform, setPlatform] = useState('douyin')
  const [style, setStyle] = useState('professional')
  const [duration, setDuration] = useState(60)
  const { data, loading, error, run } = useRequest(contentService.generate)
  const currentUser = getCurrentUser()

  const generate = useCallback(() => {
    if (!topic.trim()) return
    run({ topic, platform, style, duration }).catch(err => {
      alert(`生成失败: ${err.message || '未知错误'}`)
    })
  }, [topic, platform, style, duration, run])

  const copyResult = useCallback(() => {
    if (!data) return
    navigator.clipboard.writeText(JSON.stringify(data, null, 2))
    alert('脚本已复制到剪贴板！')
  }, [data])

  return {
    topic, setTopic,
    platform, setPlatform,
    style, setStyle,
    duration, setDuration,
    result: data, loading, error,
    generate, copyResult,
    currentUser,
    platforms: PLATFORMS,
    styles: STYLES,
    durations: DURATIONS,
  }
}
