import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSubscription } from '../../hooks/use-subscription'
import PageContainer from '../../components/common/PageContainer'

const inputStyle = {
  width: '100%',
  padding: '10px 14px',
  fontSize: '13px',
  border: '1px solid var(--border-color)',
  borderRadius: '8px',
  background: 'var(--bg-secondary)',
  color: 'var(--text-primary)',
  outline: 'none',
}

const labelStyle = {
  display: 'block',
  fontSize: '12px',
  color: 'var(--text-tertiary)',
  marginBottom: '6px',
}

const btnPrimary = {
  padding: '10px 18px',
  background: 'var(--accent-primary)',
  color: 'var(--bg-primary)',
  border: 'none',
  borderRadius: '8px',
  fontSize: '13px',
  fontWeight: '500',
  cursor: 'pointer',
}

const btnGhost = {
  padding: '10px 14px',
  background: 'transparent',
  color: 'var(--text-secondary)',
  border: '1px solid var(--border-color)',
  borderRadius: '8px',
  fontSize: '13px',
  cursor: 'pointer',
}

const cardStyle = {
  padding: '20px',
  background: 'var(--card-bg)',
  borderRadius: '12px',
  border: '1px solid var(--border-color)',
}

const tabBtnStyle = (active) => ({
  padding: '10px 18px',
  background: active ? 'var(--card-bg)' : 'transparent',
  color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
  border: active ? '1px solid var(--border-color)' : '1px solid transparent',
  borderRadius: '8px',
  fontSize: '13px',
  fontWeight: active ? '600' : '400',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
})

const badgeStyle = (bg, color) => ({
  padding: '2px 8px',
  background: bg,
  color,
  borderRadius: '10px',
  fontSize: '11px',
  fontWeight: '500',
})

const iconBtnStyle = {
  padding: '6px 8px',
  background: 'transparent',
  border: 'none',
  color: 'var(--text-tertiary)',
  cursor: 'pointer',
  fontSize: '14px',
  borderRadius: '4px',
}

function SubscriptionForm({ formData, setFormData, frequencies, onSubmit, onClose, submitLabel }) {
  return (
    <form onSubmit={onSubmit}>
      <div style={{ marginBottom: '16px' }}>
        <label style={labelStyle}>话题 *</label>
        <input
          type="text"
          value={formData.topic}
          onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
          placeholder="例如：AI、香港金融、跨境电商"
          style={inputStyle}
          required
          autoFocus
        />
      </div>
      <div style={{ marginBottom: '16px' }}>
        <label style={labelStyle}>描述</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="描述这个订阅的内容..."
          style={{ ...inputStyle, minHeight: '72px', resize: 'vertical' }}
        />
      </div>
      <div style={{ marginBottom: '24px' }}>
        <label style={labelStyle}>推送频率</label>
        <select
          value={formData.frequency}
          onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
          style={inputStyle}
        >
          {frequencies.map((freq) => (
            <option key={freq.id} value={freq.id}>{freq.name} - {freq.description}</option>
          ))}
        </select>
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
        <button type="button" onClick={onClose} style={btnGhost}>取消</button>
        <button type="submit" style={btnPrimary}>{submitLabel}</button>
      </div>
    </form>
  )
}

function Modal({ title, onClose, children }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0, 0, 0, 0.3)',
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg-primary)',
          border: '1px solid var(--border-color)',
          borderRadius: '16px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
          padding: '24px',
          width: '100%',
          maxWidth: '440px',
          maxHeight: '90vh',
          overflow: 'auto',
        }}
      >
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingBottom: '16px',
          marginBottom: '16px',
          borderBottom: '1px solid var(--border-color)',
        }}>
          <h2 style={{ fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)' }}>{title}</h2>
          <button
            onClick={onClose}
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: 'transparent',
              border: 'none',
              color: 'var(--text-tertiary)',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >✕</button>
        </div>
        {children}
      </motion.div>
    </div>
  )
}

function SubscriptionPage() {
  const {
    subscriptions,
    pushRecords,
    unreadCount,
    loading,
    error,
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

  const [activeTab, setActiveTab] = useState('subscriptions')
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingSubscription, setEditingSubscription] = useState(null)
  const [formData, setFormData] = useState({ topic: '', description: '', frequency: 'daily' })

  useEffect(() => {
    fetchSubscriptions()
    fetchPushRecords()
    fetchUnreadCount()
  }, [])

  const handleRefreshPushes = () => {
    fetchPushRecords()
    fetchUnreadCount()
  }

  const handleAddSubscription = async (e) => {
    e.preventDefault()
    const success = await createSubscription(formData.topic, formData.description, formData.frequency)
    if (success) {
      setShowAddModal(false)
      setFormData({ topic: '', description: '', frequency: 'daily' })
    }
  }

  const handleEditSubscription = (sub) => {
    setEditingSubscription(sub)
    setFormData({
      topic: sub.topic,
      description: sub.description || '',
      frequency: sub.frequency
    })
    setShowEditModal(true)
  }

  const handleSaveEdit = async (e) => {
    e.preventDefault()
    const success = await updateSubscription(editingSubscription.id, {
      topic: formData.topic,
      description: formData.description,
      frequency: formData.frequency
    })
    if (success) {
      setShowEditModal(false)
      setEditingSubscription(null)
      setFormData({ topic: '', description: '', frequency: 'daily' })
    }
  }

  const handleDeleteSubscription = async (subscriptionId) => {
    if (!confirm('确定要删除这个订阅吗？')) return
    await deleteSubscription(subscriptionId)
  }

  const handleTogglePause = async (subscriptionId, isPaused) => {
    if (isPaused) await resumeSubscription(subscriptionId)
    else await pauseSubscription(subscriptionId)
  }

  const handleMarkAsRead = async (recordId) => {
    await markAsRead(recordId)
  }

  const getFrequencyText = (frequency) => {
    const freq = frequencies.find(f => f.id === frequency)
    return freq ? freq.name : frequency
  }

  const getStatusText = (status) => {
    const statusMap = { 'active': '进行中', 'paused': '已暂停', 'read': '已读', 'unread': '未读' }
    return statusMap[status] || status
  }

  return (
    <PageContainer
      title="话题订阅与自动推送"
      description="订阅您感兴趣的话题，系统将自动为您推送最新热点"
    >
      {/* Tab 切换 */}
      <div style={{
        display: 'flex',
        gap: '6px',
        marginBottom: '20px',
        padding: '4px',
        background: 'var(--bg-accent)',
        borderRadius: '10px',
        width: 'fit-content',
      }}>
        <button
          onClick={() => setActiveTab('subscriptions')}
          style={tabBtnStyle(activeTab === 'subscriptions')}
        >
          我的订阅
          <span style={badgeStyle(activeTab === 'subscriptions' ? 'var(--bg-accent)' : 'transparent', 'var(--text-secondary)')}>
            {subscriptions.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab('pushes')}
          style={tabBtnStyle(activeTab === 'pushes')}
        >
          推送记录
          {unreadCount > 0 && (
            <span style={badgeStyle('rgba(220, 38, 38, 0.1)', '#dc2626')}>
              {unreadCount} 未读
            </span>
          )}
        </button>
      </div>

      <AnimatePresence mode="wait">
        {activeTab === 'subscriptions' && (
          <motion.div
            key="subscriptions"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {/* 添加订阅按钮 */}
            <button
              onClick={() => setShowAddModal(true)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                padding: '16px 20px',
                background: 'var(--card-bg)',
                border: '1px dashed var(--border-color)',
                borderRadius: '12px',
                cursor: 'pointer',
                marginBottom: '14px',
                color: 'var(--text-secondary)',
                fontSize: '14px',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-primary)'
                e.currentTarget.style.color = 'var(--accent-primary)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-color)'
                e.currentTarget.style.color = 'var(--text-secondary)'
              }}
            >
              <span style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: 'var(--bg-accent)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '18px',
              }}>+</span>
              添加话题订阅
            </button>

            {/* 订阅列表 */}
            {subscriptions.length === 0 ? (
              <div style={{
                ...cardStyle,
                textAlign: 'center',
                padding: '48px 24px',
                color: 'var(--text-tertiary)',
              }}>
                <div style={{ fontSize: '32px', marginBottom: '10px' }}>📭</div>
                <div style={{ fontSize: '14px' }}>暂无订阅</div>
                <div style={{ fontSize: '12px', marginTop: '4px' }}>点击上方按钮添加感兴趣的话题</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {subscriptions.map((sub) => (
                  <motion.div
                    key={sub.id}
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    style={cardStyle}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                          <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)' }}>
                            {sub.topic}
                          </h3>
                          <span style={badgeStyle(
                            sub.status === 'active' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                            sub.status === 'active' ? '#16a34a' : '#d97706'
                          )}>
                            {getStatusText(sub.status)}
                          </span>
                        </div>
                        {sub.description && (
                          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                            {sub.description}
                          </p>
                        )}
                        <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--text-tertiary)' }}>
                          <span>推送频率: {getFrequencyText(sub.frequency)}</span>
                          <span>已推送: {sub.pushCount || 0} 条</span>
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <button
                          onClick={() => handleTogglePause(sub.id, sub.status === 'paused')}
                          style={iconBtnStyle}
                          title={sub.status === 'paused' ? '恢复订阅' : '暂停订阅'}
                        >
                          {sub.status === 'paused' ? '▶️' : '⏸️'}
                        </button>
                        <button
                          onClick={() => handleEditSubscription(sub)}
                          style={iconBtnStyle}
                          title="编辑"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => handleDeleteSubscription(sub.id)}
                          style={iconBtnStyle}
                          title="删除"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* 推送记录 */}
        {activeTab === 'pushes' && (
          <motion.div
            key="pushes"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '14px',
              fontSize: '13px',
              color: 'var(--text-tertiary)',
            }}>
              <span>共 {pushRecords.length} 条推送记录</span>
              <button onClick={handleRefreshPushes} style={btnGhost}>
                {loading ? '⏳' : '🔄'} 刷新
              </button>
            </div>

            {pushRecords.length === 0 ? (
              <div style={{
                ...cardStyle,
                textAlign: 'center',
                padding: '48px 24px',
                color: 'var(--text-tertiary)',
              }}>
                <div style={{ fontSize: '32px', marginBottom: '10px' }}>📭</div>
                <div style={{ fontSize: '14px' }}>暂无推送记录</div>
                <div style={{ fontSize: '12px', marginTop: '4px' }}>
                  系统会按订阅频率自动扫描新热点并推送到这里
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {pushRecords.map((record) => (
                  <motion.div
                    key={record.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    style={{
                      ...cardStyle,
                      borderLeft: record.status === 'unread'
                        ? '3px solid var(--accent-primary)'
                        : '1px solid var(--border-color)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontSize: '13px', fontWeight: '500', color: 'var(--text-primary)' }}>
                          {record.topic}
                        </span>
                        <span style={badgeStyle(
                          record.status === 'unread' ? 'var(--bg-accent)' : 'transparent',
                          record.status === 'unread' ? 'var(--text-primary)' : 'var(--text-tertiary)'
                        )}>
                          {getStatusText(record.status)}
                        </span>
                      </div>
                      <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
                        {new Date(record.pushedAt).toLocaleString('zh-CN')}
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {record.hotspots?.map((hotspot, idx) => (
                        <div key={idx} style={{
                          padding: '10px 12px',
                          background: 'var(--bg-secondary)',
                          borderRadius: '6px',
                          fontSize: '13px',
                        }}>
                          <span style={{ color: 'var(--text-tertiary)', marginRight: '6px' }}>
                            {hotspot.platform}:
                          </span>
                          <span style={{ color: 'var(--text-primary)' }}>{hotspot.title}</span>
                        </div>
                      ))}
                    </div>
                    {record.status === 'unread' && (
                      <button
                        onClick={() => handleMarkAsRead(record.id)}
                        style={{
                          ...btnPrimary,
                          marginTop: '12px',
                          padding: '6px 14px',
                          fontSize: '12px',
                        }}
                      >
                        标记为已读
                      </button>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 错误提示 */}
      {error && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          background: 'rgba(220, 38, 38, 0.05)',
          border: '1px solid rgba(220, 38, 38, 0.2)',
          borderRadius: '8px',
          color: '#dc2626',
          fontSize: '13px',
        }}>
          {error}
        </div>
      )}

      {/* 添加订阅弹窗 */}
      <AnimatePresence>
        {showAddModal && (
          <Modal title="添加话题订阅" onClose={() => { setShowAddModal(false); setFormData({ topic: '', description: '', frequency: 'daily' }) }}>
            <SubscriptionForm
              formData={formData}
              setFormData={setFormData}
              frequencies={frequencies}
              onSubmit={handleAddSubscription}
              onClose={() => { setShowAddModal(false); setFormData({ topic: '', description: '', frequency: 'daily' }) }}
              submitLabel={loading ? '创建中...' : '创建订阅'}
            />
          </Modal>
        )}
      </AnimatePresence>

      {/* 编辑订阅弹窗 */}
      <AnimatePresence>
        {showEditModal && (
          <Modal title="编辑订阅" onClose={() => { setShowEditModal(false); setEditingSubscription(null); setFormData({ topic: '', description: '', frequency: 'daily' }) }}>
            <SubscriptionForm
              formData={formData}
              setFormData={setFormData}
              frequencies={frequencies}
              onSubmit={handleSaveEdit}
              onClose={() => { setShowEditModal(false); setEditingSubscription(null); setFormData({ topic: '', description: '', frequency: 'daily' }) }}
              submitLabel={loading ? '保存中...' : '保存'}
            />
          </Modal>
        )}
      </AnimatePresence>
    </PageContainer>
  )
}

export default SubscriptionPage
