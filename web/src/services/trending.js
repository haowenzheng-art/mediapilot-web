/**
 * 热点搜索服务
 */
import { request, downloadFile } from './api'

export const trendingService = {
  async search(keyword, options = {}) {
    return request('/api/v1/trending/search', {
      method: 'POST',
      body: JSON.stringify({
        keyword,
        platforms: options.platforms || ['baidu', 'weibo', 'zhihu', 'douyin', 'xiaohongshu'],
        days: options.days || 7,
      }),
    }).then(result => result.data)
  },

  async export(keyword, format = 'csv') {
    return downloadFile(
      `/api/v1/trending/export?keyword=${encodeURIComponent(keyword)}&format=${format}`,
      `hot-topics-${keyword}.${format}`
    )
  },
}
