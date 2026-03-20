import { useState } from 'react'
import { aiService, isAIEnabled } from '../services/api'
import { useApp, HISTORY_TYPES } from '../contexts/AppContext'
import { intelligentFormat } from '../utils/format'
import AIOutputFormatter from '../components/AIOutputFormatter'

function HotSearchPage() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const { addHistory, setSelectedContent } = useApp()
  const aiEnabled = isAIEnabled()

  const handleSearch = async () => {
    if (!query.trim() || isSearching) return

    setIsSearching(true)
    setResult('')

    try {
      const prompt = `你是一个专业的行业热点分析专家。请帮我分析以下行业的热点话题：

用户查询：${query}

请执行以下步骤：
1. 理解用户想要了解的行业或领域
2. 分析当前该领域的热点话题和趋势
3. 提供有价值的选题建议
4. 给出具体的文案创作建议

请输出以下内容：
- 🔥 热点概述（当前该领域的热点话题）
- 📊 趋势分析（为什么这些话题受到关注）
- 💡 选题建议（3-5个具体的短视频选题）
- ✍️ 文案模板（为每个选题提供1个文案范例）

请用清晰的结构输出，语言要专业且实用。`

      const messages = [
        { role: 'system', content: '你是一个专业的行业热点分析专家，擅长捕捉趋势并提供创意建议。' },
        { role: 'user', content: prompt }
      ]

      let fullContent = ''
      for await (const chunk of aiService.chatStream(messages)) {
        fullContent += chunk
        setResult(intelligentFormat(fullContent))
      }

      // 保存到历史记录
      addHistory(HISTORY_TYPES.HOT_SEARCH, {
        query,
        result: fullContent
      })
    } catch (error) {
      console.error('Hot search error:', error)
      setResult(`抱歉，热点分析失败：${error.message}\n\n请检查：\n1. API配置是否正确\n2. 网络连接是否正常\n3. API key 是否有效`)
    } finally {
      setIsSearching(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6 flex items-center justify-center gap-2">
        <span>🔥</span> 热点搜索
      </h2>

      <div className="flex justify-center">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-5xl">
          {/* 左侧 - 输入区域 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>🔍</span> 输入你想了解的行业
            </h3>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="请输入你想了解的行业或领域，例如：

最近AI行业有什么热点
跨境电商趋势分析
健身行业热门话题
家居装修新趋势

用自然语言描述，越具体越好！"
              className="w-full p-4 bg-card border border-border rounded-lg focus:outline-none focus:border-primary resize-none text-base leading-relaxed"
              style={{ height: '400px' }}
              disabled={isSearching}
            />
            {aiEnabled ? (
              <button
                onClick={handleSearch}
                disabled={isSearching || !query.trim()}
                className="mt-4 btn btn-primary w-full py-3"
              >
                {isSearching ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-pulse">正在分析热点...</span>
                  </span>
                ) : (
                  '🚀 开始分析'
                )}
              </button>
            ) : (
              <div className="mt-4 p-4 bg-yellow-500/20 border border-yellow-500/30 rounded-lg text-center">
                <p className="text-yellow-400">🔧 AI 功能暂未开放</p>
                <p className="text-sm text-secondary mt-1">该功能为演示版本，请联系开发者体验</p>
              </div>
            )}
          </div>

          {/* 右侧 - 输出区域 */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>📋</span> 分析结果
            </h3>
            <div
              className="p-4 bg-card border border-border rounded-lg leading-relaxed"
              style={{ height: '400px', overflow: 'auto' }}
            >
              {result ? (
                <AIOutputFormatter content={intelligentFormat(result)} />
              ) : (
                <div className="text-center text-secondary py-16">
                  <div className="text-5xl mb-4">🔥</div>
                  <p>输入行业后，分析结果将在这里显示</p>
                </div>
              )}
            </div>
            {result && (
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(result)
                    alert('分析结果已复制到剪贴板！')
                  }}
                  className="btn btn-secondary flex-1 py-3"
                >
                  📋 复制结果
                </button>
                <button
                  onClick={() => {
                    setSelectedContent({ type: 'hotSearch', data: result })
                    alert('内容已准备好！请切换到"脚本生成"标签页继续。')
                  }}
                  className="btn btn-primary flex-1 py-3"
                >
                  ✍️ 生成脚本
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default HotSearchPage
