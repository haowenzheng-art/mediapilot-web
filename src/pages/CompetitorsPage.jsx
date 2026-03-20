import { useState } from 'react'
import { aiService, isAIEnabled } from '../services/api'
import { useApp, HISTORY_TYPES } from '../contexts/AppContext'
import { intelligentFormat } from '../utils/format'
import AIOutputFormatter from '../components/AIOutputFormatter'

function CompetitorsPage() {
  const [mode, setMode] = useState('single') // 'single' 或 'compare'
  const [platform, setPlatform] = useState('xiaohongshu')
  const aiEnabled = isAIEnabled()

  // 单账号分析
  const [singleAccount, setSingleAccount] = useState({
    name: '',
    followers: '',
    contentDirection: '',
    observations: ''
  })

  // 多账号对比
  const [accounts, setAccounts] = useState([
    { id: 1, name: '', followers: '', contentDirection: '', observations: '' },
    { id: 2, name: '', followers: '', contentDirection: '', observations: '' }
  ])

  const [result, setResult] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const { addHistory } = useApp()

  // 添加账号
  const addAccount = () => {
    if (accounts.length < 3) {
      setAccounts([...accounts, { id: Date.now(), name: '', followers: '', contentDirection: '', observations: '' }])
    }
  }

  // 删除账号
  const removeAccount = (id) => {
    if (accounts.length > 2) {
      setAccounts(accounts.filter(a => a.id !== id))
    }
  }

  // 更新账号信息
  const updateAccount = (id, field, value) => {
    setAccounts(accounts.map(a => a.id === id ? { ...a, [field]: value } : a))
  }

  // 单账号分析
  const handleSingleAnalyze = async () => {
    if (!singleAccount.name.trim() || isAnalyzing) return

    setIsAnalyzing(true)
    setResult('')

    try {
      const prompt = `账号：${singleAccount.name}
平台：${platform === 'xiaohongshu' ? '小红书' : platform === 'douyin' ? '抖音' : '其他'}
${singleAccount.followers ? `粉丝：${singleAccount.followers}` : ''}
${singleAccount.contentDirection ? `内容：${singleAccount.contentDirection}` : ''}
${singleAccount.observations ? `观察：${singleAccount.observations}` : ''}

请分析：
- 账号定位
- 内容策略
- 可复制经验
- 差异化建议`

      const messages = [
        { role: 'user', content: prompt }
      ]

      let fullContent = ''
      for await (const chunk of aiService.chatStream(messages, { maxTokens: 1200, temperature: 0.5 })) {
        fullContent += chunk
        setResult(intelligentFormat(fullContent))
      }

      addHistory(HISTORY_TYPES.COMPETITORS, {
        type: 'single',
        accountName: singleAccount.name,
        platform,
        result: fullContent
      })
    } catch (error) {
      console.error('Account analysis error:', error)
      setResult(`抱歉，账号分析失败：${error.message || '未知错误'}\n\n请检查：\n1. API配置是否正确\n2. 网络连接是否正常\n3. 或稍后再试`)
    } finally {
      setIsAnalyzing(false)
    }
  }

  // 多账号对比分析
  const handleCompareAnalyze = async () => {
    const validAccounts = accounts.filter(a => a.name.trim())
    if (validAccounts.length < 2 || isAnalyzing) return

    setIsAnalyzing(true)
    setResult('')

    try {
      let accountsInfo = validAccounts.map((a, idx) => `账号${idx + 1}：${a.name}${a.followers ? ` | 粉丝：${a.followers}` : ''}${a.contentDirection ? ` | 内容：${a.contentDirection}` : ''}${a.observations ? ` | 观察：${a.observations}` : ''}`).join('\n')

      const prompt = `平台：${platform === 'xiaohongshu' ? '小红书' : platform === 'douyin' ? '抖音' : '其他'}

待分析账号：
${accountsInfo}

请对比分析：
- 定位对比
- 内容策略对比
- 优劣势分析
- 可复用经验
- 差异化建议`

      const messages = [
        { role: 'user', content: prompt }
      ]

      let fullContent = ''
      for await (const chunk of aiService.chatStream(messages, { maxTokens: 1500, temperature: 0.5 })) {
        fullContent += chunk
        setResult(intelligentFormat(fullContent))
      }

      addHistory(HISTORY_TYPES.COMPETITORS, {
        type: 'compare',
        accountNames: validAccounts.map(a => a.name).join(' vs '),
        platform,
        result: fullContent
      })
    } catch (error) {
      console.error('Compare analysis error:', error)
      setResult(`抱歉，对比分析失败：${error.message || '未知错误'}\n\n请检查API配置或稍后再试`)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && e.ctrlKey) {
      e.preventDefault()
      if (mode === 'single') {
        handleSingleAnalyze()
      } else {
        handleCompareAnalyze()
      }
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <span>🔍</span> 账号分析
        </h2>

        {/* 模式切换 */}
        <div className="flex items-center gap-4">
          {/* 平台选择 */}
          <div className="flex gap-2">
            <button
              onClick={() => setPlatform('xiaohongshu')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                platform === 'xiaohongshu'
                  ? 'bg-red-500 text-white'
                  : 'bg-bg-light hover:bg-bg-light/80'
              }`}
            >
              <span>📖</span> 小红书
            </button>
            <button
              onClick={() => setPlatform('douyin')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                platform === 'douyin'
                  ? 'bg-primary text-white'
                  : 'bg-bg-light hover:bg-bg-light/80'
              }`}
            >
              <span>🎵</span> 抖音
            </button>
          </div>

          {/* 模式切换 */}
          <div className="flex gap-2 bg-bg-light rounded-lg p-1">
            <button
              onClick={() => { setMode('single'); setResult('') }}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                mode === 'single'
                  ? 'bg-card shadow-sm'
                  : 'hover:bg-card/50'
              }`}
            >
              <span>1️⃣</span> 单账号分析
            </button>
            <button
              onClick={() => { setMode('compare'); setResult('') }}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                mode === 'compare'
                  ? 'bg-card shadow-sm'
                  : 'hover:bg-card/50'
              }`}
            >
              <span>🆚</span> 多账号对比
            </button>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* 左侧 - 输入区域 */}
        <div className="space-y-6">
          <div className="card" style={{ height: 'fit-content' }}>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>📋</span> {mode === 'single' ? '输入账号信息' : '输入要对比的账号'}
            </h3>

            {mode === 'single' ? (
              /* 单账号输入 */
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">账号名称/ID *</label>
                  <input
                    type="text"
                    value={singleAccount.name}
                    onChange={(e) => setSingleAccount({...singleAccount, name: e.target.value})}
                    onKeyDown={handleKeyPress}
                    placeholder="请输入要分析的账号名称"
                    className="w-full px-4 py-3 bg-card border border-border rounded-lg focus:outline-none focus:border-primary"
                    disabled={isAnalyzing}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">粉丝数（可选）</label>
                  <input
                    type="text"
                    value={singleAccount.followers}
                    onChange={(e) => setSingleAccount({...singleAccount, followers: e.target.value})}
                    placeholder="例如：10万、50万、100万+"
                    className="w-full px-4 py-3 bg-card border border-border rounded-lg focus:outline-none focus:border-primary"
                    disabled={isAnalyzing}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">内容方向（可选）</label>
                  <input
                    type="text"
                    value={singleAccount.contentDirection}
                    onChange={(e) => setSingleAccount({...singleAccount, contentDirection: e.target.value})}
                    placeholder="例如：穿搭、美妆、职场、美食"
                    className="w-full px-4 py-3 bg-card border border-border rounded-lg focus:outline-none focus:border-primary"
                    disabled={isAnalyzing}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">你的观察（可选）</label>
                  <textarea
                    value={singleAccount.observations}
                    onChange={(e) => setSingleAccount({...singleAccount, observations: e.target.value})}
                    placeholder="说说你观察到的这个账号的特点..."
                    className="w-full p-4 bg-card border border-border rounded-lg focus:outline-none focus:border-primary resize-none"
                    style={{ height: '100px' }}
                    disabled={isAnalyzing}
                  />
                </div>

                {aiEnabled ? (
                  <button
                    onClick={handleSingleAnalyze}
                    disabled={isAnalyzing || !singleAccount.name.trim()}
                    className="btn btn-primary w-full"
                    style={{ padding: '16px' }}
                  >
                    {isAnalyzing ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="animate-pulse">正在深度拆解...</span>
                      </span>
                    ) : (
                      '🔍 开始拆解分析'
                    )}
                  </button>
                ) : (
                  <div className="p-4 bg-yellow-500/20 border border-yellow-500/30 rounded-lg text-center">
                    <p className="text-yellow-400">🔧 AI 功能暂未开放</p>
                    <p className="text-sm text-secondary mt-1">该功能为演示版本，请联系开发者体验</p>
                  </div>
                )}
              </div>
            ) : (
              /* 多账号对比输入 */
              <div className="space-y-4">
                {accounts.map((account, idx) => (
                  <div key={account.id} className="p-4 bg-bg-light rounded-lg border border-border relative">
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-semibold">账号 {idx + 1}</span>
                      {accounts.length > 2 && (
                        <button
                          onClick={() => removeAccount(account.id)}
                          className="text-red-400 hover:text-red-500 text-sm"
                          disabled={isAnalyzing}
                        >
                          删除
                        </button>
                      )}
                    </div>

                    <div className="space-y-3">
                      <input
                        type="text"
                        value={account.name}
                        onChange={(e) => updateAccount(account.id, 'name', e.target.value)}
                        placeholder="账号名称 *"
                        className="w-full px-3 py-2 bg-card border border-border rounded-lg focus:outline-none focus:border-primary text-sm"
                        disabled={isAnalyzing}
                      />
                      <input
                        type="text"
                        value={account.followers}
                        onChange={(e) => updateAccount(account.id, 'followers', e.target.value)}
                        placeholder="粉丝数（可选）"
                        className="w-full px-3 py-2 bg-card border border-border rounded-lg focus:outline-none focus:border-primary text-sm"
                        disabled={isAnalyzing}
                      />
                      <input
                        type="text"
                        value={account.contentDirection}
                        onChange={(e) => updateAccount(account.id, 'contentDirection', e.target.value)}
                        placeholder="内容方向（可选）"
                        className="w-full px-3 py-2 bg-card border border-border rounded-lg focus:outline-none focus:border-primary text-sm"
                        disabled={isAnalyzing}
                      />
                      <textarea
                        value={account.observations}
                        onChange={(e) => updateAccount(account.id, 'observations', e.target.value)}
                        placeholder="你的观察（可选）"
                        className="w-full px-3 py-2 bg-card border border-border rounded-lg focus:outline-none focus:border-primary text-sm resize-none"
                        style={{ height: '60px' }}
                        disabled={isAnalyzing}
                      />
                    </div>
                  </div>
                ))}

                {accounts.length < 3 && (
                  <button
                    onClick={addAccount}
                    className="w-full py-3 border-2 border-dashed border-border rounded-lg text-text-secondary hover:border-primary hover:text-primary transition-all"
                    disabled={isAnalyzing}
                  >
                    + 添加账号（最多3个）
                  </button>
                )}

                {aiEnabled ? (
                    <button
                      onClick={handleCompareAnalyze}
                      disabled={isAnalyzing || accounts.filter(a => a.name.trim()).length < 2}
                      className="btn btn-primary w-full"
                      style={{ padding: '16px' }}
                    >
                      {isAnalyzing ? (
                        <span className="flex items-center justify-center gap-2">
                          <span className="animate-pulse">正在对比分析...</span>
                        </span>
                      ) : (
                        '🆚 开始对比分析'
                      )}
                    </button>
                  ) : (
                    <div className="p-4 bg-yellow-500/20 border border-yellow-500/30 rounded-lg text-center">
                      <p className="text-yellow-400">🔧 AI 功能暂未开放</p>
                      <p className="text-sm text-secondary mt-1">该功能为演示版本，请联系开发者体验</p>
                    </div>
                  )}
              </div>
            )}

            <p className="text-xs text-text-secondary mt-3 text-center">
              提示：填的信息越多，分析越精准（Ctrl+Enter 快速分析）
            </p>
          </div>
        </div>

        {/* 右侧 - 输出区域 */}
        <div className="space-y-6">
          <div className="card" style={{ height: 'fit-content' }}>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <span>📊</span> {mode === 'single' ? '拆解分析结果' : '对比分析结果'}
            </h3>
            <div
              className="p-5 bg-card border border-border rounded-lg text-sm leading-relaxed"
              style={{ minHeight: '500px', maxHeight: '650px', overflow: 'auto' }}
            >
              {result ? (
                <AIOutputFormatter content={intelligentFormat(result)} />
              ) : (
                <div className="text-center text-secondary py-20">
                  <div className="text-5xl mb-4">
                    {mode === 'single' ? '🔍' : '🆚'}
                  </div>
                  <p>{mode === 'single' ? '输入账号信息后，拆解分析结果将在这里显示' : '输入2-3个账号，对比分析结果将在这里显示'}</p>
                  <p className="text-sm mt-2">AI会帮你深度分析账号的成功逻辑</p>
                </div>
              )}
            </div>
            {result && (
              <button
                onClick={() => {
                  navigator.clipboard.writeText(result)
                  alert('分析结果已复制到剪贴板！')
                }}
                className="btn btn-secondary w-full mt-4"
                style={{ padding: '16px' }}
              >
                📋 复制结果
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default CompetitorsPage
