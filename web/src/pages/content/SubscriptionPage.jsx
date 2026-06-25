/**
 * 话题订阅与自动推送页面
 */
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSubscription } from '../../hooks/use-subscription'

function SubscriptionPage() {
  const {
    subscriptions,
    pushRecords,
    unreadCount,
    loading,
    error,
    setError,
    fetchSubscriptions,
    createSubscription,
    updateSubscription,
    deleteSubscription,
    pauseSubscription,
    resumeSubscription,
    fetchPushRecords,
    markAsRead,
    fetchUnreadCount,
    frequencies
  } = useSubscription()

  const [activeTab, setActiveTab] = useState('subscriptions') // 'subscriptions' or 'pushes'
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingSubscription, setEditingSubscription] = useState(null)
  const [formData, setFormData] = useState({
    topic: '',
    description: '',
    frequency: 'daily'
  })

  // 加载数据
  useEffect(() => {
    fetchSubscriptions()
    fetchPushRecords()
    fetchUnreadCount()
  }, [])

  // 刷新推送记录
  const handleRefreshPushes = () => {
    fetchPushRecords()
    fetchUnreadCount()
  }

  // 处理添加订阅
  const handleAddSubscription = async (e) => {
    e.preventDefault()
    const success = await createSubscription(
      formData.topic,
      formData.description,
      formData.frequency
    )
    if (success) {
      setShowAddModal(false)
      setFormData({ topic: '', description: '', frequency: 'daily' })
    }
  }

  // 处理编辑订阅
  const handleEditSubscription = (sub) => {
    setEditingSubscription(sub)
    setFormData({
      topic: sub.topic,
      description: sub.description || '',
      frequency: sub.frequency
    })
    setShowEditModal(true)
  }

  // 处理保存编辑
  const handleSaveEdit = async (e) => {
    e.preventDefault()
    const success = await updateSubscription(
      editingSubscription.id,
      {
        topic: formData.topic,
        description: formData.description,
        frequency: formData.frequency
      }
    )
    if (success) {
      setShowEditModal(false)
      setEditingSubscription(null)
      setFormData({ topic: '', description: '', frequency: 'daily' })
    }
  }

  // 处理删除订阅
  const handleDeleteSubscription = async (subscriptionId) => {
    if (!confirm('确定要删除这个订阅吗？')) return
    await deleteSubscription(subscriptionId)
  }

  // 处理暂停/恢复订阅
  const handleTogglePause = async (subscriptionId, isPaused) => {
    if (isPaused) {
      await resumeSubscription(subscriptionId)
    } else {
      await pauseSubscription(subscriptionId)
    }
  }

  // 处理标记已读
  const handleMarkAsRead = async (recordId) => {
    await markAsRead(recordId)
  }

  // 获取频率显示文本
  const getFrequencyText = (frequency) => {
    const freq = frequencies.find(f => f.id === frequency)
    return freq ? freq.name : frequency
  }

  // 获取状态文本
  const getStatusText = (status) => {
    const statusMap = {
      'active': '进行中',
      'paused': '已暂停',
      'read': '已读',
      'unread': '未读'
    }
    return statusMap[status] || status
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            话题订阅与自动推送
          </h1>
          <p className="text-gray-600">
            订阅您感兴趣的话题，系统将自动为您推送最新热点
          </p>
        </div>

        {/* Tab 切换 */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setActiveTab('subscriptions')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'subscriptions'
                ? 'bg-white shadow-lg text-purple-600'
                : 'bg-white/50 text-gray-600 hover:bg-white'
            }`}
          >
            我的订阅
            <span className="ml-2 px-2 py-0.5 bg-purple-100 rounded-full text-sm">
              {subscriptions.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('pushes')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'pushes'
                ? 'bg-white shadow-lg text-purple-600'
                : 'bg-white/50 text-gray-600 hover:bg-white'
            }`}
          >
            推送记录
            {unreadCount > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-600 rounded-full text-sm">
                {unreadCount} 未读
              </span>
            )}
          </button>
        </div>

        {/* 订阅列表 */}
        <AnimatePresence mode="wait">
          {activeTab === 'subscriptions' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
            >
              <div className="grid gap-4">
                {/* 添加订阅按钮 */}
                <button
                  onClick={() => setShowAddModal(true)}
                  className="flex items-center gap-2 p-4 bg-white rounded-xl shadow hover:shadow-lg transition-all border-2 border-dashed border-purple-200 hover:border-purple-400 group"
                >
                  <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center group-hover:bg-purple-200 transition-colors">
                    ➕
                  </div>
                  <span className="text-purple-600 font-medium">添加话题订阅</span>
                </button>

                {/* 订阅列表 */}
                {subscriptions.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <p>暂无订阅，点击上方按钮添加话题</p>
                  </div>
                ) : (
                  subscriptions.map((sub) => (
                    <motion.div
                      key={sub.id}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="bg-white rounded-xl shadow hover:shadow-lg transition-all p-5"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold text-gray-800">
                              {sub.topic}
                            </h3>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                              sub.status === 'active'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-yellow-100 text-yellow-700'
                            }`}>
                              {getStatusText(sub.status)}
                            </span>
                          </div>
                          {sub.description && (
                            <p className="text-gray-600 text-sm mb-2">
                              {sub.description}
                            </p>
                          )}
                          <div className="flex items-center gap-4 text-sm text-gray-500">
                            <span>
                              推送频率: {getFrequencyText(sub.frequency)}
                            </span>
                            <span>
                              已推送: {sub.pushCount || 0} 条
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleTogglePause(sub.id, sub.status === 'paused')}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            title={sub.status === 'paused' ? '恢复订阅' : '暂停订阅'}
                          >
                            {sub.status === 'paused' ? (
                              <span>▶️</span>
                            ) : (
                              <span>⏸️</span>
                            )}
                          </button>
                          <button
                            onClick={() => handleEditSubscription(sub)}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            title="编辑"
                          >
                            <span>✏️</span>
                          </button>
                          <button
                            onClick={() => handleDeleteSubscription(sub.id)}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            title="删除"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </motion.div>
          )}

          {/* 推送记录 */}
          {activeTab === 'pushes' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
            >
              <div className="flex items-center justify-between mb-4">
                <p className="text-gray-600">
                  共 {pushRecords.length} 条推送记录
                </p>
                <button
                  onClick={handleRefreshPushes}
                  className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg hover:bg-gray-50 transition-colors"
                >
                  {loading ? '🔄' : '🔄'}
                  刷新
                </button>
              </div>

              <div className="grid gap-4">
                {pushRecords.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <p>暂无推送记录</p>
                  </div>
                ) : (
                  pushRecords.map((record) => (
                    <motion.div
                      key={record.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`bg-white rounded-xl shadow hover:shadow-lg transition-all p-5 ${
                        record.status === 'unread' ? 'border-l-4 border-purple-500' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium text-purple-600">
                            {record.topic}
                          </span>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            record.status === 'unread'
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}>
                            {getStatusText(record.status)}
                          </span>
                        </div>
                        <span className="text-sm text-gray-500">
                          {new Date(record.pushedAt).toLocaleString('zh-CN')}
                        </span>
                      </div>
                      <div className="space-y-2">
                        {record.hotspots?.map((hotspot, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-gray-50 rounded-lg"
                          >
                            <div className="flex items-start gap-2">
                              <span className="text-purple-600 font-medium">
                                {hotspot.platform}:
                              </span>
                              <p className="text-gray-700 text-sm">
                                {hotspot.title}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                      {record.status === 'unread' && (
                        <button
                          onClick={() => handleMarkAsRead(record.id)}
                          className="mt-3 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm"
                        >
                          标记为已读
                        </button>
                      )}
                    </motion.div>
                  ))
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 错误提示 */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {/* 添加订阅弹窗 */}
        <AnimatePresence>
          {showAddModal && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md"
              >
                <h2 className="text-xl font-bold text-gray-800 mb-4">
                  添加话题订阅
                </h2>
                <form onSubmit={handleAddSubscription}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        话题 *
                      </label>
                      <input
                        type="text"
                        value={formData.topic}
                        onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                        placeholder="例如：AI、香港金融、跨境电商"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        描述
                      </label>
                      <textarea
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        placeholder="描述这个订阅的内容..."
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        rows={3}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        推送频率
                      </label>
                      <select
                        value={formData.frequency}
                        onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        {frequencies.map((freq) => (
                          <option key={freq.id} value={freq.id}>
                            {freq.name} - {freq.description}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="flex justify-end gap-3 mt-6">
                    <button
                      type="button"
                      onClick={() => {
                        setShowAddModal(false)
                        setFormData({ topic: '', description: '', frequency: 'daily' })
                      }}
                      className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      取消
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                    >
                      {loading ? '创建中...' : '创建订阅'}
                    </button>
                  </div>
                </form>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        {/* 编辑订阅弹窗 */}
        <AnimatePresence>
          {showEditModal && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md"
              >
                <h2 className="text-xl font-bold text-gray-800 mb-4">
                  编辑订阅
                </h2>
                <form onSubmit={handleSaveEdit}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        话题 *
                      </label>
                      <input
                        type="text"
                        value={formData.topic}
                        onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        描述
                      </label>
                      <textarea
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        rows={3}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        推送频率
                      </label>
                      <select
                        value={formData.frequency}
                        onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        {frequencies.map((freq) => (
                          <option key={freq.id} value={freq.id}>
                            {freq.name} - {freq.description}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="flex justify-end gap-3 mt-6">
                    <button
                      type="button"
                      onClick={() => {
                        setShowEditModal(false)
                        setEditingSubscription(null)
                        setFormData({ topic: '', description: '', frequency: 'daily' })
                      }}
                      className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      取消
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                    >
                      {loading ? '保存中...' : '保存'}
                    </button>
                  </div>
                </form>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default SubscriptionPage