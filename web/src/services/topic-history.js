/**
 * 话题历史服务
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const topicHistoryService = {
  /**
   * 获取话题列表
   */
  async getTopics() {
    const response = await fetch(`${API_BASE}/topic-history/topics`)
    const data = await response.json()
    return data
  },

  /**
   * 获取话题详情
   * @param {number} topicId - 话题ID
   */
  async getTopicDetail(topicId) {
    const response = await fetch(`${API_BASE}/topic-history/topics/${topicId}`)
    const data = await response.json()
    return data
  },

  /**
   * 获取话题趋势数据
   * @param {number} topicId - 话题ID
   * @param {string} startDate - 开始日期
   * @param {string} endDate - 结束日期
   */
  async getTopicTrend(topicId, startDate, endDate) {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate
    })
    const response = await fetch(`${API_BASE}/topic-history/topics/${topicId}/trend?${params}`)
    const data = await response.json()
    return data
  },

  /**
   * 获取话题关联内容
   * @param {number} topicId - 话题ID
   * @param {number} page - 页码
   * @param {number} pageSize - 每页数量
   */
  async getTopicContents(topicId, page = 1, pageSize = 20) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    })
    const response = await fetch(`${API_BASE}/topic-history/topics/${topicId}/contents?${params}`)
    const data = await response.json()
    return data
  },

  /**
   * 获取话题关联热点
   * @param {number} topicId - 话题ID
   */
  async getTopicHotspots(topicId) {
    const response = await fetch(`${API_BASE}/topic-history/topics/${topicId}/hotspots`)
    const data = await response.json()
    return data
  },

  /**
   * 创建话题
   * @param {Object} data - 话题数据
   */
  async createTopic(data) {
    const response = await fetch(`${API_BASE}/topic-history/topics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    const result = await response.json()
    return result
  },

  /**
   * 更新话题
   * @param {number} topicId - 话题ID
   * @param {Object} data - 更新数据
   */
  async updateTopic(topicId, data) {
    const response = await fetch(`${API_BASE}/topic-history/topics/${topicId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    const result = await response.json()
    return result
  },

  /**
   * 删除话题
   * @param {number} topicId - 话题ID
   */
  async deleteTopic(topicId) {
    const response = await fetch(`${API_BASE}/topic-history/topics/${topicId}`, {
      method: 'DELETE'
    })
    const result = await response.json()
    return result
  }
}