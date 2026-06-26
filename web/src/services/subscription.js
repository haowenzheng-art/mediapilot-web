/**
 * 话题订阅服务
 */
import { request } from './api'

const BASE = '/api/v1/subscriptions'

export const subscriptionService = {
  async getSubscriptions() {
    return request(BASE)
  },

  async createSubscription(topic, description, frequency) {
    return request(BASE, {
      method: 'POST',
      body: JSON.stringify({ topic, description, frequency })
    })
  },

  async updateSubscription(subscriptionId, updates) {
    return request(`${BASE}/${subscriptionId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    })
  },

  async deleteSubscription(subscriptionId) {
    return request(`${BASE}/${subscriptionId}`, { method: 'DELETE' })
  },

  async pauseSubscription(subscriptionId) {
    return request(`${BASE}/${subscriptionId}/pause`, { method: 'POST' })
  },

  async resumeSubscription(subscriptionId) {
    return request(`${BASE}/${subscriptionId}/resume`, { method: 'POST' })
  },

  async getPushRecords(unreadOnly = false) {
    return request(`${BASE}/push/records?unread_only=${unreadOnly}`)
  },

  async markAsRead(recordId) {
    return request(`${BASE}/push/records/${recordId}/read`, { method: 'POST' })
  },

  async getUnreadCount() {
    return request(`${BASE}/push/unread-count`)
  }
}
