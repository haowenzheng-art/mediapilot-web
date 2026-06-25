/**
 * 拍摄脚本服务
 *
 * 用 request() 统一加 Authorization header，避免后端 401 静默失败。
 */
import { request, downloadFile, API_BASE_URL } from './api'
import { getToken } from './auth'

export const shootScriptService = {
  /**
   * 生成拍摄脚本
   */
  async generate(topic, platform, style, persona, duration_seconds) {
    const body = { topic, platform, style, persona }
    if (duration_seconds) body.duration_seconds = duration_seconds
    return request('/api/v1/shoot-script/generate', {
      method: 'POST',
      body: JSON.stringify(body),
    })
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
