import { useState, useCallback } from 'react'
import { useStreamRequest } from './use-stream-request'
import { aiService } from '../services/ai'
import { isAIEnabled } from '../services/api'
import { useApp, HISTORY_TYPES } from '../contexts/AppContext'
import { intelligentFormat } from '../utils/format'

const TEMPLATE_CATEGORIES = [
  { id: 'hook', name: '钩子开头', icon: '🎣' },
  { id: 'story', name: '故事叙述', icon: '📖' },
  { id: 'tutorial', name: '教程干货', icon: '🎓' },
  { id: 'interview', name: '访谈对话', icon: '🎙️' },
  { id: 'review', name: '评测体验', icon: '⭐' },
  { id: 'vlog', name: 'Vlog日常', icon: '🎬' },
]

const PRESET_TEMPLATES = [
  {
    id: 1, category: 'hook', name: '痛点提问式', description: '用痛点问题开头，直击用户需求',
    template: `你有没有遇到过【痛点问题】？\n\n是不是【具体场景】的时候，总是【糟糕体验】？\n\n今天我就教你【解决方案】！\n\n【具体步骤/方法】\n\n学会了吗？点赞收藏，下次用的时候就能找到！`,
  },
  {
    id: 2, category: 'hook', name: '数字震惊式', description: '用数字开头，抓住眼球',
    template: `【数字】个【事物】，【惊人结论】！\n\n第1个：【内容1】\n第2个：【内容2】\n第3个：【内容3】\n\n最后一个，【强调】！\n\n你知道几个？评论区告诉我！`,
  },
  {
    id: 3, category: 'story', name: '个人经历式', description: '用真实经历引发共鸣',
    template: `曾经我【过去的困境】，直到【转折点】。\n\n那时候，【具体困难】，真的【感受】。\n\n后来我发现了【方法/契机】，从此【改变】。\n\n今天分享给你：【核心内容】\n\n希望对你有帮助！`,
  },
  {
    id: 4, category: 'tutorial', name: '三步教学法', description: '清晰三步，易学易用',
    template: `【技能/方法】，只需要三步！\n\n第一步：【步骤1】\n这里要注意【要点1】\n\n第二步：【步骤2】\n关键点是【要点2】\n\n第三步：【步骤3】\n这样做【好处】\n\n学会了吗？快去试试！`,
  },
  {
    id: 5, category: 'review', name: '真实体验式', description: '真实体验，可信度高',
    template: `我用了【时间】【产品/方法】，说实话【初印象】。\n\n刚开始【初期体验】，后来【深入体验】。\n\n优点：\n✅ 【优点1】\n✅ 【优点2】\n\n缺点：\n❌ 【缺点1】\n\n总结：【结论】。\n\n你们觉得呢？`,
  },
  {
    id: 6, category: 'vlog', name: '一天记录式', description: '记录一天，真实自然',
    template: `欢迎来到我的一天！\n\n早上【时间】，【早晨活动】\n\n中午【时间】，【中午活动】\n\n下午【时间】，【下午活动】\n\n晚上【时间】，【晚上活动】\n\n今天的感悟：【感悟】\n\n明天见！👋`,
  },
]

export function useTemplates() {
  const [selectedCategory, setSelectedCategory] = useState('hook')
  const [customTopic, setCustomTopic] = useState('')
  const [generatedTemplate, setGeneratedTemplate] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const aiEnabled = isAIEnabled()
  const { addHistory } = useApp()

  const { isStreaming, run: runStream } = useStreamRequest(aiService.chatStream)

  const filteredTemplates = PRESET_TEMPLATES.filter(t => t.category === selectedCategory)

  const useTemplate = useCallback((template) => {
    setSelectedTemplate(template)
    setGeneratedTemplate(template.template)
  }, [])

  const generateCustomTemplate = useCallback(async () => {
    if (!customTopic.trim() || isStreaming) return
    setGeneratedTemplate('')

    const messages = [
      { role: 'system', content: '你是一个专业的短视频文案模板创作专家。' },
      { role: 'user', content: `你是一个专业的短视频文案模板创作专家。请为以下主题创作一个实用的短视频文案模板：\n\n用户主题：${customTopic}\n\n请创作一个完整的、可直接使用的短视频文案模板，要求：\n1. 结构清晰，有明确的开头、中间、结尾\n2. 包含【】占位符，方便用户填充内容\n3. 语言口语化，适合口播\n4. 有互动引导（点赞、评论、关注）\n5. 长度适合15-60秒的短视频\n\n请直接输出模板内容，不要多余说明。` },
    ]

    try {
      let fullContent = ''
      for await (const chunk of aiService.chatStream(messages)) {
        fullContent += chunk
        setGeneratedTemplate(intelligentFormat(fullContent))
      }
      addHistory(HISTORY_TYPES.TEMPLATE, { templateName: customTopic, result: fullContent })
    } catch (error) {
      setGeneratedTemplate('抱歉，模板生成失败，请稍后再试。')
    }
  }, [customTopic, isStreaming, addHistory])

  const copyTemplate = useCallback(() => {
    if (generatedTemplate) {
      navigator.clipboard.writeText(generatedTemplate)
      alert('模板已复制到剪贴板！')
    }
  }, [generatedTemplate])

  return {
    selectedCategory, setSelectedCategory,
    customTopic, setCustomTopic,
    generatedTemplate, selectedTemplate,
    isGenerating: isStreaming,
    useTemplate, generateCustomTemplate, copyTemplate,
    aiEnabled, filteredTemplates, categories: TEMPLATE_CATEGORIES,
  }
}
