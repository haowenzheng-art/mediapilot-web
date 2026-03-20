import { useState, useEffect } from 'react'
import { aiService, isAIEnabled } from '../services/api'
import { useApp, HISTORY_TYPES } from '../contexts/AppContext'
import { intelligentFormat } from '../utils/format'
import AIOutputFormatter from '../components/AIOutputFormatter'

function ScriptPage() {
  const [topic, setTopic] = useState('')
  const [script, setScript] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const { addHistory, selectedContent, setSelectedContent } = useApp()
  const aiEnabled = isAIEnabled()

  // 检查是否有从热点搜索传来的数据
  useEffect(() => {
    if (selectedContent?.type === 'hotSearch') {
      setTopic(`基于以下热点分析创作脚本：\n\n${selectedContent.data}`)
      // 清空已传递的内容
      setSelectedContent(null)
    }
  }, [selectedContent, setSelectedContent])

  const handleGenerate = async () => {
    if (!topic.trim() || isGenerating) return

    setIsGenerating(true)
    setScript('')

    try {
      const prompt = `主题：${topic}

请输出：
- 标题
- 钩子
- 分镜头脚本（5-6个）
- 话题标签`

      const messages = [
        { role: 'user', content: prompt }
      ]

      let fullContent = ''
      for await (const chunk of aiService.chatStream(messages, { maxTokens: 1200, temperature: 0.5 })) {
        fullContent += chunk
        setScript(intelligentFormat(fullContent))
      }

      // 保存到历史记录
      addHistory(HISTORY_TYPES.SCRIPT, {
        topic: topic.substring(0, 100),
        result: fullContent
      })
    } catch (error) {
      console.error('Script generation error:', error)
      setScript('抱歉，脚本生成失败，请稍后再试。')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleGenerate()
    }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 flex items-center justify-center gap-2">
        <span>✍️</span> 脚本生成
      </h2>

      <div className="grid lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
        {/* 左侧 - 输入区域 */}
        <div className="space-y-6">
          <div className="card" style={{ height: '100%' }}>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>💡</span> 输入选题
            </h3>
            {selectedContent?.type === 'hotSearch' && (
              <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <p className="text-sm text-blue-600 dark:text-blue-400">
                  ✨ 检测到热点分析内容，已自动填充！
                </p>
              </div>
            )}
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder='请输入你想要创作的短视频主题，例如：如何提高工作效率

提示：
• 主题要具体，比如"新手怎么学编程"比"学编程"更好
• 可以包含特定的风格要求，比如"用幽默的风格"
• 明确目标受众，比如"给职场新人"'
              className="w-full p-5 bg-card border border-border rounded-lg focus:outline-none focus:border-primary min-h-[400px] resize-none text-base leading-relaxed"
              style={{ height: '450px' }}
              disabled={isGenerating}
            />
            {aiEnabled ? (
              <button
                onClick={handleGenerate}
                disabled={isGenerating || !topic.trim()}
                className="mt-4 btn btn-primary w-full"
                style={{ padding: '16px' }}
              >
                {isGenerating ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-pulse">生成中...</span>
                  </span>
                ) : (
                  '✨ 生成脚本'
                )}
              </button>
            ) : (
              <div className="mt-4 p-4 bg-yellow-500/20 border border-yellow-500/30 rounded-lg text-center">
                <p className="text-yellow-400">🔧 AI 功能暂未开放</p>
                <p className="text-sm text-secondary mt-1">该功能为演示版本，请联系开发者体验</p>
              </div>
            )}
          </div>
        </div>

        {/* 右侧 - 输出区域 */}
        <div className="space-y-6">
          <div className="card" style={{ height: '100%' }}>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>📝</span> 生成结果
            </h3>
            <div
              className="p-5 bg-card border border-border rounded-lg text-sm leading-relaxed"
              style={{ minHeight: '450px', height: '450px', overflow: 'auto' }}
            >
              {script ? (
                <AIOutputFormatter content={intelligentFormat(script)} />
              ) : (
                <div className="text-center text-secondary py-20">
                  <div className="text-5xl mb-4">✨</div>
                  <p>输入选题后，生成的脚本将在这里显示</p>
                </div>
              )}
            </div>
            {script && (
              <div className="flex gap-3 mt-4">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(script)
                    alert('脚本已复制到剪贴板！')
                  }}
                  className="btn btn-secondary flex-1"
                  style={{ padding: '16px' }}
                >
                  📋 复制脚本
                </button>
                <button
                  onClick={() => {
                    // 这里可以添加发送到日历的功能
                    alert('请切换到"发布日历"标签页，选择日期添加备注！')
                  }}
                  className="btn btn-primary flex-1"
                  style={{ padding: '16px' }}
                >
                  📅 添加到日历
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ScriptPage
