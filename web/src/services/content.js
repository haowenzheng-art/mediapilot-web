/**
 * 内容生成服务（流式 + 非流式）
 */
import { request } from './api'

// 非流式：生成内容（兼容旧 contentService.generate 接口）
export const contentService = {
  async generate(options) {
    return request('/api/v1/content/generate', {
      method: 'POST',
      body: JSON.stringify({
        topic: options.topic,
        platform: options.platform || 'douyin',
        duration: options.duration || 60,
        style: options.style || 'professional',
      }),
    }).then(result => result.data)
  },
}

/**
 * 改写逐字稿（非流式）
 */
export async function rewriteTranscript(data) {
  return request('/api/v1/content/rewrite', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}
