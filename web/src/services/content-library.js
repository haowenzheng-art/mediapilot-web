/**
 * 内容库服务
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const contentLibraryService = {
  /**
   * 获取内容列表
   * @param {Object} filters - 筛选条件
   * @param {string} filters.content_type - 内容类型 (script, copywriting, video, audio)
   * @param {string} filters.topic - 话题
   * @param {string} filters.start_date - 开始日期
   * @param {string} filters.end_date - 结束日期
   * @param {string} filters.search - 搜索关键词
   * @param {number} page - 页码
   * @param {number} page_size - 每页数量
   */
  async getContents(filters = {}, page = 1, pageSize = 20) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      ...Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== undefined && v !== '')
      )
    })

    const response = await fetch(`${API_BASE}/content-library?${params}`)
    const data = await response.json()
    return data
  },

  /**
   * 获取内容详情
   * @param {number} contentId - 内容ID
   */
  async getContentDetail(contentId) {
    const response = await fetch(`${API_BASE}/content-library/${contentId}`)
    const data = await response.json()
    return data
  },

  /**
   * 获取关联内容
   * @param {number} contentId - 内容ID
   */
  async getRelatedContents(contentId) {
    const response = await fetch(`${API_BASE}/content-library/${contentId}/related`)
    const data = await response.json()
    return data
  },

  /**
   * 更新内容标签
   * @param {number} contentId - 内容ID
   * @param {Array} tags - 标签列表
   */
  async updateTags(contentId, tags) {
    const response = await fetch(`${API_BASE}/content-library/${contentId}/tags`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tags })
    })
    const data = await response.json()
    return data
  },

  /**
   * 关联话题
   * @param {number} contentId - 内容ID
   * @param {number} topicId - 话题ID
   */
  async linkTopic(contentId, topicId) {
    const response = await fetch(`${API_BASE}/content-library/${contentId}/link-topic`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic_id: topicId })
    })
    const data = await response.json()
    return data
  },

  /**
   * 取消关联话题
   * @param {number} contentId - 内容ID
   * @param {number} topicId - 话题ID
   */
  async unlinkTopic(contentId, topicId) {
    const response = await fetch(`${API_BASE}/content-library/${contentId}/unlink-topic`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic_id: topicId })
    })
    const data = await response.json()
    return data
  },

  /**
   * 删除内容
   * @param {number} contentId - 内容ID
   */
  async deleteContent(contentId) {
    const response = await fetch(`${API_BASE}/content-library/${contentId}`, {
      method: 'DELETE'
    })
    const data = await response.json()
    return data
  },

  /**
   * 获取统计信息
   */
  async getStats() {
    const response = await fetch(`${API_BASE}/content-library/stats`)
    const data = await response.json()
    return data
  }
}