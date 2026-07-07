/**
 * 口播文案服务
 *
 * 后端 success_response 返回 { success, data, message, timestamp }，
 * hook 层依赖 data.success 判断，所以这里直接透传整包，不在 service 里解包。
 */
import { request, API_BASE_URL } from './api'

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
   * 生成口播文案（阻塞）
   *
   * @param {'from_zero'|'hotspot'|'rewrite'} mode
   * @param {string} persona
   * @param {object} params - mode 决定字段：topic / hotspot_content / original_text
   * @param {object} options - { enableReasoning }
   */
  async generate(mode, persona, params = {}, options = {}) {
    return request('/api/v1/copywriting/generate', {
      method: 'POST',
      body: JSON.stringify({
        mode,
        persona,
        enable_reasoning: options.enableReasoning ?? true,
        ...params,
      }),
    })
  },

  /**
   * 流式生成口播文案（SSE）
   *
   * 后端 POST /api/v1/copywriting/generate/stream
   * 事件格式（OpenAI 兼容 + reasoning_content + meta.parsed）：
   *   {choices:[{delta:{content|reasoning_content}}]}
   *   {choices:[{delta:{}}], meta:{final, reasoning_supported, parsed}}
   *   {error: '...'}
   *   [DONE]
   *
   * 转换为内部事件对象 yield：
   *   {type:'content', delta}
   *   {type:'reasoning', delta}
   *   {type:'meta', meta}
   *   {type:'error', delta}
   *
   * @param {'from_zero'|'hotspot'|'rewrite'} mode
   * @param {string} persona
   * @param {object} params - mode 决定字段：topic / hotspot_content / original_text
   * @param {object} options - { enableReasoning }
   */
  async *generateStream(mode, persona, params = {}, options = {}) {
    const response = await fetch(`${API_BASE_URL}/api/v1/copywriting/generate/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
      credentials: 'include',
      body: JSON.stringify({
        mode,
        persona,
        enable_reasoning: options.enableReasoning ?? true,
        ...params,
      }),
    })

    if (!response.ok) {
      throw new Error(`API请求失败: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          if (!data || data === '[DONE]') continue
          try {
            const parsed = JSON.parse(data)
            if (parsed.error) {
              yield { type: 'error', delta: parsed.error }
              continue
            }
            const choice = parsed.choices?.[0]
            if (!choice) continue
            const delta = choice.delta || {}
            if (delta.content) {
              yield { type: 'content', delta: delta.content }
            }
            if (delta.reasoning_content) {
              yield { type: 'reasoning', delta: delta.reasoning_content }
            }
            if (parsed.meta) {
              yield { type: 'meta', meta: parsed.meta }
            }
          } catch (e) {
            // 忽略 JSON 解析错误（SSE 行可能不完整）
          }
        }
      }
    }
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
