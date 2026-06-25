/**
 * 内容卡片组件
 */
function ContentCard({ content, onViewDetail, onEdit, onDelete }) {
  const getTypeIcon = (type) => {
    switch (type) {
      case 'script':
        return '🎬'
      case 'copywriting':
        return '🎤'
      case 'video':
        return '📹'
      case 'audio':
        return '🎙️'
      default:
        return '📄'
    }
  }

  const getTypeName = (type) => {
    const typeMap = {
      'script': '拍摄脚本',
      'copywriting': '口播文案',
      'video': '视频',
      'audio': '音频'
    }
    return typeMap[type] || type
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  }

  return (
    <div className="bg-white rounded-xl shadow hover:shadow-lg transition-all p-5 cursor-pointer group">
      {/* 顶部图标和类型标签 */}
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center group-hover:bg-purple-100 transition-colors text-2xl">
          {getTypeIcon(content.content_type)}
        </div>
        <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
          {getTypeName(content.content_type)}
        </span>
      </div>

      {/* 标题 */}
      <h3 className="font-semibold text-gray-800 mb-2 line-clamp-2">
        {content.title || '未命名内容'}
      </h3>

      {/* 摘要 */}
      <p className="text-sm text-gray-600 mb-3 line-clamp-3">
        {content.summary || content.content?.substring(0, 150) || '暂无摘要'}
      </p>

      {/* 话题标签 */}
      {content.topics && content.topics.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {content.topics.slice(0, 3).map((topic, idx) => (
            <span
              key={idx}
              className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs"
            >
              {topic.name || topic.topic}
            </span>
          ))}
          {content.topics.length > 3 && (
            <span className="px-2 py-0.5 text-gray-500 text-xs">
              +{content.topics.length - 3}
            </span>
          )}
        </div>
      )}

      {/* 标签 */}
      {content.tags && content.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {content.tags.slice(0, 3).map((tag, idx) => (
            <span
              key={idx}
              className="flex items-center gap-1 px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
            >
              🏷️ {tag}
            </span>
          ))}
          {content.tags.length > 3 && (
            <span className="px-2 py-0.5 text-gray-500 text-xs">
              +{content.tags.length - 3}
            </span>
          )}
        </div>
      )}

      {/* 底部信息 */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>📅</span>
          <span>{formatDate(content.created_at)}</span>
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onViewDetail(content.id)
            }}
            className="p-1.5 hover:bg-gray-100 rounded text-gray-600 hover:text-purple-600 transition-colors"
            title="查看详情"
          >
            👁️
          </button>
          {onEdit && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onEdit(content)
              }}
              className="p-1.5 hover:bg-gray-100 rounded text-gray-600 hover:text-blue-600 transition-colors"
              title="编辑"
            >
              ✏️
            </button>
          )}
          {onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDelete(content.id)
              }}
              className="p-1.5 hover:bg-red-50 rounded text-gray-600 hover:text-red-600 transition-colors"
              title="删除"
            >
              🗑️
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default ContentCard