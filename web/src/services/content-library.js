/**
 * 内容库服务
 *
 * 后端实际路由（backend/api/content_library.py）：
 *   GET    /contents                 列表
 *   POST   /contents                 创建
 *   GET    /contents/{id}            详情
 *   PUT    /contents/{id}            更新
 *   DELETE /contents/{id}            删除
 *   POST   /contents/{id}/process    标记已用
 *   GET    /hot-topic/{id}/contents  热点反查
 *   POST   /topic-history            话题趋势
 *   GET    /health                   健康检查
 */
import { request } from './api'

const BASE = '/api/v1/content-library'

export const contentLibraryService = {
  async getContents(filters = {}, page = 1, pageSize = 20) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      ...Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== undefined && v !== '')
      )
    })
    return request(`${BASE}/contents?${params}`)
  },

  async getContentDetail(contentId) {
    return request(`${BASE}/contents/${contentId}`)
  },

  async deleteContent(contentId) {
    return request(`${BASE}/contents/${contentId}`, { method: 'DELETE' })
  },

  async markAsProcessed(contentId) {
    return request(`${BASE}/contents/${contentId}/process`, { method: 'POST' })
  },

  async getContentsByHotTopic(hotTopicId) {
    return request(`${BASE}/hot-topic/${hotTopicId}/contents`)
  },

  async getTopicHistory(payload) {
    return request(`${BASE}/topic-history`, {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  }
}
