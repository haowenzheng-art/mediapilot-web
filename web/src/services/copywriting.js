/**
 * 口播文案服务
 *
 * 后端 success_response 返回 { success, data, message, timestamp }，
 * hook 层依赖 data.success 判断，所以这里直接透传整包，不在 service 里解包。
 */
import { request } from './api'

export const copywritingService = {
  /**
   * 获取用户的人设列表（最近3条）
   */
  async getPersonas() {
    return request('/api/v1/copywriting/personas')
  },

  /**
   * 创建人设
   */
  async createPersona(personaDescription) {
    return request('/api/v1/copywriting/personas', {
      method: 'POST',
      body: JSON.stringify({
        persona_description: personaDescription,
      }),
    })
  },

  /**
   * 删除人设
   */
  async deletePersona(personaId) {
    return request(`/api/v1/copywriting/personas/${personaId}`, {
      method: 'DELETE',
    })
  },

  /**
   * 生成口播文案
   *
   * @param {'from_zero'|'hotspot'|'rewrite'} mode
   * @param {string} persona
   * @param {object} params - mode 决定字段：topic / hotspot_content / original_text
   */
  async generate(mode, persona, params = {}) {
    return request('/api/v1/copywriting/generate', {
      method: 'POST',
      body: JSON.stringify({
        mode,
        persona,
        ...params,
      }),
    })
  },

  /**
   * 改写文案（再改改）
   *
   * @param {number|string} copywritingId
   * @param {'more_colloquial'|'add_emotion'|'add_opinion'} direction
   */
  async rewrite(copywritingId, direction) {
    return request('/api/v1/copywriting/rewrite', {
      method: 'POST',
      body: JSON.stringify({
        copywriting_id: copywritingId,
        direction,
      }),
    })
  },

  /**
   * 获取AI文案参考内容
   */
  async getReferenceContent(keyword, platforms = 'weibo,baidu,zhihu') {
    const qs = `keyword=${encodeURIComponent(keyword)}&platforms=${encodeURIComponent(platforms)}`
    return request(`/api/v1/copywriting/reference?${qs}`)
  },
}
