import { useState } from 'react'
import { useApp, HISTORY_TYPES } from '../contexts/AppContext'
import { intelligentFormat } from '../utils/format'

function HistoryPage() {
  const { history, deleteHistory, clearHistory, getHistoryByType } = useApp()
  const [filterType, setFilterType] = useState('all')

  const filterOptions = [
    { id: 'all', name: '全部', icon: '📋' },
    { id: HISTORY_TYPES.HOT_SEARCH, name: '热点搜索', icon: '🔥' },
    { id: HISTORY_TYPES.COMPETITORS, name: '对标账号', icon: '👥' },
    { id: HISTORY_TYPES.SCRIPT, name: '脚本生成', icon: '✍️' },
    { id: HISTORY_TYPES.TEMPLATE, name: 'AI模板', icon: '📄' },
  ]

  const getTypeInfo = (type) => {
    switch (type) {
      case HISTORY_TYPES.HOT_SEARCH:
        return { name: '热点搜索', icon: '🔥', color: 'text-orange-500' }
      case HISTORY_TYPES.COMPETITORS:
        return { name: '对标账号', icon: '👥', color: 'text-blue-500' }
      case HISTORY_TYPES.SCRIPT:
        return { name: '脚本生成', icon: '✍️', color: 'text-green-500' }
      case HISTORY_TYPES.TEMPLATE:
        return { name: 'AI模板', icon: '📄', color: 'text-purple-500' }
      default:
        return { name: '未知', icon: '❓', color: 'text-gray-500' }
    }
  }

  const formatDate = (isoString) => {
    const date = new Date(isoString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getPreview = (data) => {
    if (data.query) return data.query.substring(0, 50)
    if (data.niche) return data.niche.substring(0, 50)
    if (data.topic) return data.topic.substring(0, 50)
    if (data.templateName) return data.templateName
    return '无预览'
  }

  const filteredHistory = filterType === 'all'
    ? history
    : getHistoryByType(filterType)

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <span>📜</span> 历史记录
        </h2>
        {history.length > 0 && (
          <button
            onClick={() => {
              if (confirm('确定要清空所有历史记录吗？')) {
                clearHistory()
              }
            }}
            className="btn btn-secondary text-sm px-4 py-2 text-red-500 hover:text-red-600"
          >
            🗑️ 清空全部
          </button>
        )}
      </div>

      {/* 筛选器 */}
      <div className="card mb-6">
        <div className="flex flex-wrap gap-2">
          {filterOptions.map(option => (
            <button
              key={option.id}
              onClick={() => setFilterType(option.id)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                filterType === option.id
                  ? 'bg-primary text-white'
                  : 'bg-bg-light hover:bg-bg-light/80'
              }`}
            >
              <span>{option.icon}</span>
              <span>{option.name}</span>
              {option.id === 'all' && (
                <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full">
                  {history.length}
                </span>
              )}
              {option.id !== 'all' && (
                <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full">
                  {getHistoryByType(option.id).length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 历史列表 */}
      {filteredHistory.length > 0 ? (
        <div className="space-y-4">
          {filteredHistory.map(item => {
            const typeInfo = getTypeInfo(item.type)
            return (
              <div key={item.id} className="card">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xl ${typeInfo.color}`}>{typeInfo.icon}</span>
                      <span className={`font-medium ${typeInfo.color}`}>{typeInfo.name}</span>
                      <span className="text-xs text-text-secondary">{formatDate(item.timestamp)}</span>
                    </div>
                    <p className="text-sm text-text-secondary mb-3">
                      {getPreview(item.data)}
                      {item.data.query?.length > 50 || item.data.niche?.length > 50 || item.data.topic?.length > 50 ? '...' : ''}
                    </p>
                    {item.data.result && (
                      <details className="mt-2">
                        <summary className="text-sm text-accent cursor-pointer hover:underline">
                          查看详情
                        </summary>
                        <div className="mt-2 p-3 bg-bg-light rounded-lg text-sm max-h-60 overflow-auto whitespace-pre-wrap">
                          {intelligentFormat(item.data.result)}
                        </div>
                      </details>
                    )}
                  </div>
                  <button
                    onClick={() => deleteHistory(item.id)}
                    className="text-text-secondary hover:text-red-500 p-2 transition-colors"
                    title="删除"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="card text-center py-16">
          <div className="text-5xl mb-4">📝</div>
          <p className="text-text-secondary text-lg">还没有历史记录</p>
          <p className="text-text-secondary text-sm mt-2">使用其他功能后，记录会在这里显示</p>
        </div>
      )}
    </div>
  )
}

export default HistoryPage
