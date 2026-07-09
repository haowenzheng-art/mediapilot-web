/**
 * 拍摄脚本服务
 *
 * 用 request() 统一加 Authorization header，避免后端 401 静默失败。
 */
import { request, downloadFile, API_BASE_URL } from './api'
import { getToken } from './auth'

export const shootScriptService = {
  /**
   * 生成拍摄脚本（阻塞）
   */
  async generate(topic, platform, style, persona, duration_seconds, options = {}) {
    const body = { topic, platform, style, persona, enable_reasoning: true }
    if (duration_seconds) body.duration_seconds = duration_seconds
    // C1: 携带热点关联（让内容库反查可拿到 hot_topic_id）
    if (options.hotTopic) {
      body.hot_topic_id = options.hotTopic.id
      body.hot_topic_title = options.hotTopic.title
      body.hot_topic_source = options.hotTopic.source
    }
    return request('/api/v1/shoot-script/generate', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  /**
   * 流式生成拍摄脚本（SSE）
   *
   * 后端 POST /api/v1/shoot-script/generate/stream
   * 事件格式与 copywriting/stream 一致（OpenAI 兼容 + reasoning_content + meta.parsed）
   *
   * @param {string} topic
   * @param {string} platform
   * @param {string} style
   * @param {string} persona
   * @param {number|null} duration_seconds
   * @param {object} options - { enableReasoning }
   */
  async *generateStream(topic, platform, style, persona, duration_seconds, options = {}) {
    const body = {
      topic,
      platform,
      style,
      persona,
      enable_reasoning: options.enableReasoning ?? true,
    }
    if (duration_seconds) body.duration_seconds = duration_seconds
    // C1: 携带热点关联（让内容库反查可拿到 hot_topic_id）
    if (options.hotTopic) {
      body.hot_topic_id = options.hotTopic.id
      body.hot_topic_title = options.hotTopic.title
      body.hot_topic_source = options.hotTopic.source
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/shoot-script/generate/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
      credentials: 'include',
      body: JSON.stringify(body),
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
   * 获取拍摄脚本
   */
  async get(scriptId) {
    return request(`/api/v1/shoot-script/${scriptId}`)
  },

  /**
   * 导出脚本（二进制下载，绕过 request 的 JSON 解析）
   */
  async export(scriptId, format) {
    const token = getToken()
    const response = await fetch(`${API_BASE_URL}/api/v1/shoot-script/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ script_id: scriptId, format }),
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.error?.message || data.message || '导出失败')
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `shoot_script_${scriptId}.${format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },
}
