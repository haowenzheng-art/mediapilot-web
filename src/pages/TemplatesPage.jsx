import { useState } from 'react'
import { aiService, isAIEnabled } from '../services/api'
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
    id: 1,
    category: 'hook',
    name: '痛点提问式',
    description: '用痛点问题开头，直击用户需求',
    template: `你有没有遇到过【痛点问题】？

是不是【具体场景】的时候，总是【糟糕体验】？

今天我就教你【解决方案】！

【具体步骤/方法】

学会了吗？点赞收藏，下次用的时候就能找到！`,
  },
  {
    id: 2,
    category: 'hook',
    name: '数字震惊式',
    description: '用数字开头，抓住眼球',
    template: `【数字】个【事物】，【惊人结论】！

第1个：【内容1】
第2个：【内容2】
第3个：【内容3】

最后一个，【强调】！

你知道几个？评论区告诉我！`,
  },
  {
    id: 3,
    category: 'story',
    name: '个人经历式',
    description: '用真实经历引发共鸣',
    template: `曾经我【过去的困境】，直到【转折点】。

那时候，【具体困难】，真的【感受】。

后来我发现了【方法/契机】，从此【改变】。

今天分享给你：【核心内容】

希望对你有帮助！`,
  },
  {
    id: 4,
    category: 'tutorial',
    name: '三步教学法',
    description: '清晰三步，易学易用',
    template: `【技能/方法】，只需要三步！

第一步：【步骤1】
这里要注意【要点1】

第二步：【步骤2】
关键点是【要点2】

第三步：【步骤3】
这样做【好处】

学会了吗？快去试试！`,
  },
  {
    id: 5,
    category: 'review',
    name: '真实体验式',
    description: '真实体验，可信度高',
    template: `我用了【时间】【产品/方法】，说实话【初印象】。

刚开始【初期体验】，后来【深入体验】。

优点：
✅ 【优点1】
✅ 【优点2】

缺点：
❌ 【缺点1】

总结：【结论】。

你们觉得呢？`,
  },
  {
    id: 6,
    category: 'vlog',
    name: '一天记录式',
    description: '记录一天，真实自然',
    template: `欢迎来到我的一天！

早上【时间】，【早晨活动】

中午【时间】，【中午活动】

下午【时间】，【下午活动】

晚上【时间】，【晚上活动】

今天的感悟：【感悟】

明天见！👋`,
  },
]

function TemplatesPage() {
  const [selectedCategory, setSelectedCategory] = useState('hook')
  const [customTopic, setCustomTopic] = useState('')
  const [generatedTemplate, setGeneratedTemplate] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const aiEnabled = isAIEnabled()
  const { addHistory } = useApp()

  const filteredTemplates = PRESET_TEMPLATES.filter(t => t.category === selectedCategory)

  const useTemplate = (template) => {
    setSelectedTemplate(template)
    setGeneratedTemplate(template.template)
  }

  const generateCustomTemplate = async () => {
    if (!customTopic.trim() || isGenerating) return

    setIsGenerating(true)
    setGeneratedTemplate('')

    try {
      const prompt = `你是一个专业的短视频文案模板创作专家。请为以下主题创作一个实用的短视频文案模板：

用户主题：${customTopic}

请创作一个完整的、可直接使用的短视频文案模板，要求：
1. 结构清晰，有明确的开头、中间、结尾
2. 包含【】占位符，方便用户填充内容
3. 语言口语化，适合口播
4. 有互动引导（点赞、评论、关注）
5. 长度适合15-60秒的短视频

请直接输出模板内容，不要多余说明。`

      const messages = [
        { role: 'system', content: '你是一个专业的短视频文案模板创作专家。' },
        { role: 'user', content: prompt }
      ]

      let fullContent = ''
      for await (const chunk of aiService.chatStream(messages)) {
        fullContent += chunk
        setGeneratedTemplate(intelligentFormat(fullContent))
      }

      // 保存到历史记录
      addHistory(HISTORY_TYPES.TEMPLATE, {
        templateName: customTopic,
        result: fullContent
      })
    } catch (error) {
      console.error('Template generation error:', error)
      setGeneratedTemplate('抱歉，模板生成失败，请稍后再试。')
    } finally {
      setIsGenerating(false)
    }
  }

  const copyTemplate = () => {
    if (generatedTemplate) {
      navigator.clipboard.writeText(generatedTemplate)
      alert('模板已复制到剪贴板！')
    }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <span>📋</span> AI模板
      </h2>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* 左侧 - 模板选择 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 分类标签 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>📂</span> 模板分类
            </h3>
            <div className="flex flex-wrap gap-2">
              {TEMPLATE_CATEGORIES.map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                    selectedCategory === cat.id
                      ? 'bg-primary text-white'
                      : 'bg-bg-light hover:bg-bg-light/80'
                  }`}
                >
                  <span>{cat.icon}</span>
                  <span>{cat.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 模板列表 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>📝</span> 预设模板
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              {filteredTemplates.map(template => (
                <div
                  key={template.id}
                  className={`p-4 rounded-lg border border-border cursor-pointer transition-all hover:border-primary ${
                    selectedTemplate?.id === template.id ? 'border-primary bg-primary/5' : ''
                  }`}
                  onClick={() => useTemplate(template)}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-semibold">{template.name}</h4>
                      <p className="text-sm text-secondary mt-1">{template.description}</p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        useTemplate(template)
                      }}
                      className="btn btn-primary text-sm px-3 py-1.5"
                    >
                      使用
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 自定义模板生成 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>✨</span> 生成自定义模板
            </h3>
            <p className="text-secondary text-sm mb-4">
              输入你的主题，AI为你生成专属模板
            </p>
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="例如：产品测评、知识科普、情感励志..."
                value={customTopic}
                onChange={(e) => setCustomTopic(e.target.value)}
                className="flex-1 px-4 py-3 bg-bg-light border border-border rounded-lg focus:outline-none focus:border-primary"
                disabled={isGenerating}
              />
              {aiEnabled ? (
                <button
                  onClick={generateCustomTemplate}
                  disabled={isGenerating || !customTopic.trim()}
                  className="btn btn-primary whitespace-nowrap"
                >
                  {isGenerating ? (
                    <span className="animate-pulse">生成中...</span>
                  ) : (
                    '生成模板'
                  )}
                </button>
              ) : (
                <div className="px-4 py-3 bg-yellow-500/20 border border-yellow-500/30 rounded-lg text-center">
                  <p className="text-yellow-400 text-sm">🔧 AI 暂未开放</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 右侧 - 模板预览 */}
        <div className="space-y-6">
          <div className="card sticky top-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <span>👁️</span> 模板预览
              </h3>
              {generatedTemplate && (
                <button
                  onClick={copyTemplate}
                  className="btn btn-secondary text-sm px-3 py-1.5"
                >
                  📋 复制
                </button>
              )}
            </div>
            {generatedTemplate ? (
              <div className="p-4 bg-bg-light rounded-lg border border-border">
                <pre className="whitespace-pre-wrap text-sm leading-relaxed font-mono">
                  {generatedTemplate}
                </pre>
              </div>
            ) : (
              <div className="text-center py-12 text-secondary">
                <p className="text-4xl mb-4">📝</p>
                <p>选择一个模板或生成新模板</p>
                <p className="text-sm mt-2">模板将在这里显示</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default TemplatesPage
