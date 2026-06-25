/**
 * 内容详情弹窗组件
 */
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

function ContentDetailModal({ content, relatedContents, onClose, onCopy }) {
  const [showFullContent, setShowFullContent] = useState(false)

  if (!content) return null

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('zh-CN')
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

  const handleCopy = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      if (onCopy) onCopy(true)
    } catch (err) {
      console.error('复制失败:', err)
      if (onCopy) onCopy(false)
    }
  }

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden"
        >
          {/* 标题栏 */}
          <div className="flex items-center justify-between p-6 border-b border-gray-100">
            <div>
              <h2 className="text-xl font-bold text-gray-800">{content.title || '未命名内容'}</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                  {getTypeName(content.content_type)}
                </span>
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <span>📅</span>
                  <span>{formatDate(content.created_at)}</span>
                </div>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-xl"
            >
              ✕
            </button>
          </div>

          {/* 内容区域 */}
          <div className="p-6 overflow-y-auto max-h-[60vh]">
            {/* 摘要 */}
            {content.summary && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-2">摘要</h3>
                <p className="text-gray-600">{content.summary}</p>
              </div>
            )}

            {/* 话题标签 */}
            {content.topics && content.topics.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                  🏷️ 关联话题
                </h3>
                <div className="flex flex-wrap gap-2">
                  {content.topics.map((topic, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm"
                    >
                      {topic.name || topic.topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 内容标签 */}
            {content.tags && content.tags.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                  🏷️ 标签
                </h3>
                <div className="flex flex-wrap gap-2">
                  {content.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 正文内容 */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-700 flex items-center gap-1">
                  📄 内容正文
                </h3>
                <button
                  onClick={() => setShowFullContent(!showFullContent)}
                  className="text-sm text-purple-600 hover:text-purple-700 transition-colors"
                >
                  {showFullContent ? '收起' : '展开全部'}
                </button>
              </div>
              <div className={`p-4 bg-gray-50 rounded-lg ${showFullContent ? '' : 'line-clamp-10'}`}>
                <pre className="whitespace-pre-wrap text-gray-700 text-sm font-sans">
                  {content.content || '暂无内容'}
                </pre>
              </div>
              <button
                onClick={() => handleCopy(content.content || '')}
                className="mt-2 flex items-center gap-1 text-sm text-gray-600 hover:text-purple-600 transition-colors"
              >
                📋 复制内容
              </button>
            </div>

            {/* 关联内容 */}
            {relatedContents && relatedContents.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">关联内容</h3>
                <div className="space-y-2">
                  {relatedContents.map((item) => (
                    <div
                      key={item.id}
                      className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-800 mb-1">
                            {item.title || '未命名内容'}
                          </p>
                          <p className="text-xs text-gray-500 line-clamp-2">
                            {item.summary || item.content?.substring(0, 100)}
                          </p>
                        </div>
                        <span className="ml-2 text-xs text-gray-400">
                          {new Date(item.created_at).toLocaleDateString('zh-CN')}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 底部操作栏 */}
          <div className="flex justify-end gap-3 p-6 border-t border-gray-100 bg-gray-50">
            <button
              onClick={onClose}
              className="px-6 py-2 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
            >
              关闭
            </button>
            <button
              onClick={() => handleCopy(content.content || '')}
              className="flex items-center gap-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              📋 复制内容
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}

export default ContentDetailModal