import { useState, useEffect } from 'react'
import { getConfig, saveConfig, updateConfig, currentConfig } from '../services/api'

function SettingsPage() {
  const [config, setConfig] = useState(getConfig())
  const [saveStatus, setSaveStatus] = useState('')

  const handleSave = () => {
    saveConfig(config)
    updateConfig(config)
    setSaveStatus('✅ 配置已保存！')
    setTimeout(() => setSaveStatus(''), 2000)
  }

  const handleReset = () => {
    if (confirm('确定要重置为默认配置吗？')) {
      const defaultConfig = {
        provider: 'openai',
        apiKey: '1a73929c-d549-43e8-b03f-0d6e3e979771',
        baseUrl: 'https://ark.cn-beijing.volces.com/api/v3',
        model: 'ep-m-20260311150444-fn2zc',
      }
      setConfig(defaultConfig)
      saveConfig(defaultConfig)
      updateConfig(defaultConfig)
      setSaveStatus('✅ 已重置为默认配置！')
      setTimeout(() => setSaveStatus(''), 2000)
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <span>⚙️</span> 设置
      </h2>

      <div className="space-y-6">
        {/* API配置卡片 */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>🔑</span> API 配置
          </h3>
          <p className="text-sm text-secondary mb-6">
            配置已预设，无需修改即可使用！如有需要可以调整。
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">API Key</label>
              <input
                type="password"
                value={config.apiKey}
                onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                className="w-full px-4 py-3 bg-bg-light border border-border rounded-lg focus:outline-none focus:border-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Base URL</label>
              <input
                type="text"
                value={config.baseUrl}
                onChange={(e) => setConfig({ ...config, baseUrl: e.target.value })}
                className="w-full px-4 py-3 bg-bg-light border border-border rounded-lg focus:outline-none focus:border-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Model (接入点ID)</label>
              <input
                type="text"
                value={config.model}
                onChange={(e) => setConfig({ ...config, model: e.target.value })}
                className="w-full px-4 py-3 bg-bg-light border border-border rounded-lg focus:outline-none focus:border-primary"
              />
              <p className="text-xs text-secondary mt-2">
                火山方舟使用接入点ID（ep-xxxxx）而不是模型名称
              </p>
            </div>
          </div>

          <div className="flex gap-4 mt-6">
            <button
              onClick={handleSave}
              className="btn btn-primary flex-1"
            >
              💾 保存配置
            </button>
            <button
              onClick={handleReset}
              className="btn btn-secondary"
            >
              🔄 重置默认
            </button>
          </div>

          {saveStatus && (
            <div className="mt-4 p-3 bg-green-500/20 border border-green-500/30 rounded-lg text-green-400">
              {saveStatus}
            </div>
          )}
        </div>

        {/* 关于卡片 */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>ℹ️</span> 关于
          </h3>
          <div className="space-y-2 text-secondary">
            <p>MediaPilot 网页版</p>
            <p>版本：1.0.0</p>
            <p>✨ 6种主题切换</p>
            <p>🤖 AI助手聊天</p>
            <p>✍️ 脚本生成</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage