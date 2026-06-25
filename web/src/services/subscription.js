/**
 * 话题订阅服务
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const subscriptionService = {
  /**
   * 获取订阅列表
   */
  async getSubscriptions() {
    const response = await fetch(`${API_BASE}/subscriptions`)
    const data = await response.json()
    return data
  },

  /**
   * 创建订阅
   */
  async createSubscription(topic, description, frequency) {
    const response = await fetch(`${API_BASE}/subscriptions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic,
        description,
        frequency
      })
    })
    const data = await response.json()
    return data
  },

  /**
   * 更新订阅
   */
  async updateSubscription(subscriptionId, updates) {
    const response = await fetch(`${API_BASE}/subscriptions/${subscriptionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    })
    const data = await response.json()
    return data
  },

  /**
   * 删除订阅
   */
  async deleteSubscription(subscriptionId) {
    const response = await fetch(`${API_BASE}/subscriptions/${subscriptionId}`, {
      method: 'DELETE'
    })
    const data = await response.json()
    return data
  },

  /**
   * 暂停订阅
   */
  async pauseSubscription(subscriptionId) {
    const response = await fetch(`${API_BASE}/subscriptions/${subscriptionId}/pause`, {
      method: 'POST'
    })
    const data = await response.json()
    return data
  },

  /**
   * 恢复订阅
   */
  async resumeSubscription(subscriptionId) {
    const response = await fetch(`${API_BASE}/subscriptions/${subscriptionId}/resume`, {
      method: 'POST'
    })
    const data = await response.json()
    return data
  },

  /**
   * 获取推送记录
   */
  async getPushRecords(unreadOnly = false) {
    const response = await fetch(`${API_BASE}/subscriptions/push/records?unread_only=${unreadOnly}`)
    const data = await response.json()
    return data
  },

  /**
   * 标记为已读
   */
  async markAsRead(recordId) {
    const response = await fetch(`${API_BASE}/subscriptions/push/records/${recordId}/read`, {
      method: 'POST'
    })
    const data = await response.json()
    return data
  },

  /**
   * 获取未读数量
   */
  async getUnreadCount() {
    const response = await fetch(`${API_BASE}/subscriptions/push/unread-count`)
    const data = await response.json()
    return data
  }
}