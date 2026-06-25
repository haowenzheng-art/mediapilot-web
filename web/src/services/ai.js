/**
 * AI 服务（聊天、流式、脚本生成）
 */
import { API_BASE_URL, request } from './api'

export const aiService = {
  async chat(messages, options = {}) {
    return request('/api/ai/chat', {
      method: 'POST',
      body: JSON.stringify({
        messages,
        max_tokens: options.maxTokens || 1500,
        temperature: options.temperature || 0.6,
      }),
    }).then(result => result.content)
  },

  async *chatStream(messages, options = {}) {
    const response = await fetch(`${API_BASE_URL}/api/ai/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
      body: JSON.stringify({
        messages,
        max_tokens: options.maxTokens || 1500,
        temperature: options.temperature || 0.6,
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
          const data = line.slice(6)
          if (data === '[DONE]') continue
          try {
            const parsed = JSON.parse(data)
            const content = parsed.choices?.[0]?.delta?.content
            if (content) yield content
          } catch (e) {}
        }
      }
    }
  },

  async generateScript(topic, options = {}) {
    return request('/api/v1/content/generate', {
      method: 'POST',
      body: JSON.stringify({
        topic,
        max_tokens: options.maxTokens || 1500,
        temperature: options.temperature || 0.6,
      }),
    }).then(result => result.content)
  },
}
