/**
 * 媒体转写服务
 * 对接后端 /api/v1/media/upload + /api/v1/media/task/{task_id}
 */
import { API_BASE_URL, request } from './api'
import { getToken, refreshToken, logout } from './auth'

/**
 * 上传音视频文件，启动转写任务
 * 返回 { task_id, status }
 */
export async function uploadMedia(file) {
  const formData = new FormData()
  formData.append('file', file)

  const token = getToken()
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  // 不要手动设置 Content-Type，让浏览器自动加 multipart boundary

  const doFetch = (authHeader) =>
    fetch(`${API_BASE_URL}/api/v1/media/upload`, {
      method: 'POST',
      headers: authHeader ? { Authorization: authHeader } : {},
      body: formData,
    })

  let response = await doFetch(token ? `Bearer ${token}` : null)

  // 401 → 刷新 token 后重试一次
  if (response.status === 401) {
    const refreshed = await refreshToken()
    if (refreshed) {
      response = await doFetch(`Bearer ${refreshed.token}`)
    } else {
      logout()
      window.location.href = '/login'
      throw new Error('登录已过期，请重新登录')
    }
  }

  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body?.error?.message || body?.detail?.message || `上传失败: ${response.status}`)
  }
  return body.data
}

/**
 * 查询转写任务状态
 * 返回 MediaTranscribeResponse: { task_id, status, transcript, outline, timestamps, error }
 */
export async function getMediaTask(taskId) {
  const body = await request(`/api/v1/media/task/${taskId}`)
  return body.data
}

/**
 * 轮询任务直到 completed/failed 或超过最大尝试次数
 * onProgress(status, data) 在每次轮询时被调用
 */
export async function pollMediaTask(taskId, { onProgress, intervalMs = 1500, maxAttempts = 200 } = {}) {
  for (let i = 0; i < maxAttempts; i++) {
    const data = await getMediaTask(taskId)
    if (onProgress) onProgress(data, i)
    if (data.status === 'completed') return data
    if (data.status === 'failed') {
      throw new Error(data.error || '转写失败')
    }
    await new Promise((r) => setTimeout(r, intervalMs))
  }
  throw new Error('转写超时，请稍后重试')
}

export const mediaService = {
  uploadMedia,
  getMediaTask,
  pollMediaTask,
}
