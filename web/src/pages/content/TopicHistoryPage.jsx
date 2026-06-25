/**
 * 话题历史页面
 */
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useTopicHistory } from '../../hooks/use-topic-history'

function TopicHistoryPage() {
  const {
    topics,
    selectedTopic,
    trendData,
    topicContents,
    topicHotspots,
    loading,
    error,
    setError,
    fetchTopics,
    selectTopic,
    timeRanges
  } = useTopicHistory()

  const [selectedTimeRange, setSelectedTimeRange] = useState('7')
  const [showEmptyState, setShowEmptyState] = useState(!selectedTopic)

  // 加载话题列表
  useEffect(() => {
    fetchTopics()
  }, [])

  // 选择话题
  const handleSelectTopic = async (topicId) => {
    await selectTopic(topicId, selectedTimeRange)
    setShowEmptyState(false)
  }

  // 切换时间范围
  const handleTimeRangeChange = async (timeRange) => {
    setSelectedTimeRange(timeRange)
    if (selectedTopic) {
      await selectTopic(selectedTopic.id, timeRange)
    }
  }

  // 格式化日期
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      month: '2-digit',
      day: '2-digit'
    })
  }

  // 渲染趋势图表（使用CSS简单的条形图）
  const renderTrendChart = () => {
    if (!trendData || trendData.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          暂无趋势数据
        </div>
      )
    }

    const maxValue = Math.max(...trendData.map(d => d.content_count))

    return (
      <div className="flex items-end gap-2 h-48">
        {trendData.map((data, idx) => {
          const height = maxValue > 0 ? (data.content_count / maxValue) * 100 : 0
          const isMax = data.content_count === maxValue

          return (
            <div
              key={idx}
              className="flex-1 flex flex-col items-center group"
            >
              <div className="relative w-full h-full flex items-end justify-center">
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: `${height}%` }}
                  transition={{ duration: 0.5, delay: idx * 0.05 }}
                  className={`w-full max-w-[40px] rounded-t-lg transition-all group-hover:brightness-110 ${
                    isMax ? 'bg-purple-600' : 'bg-purple-400'
                  }`}
                >
                  {/* 数值标签 */}
                  {data.content_count > 0 && (
                    <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs font-medium text-gray-700">
                      {data.content_count}
                    </div>
                  )}
                </motion.div>
              </div>
              <div className="mt-2 text-xs text-gray-500 text-center">
                {formatDate(data.date)}
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            话题历史与追踪
          </h1>
          <p className="text-gray-600">
            追踪话题趋势，分析内容创作历史
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* 左侧：话题列表 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-800">话题列表</h2>
                <button
                  onClick={fetchTopics}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  title="刷新"
                >
                  🔄
                </button>
              </div>

              <div className="space-y-2">
                {topics.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    暂无话题
                  </div>
                ) : (
                  topics.map((topic) => (
                    <motion.div
                      key={topic.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      onClick={() => handleSelectTopic(topic.id)}
                      className={`p-3 rounded-lg cursor-pointer transition-all ${
                        selectedTopic?.id === topic.id
                          ? 'bg-purple-100 border-2 border-purple-400'
                          : 'hover:bg-gray-50 border-2 border-transparent'
                      }`}
                    >
                      <div className="font-medium text-gray-800 mb-1">
                        {topic.name}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>{topic.content_count || 0} 条内容</span>
                        <span>·</span>
                        <span>{topic.hotspot_count || 0} 个热点</span>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* 右侧：话题详情 */}
          <div className="lg:col-span-3">
            {showEmptyState ? (
              <div className="bg-white rounded-xl shadow p-12 text-center">
                <div className="mx-auto text-6xl text-gray-300 mb-4">📈</div>
                <h3 className="text-xl font-medium text-gray-700 mb-2">
                  选择一个话题
                </h3>
                <p className="text-gray-500">
                  从左侧列表选择一个话题，查看其趋势和关联内容
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* 话题信息 */}
                {selectedTopic && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-xl shadow p-6"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h2 className="text-2xl font-bold text-gray-800 mb-2">
                          {selectedTopic.name}
                        </h2>
                        {selectedTopic.description && (
                          <p className="text-gray-600">{selectedTopic.description}</p>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold text-purple-600">
                          {selectedTopic.content_count || 0}
                        </div>
                        <div className="text-sm text-gray-500">相关内容</div>
                      </div>
                    </div>

                    {/* 时间范围选择器 */}
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-600">时间范围：</span>
                      {timeRanges.map((range) => (
                        <button
                          key={range.id}
                          onClick={() => handleTimeRangeChange(range.id)}
                          className={`px-3 py-1 rounded-lg text-sm transition-all ${
                            selectedTimeRange === range.id
                              ? 'bg-purple-600 text-white'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          {range.name}
                        </button>
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* 趋势图表 */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="bg-white rounded-xl shadow p-6"
                >
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    📈 内容创作趋势
                  </h3>
                  {renderTrendChart()}
                </motion.div>

                {/* 关联内容 */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="bg-white rounded-xl shadow p-6"
                >
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    📄 关联内容
                  </h3>

                  {topicContents.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      暂无关联内容
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {topicContents.map((content, idx) => (
                        <motion.div
                          key={content.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.3 + idx * 0.05 }}
                          className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h4 className="font-medium text-gray-800 mb-1">
                                {content.title || '未命名内容'}
                              </h4>
                              <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                                {content.summary || content.content?.substring(0, 100)}
                              </p>
                              <div className="flex items-center gap-2 text-xs text-gray-500">
                                <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded">
                                  {content.content_type === 'script' ? '拍摄脚本' :
                                   content.content_type === 'copywriting' ? '口播文案' :
                                   content.content_type === 'video' ? '视频' : '音频'}
                                </span>
                                <span className="flex items-center gap-1">
                                  📅 {new Date(content.created_at).toLocaleDateString('zh-CN')}
                                </span>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </motion.div>

                {/* 关联热点 */}
                {topicHotspots.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-white rounded-xl shadow p-6"
                  >
                    <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                      🔥 关联热点
                    </h3>

                    <div className="space-y-2">
                      {topicHotspots.map((hotspot, idx) => (
                        <div
                          key={idx}
                          className="p-3 bg-orange-50 rounded-lg"
                        >
                          <div className="flex items-start gap-2">
                            <span className="text-orange-600 font-medium text-sm">
                              {hotspot.platform}:
                            </span>
                            <p className="text-gray-700 text-sm flex-1">
                              {hotspot.title}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600">{error}</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default TopicHistoryPage