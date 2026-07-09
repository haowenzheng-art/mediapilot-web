/**
 * 视频剪辑服务（AI 自动去除磕巴片段）
 * 对接后端 /api/v1/media/video-edit/*
 */
import { API_BASE_URL, request, downloadFile } from './api'
import { getToken, refreshToken, logout } from './auth'

/**
 * 上传视频，启动 AI 剪辑任务
 * @param {File} file - 视频文件
 * @param {object} options - { strength: 'conservative'|'medium'|'aggressive', config?: {...} }
 * 返回 { task_id, status }
 */
export async function uploadVideoEdit(file, { strength = 'medium', config = null } = {}) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('strength', strength)
  if (config) {
    formData.append('config', JSON.stringify(config))
  }

  const token = getToken()
  const doFetch = (authHeader) =>
    fetch(`${API_BASE_URL}/api/v1/media/video-edit/upload`, {
      method: 'POST',
      headers: authHeader ? { Authorization: authHeader } : {},
      body: formData,
    })

  let response = await doFetch(token ? `Bearer ${token}` : null)

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
 * 查询视频剪辑任务状态
 * 返回 VideoEditResponse: { task_id, status, transcript, kept_segments, removed_segments, ... }
 */
export async function getVideoEditTask(taskId) {
  const body = await request(`/api/v1/media/video-edit/task/${taskId}`)
  return body.data
}

/**
 * 列出当前用户的视频剪辑历史任务（B1）
 * @param {number} skip
 * @param {number} limit
 * @returns {Promise<{tasks: Array, total: number, skip: number, limit: number}>}
 */
export async function listVideoEditTasks(skip = 0, limit = 20) {
  const qs = `skip=${skip}&limit=${limit}`
  const body = await request(`/api/v1/media/video-edit/tasks?${qs}`)
  return body.data
}

/**
 * B3: 用户微调 kept_segments 后重新生成视频/字幕/预览
 * @param {string} taskId
 * @param {Array<[number, number]>} keptSegments - [[start, end], ...]
 * @returns {Promise<{task_id, kept_segments, removed_segments, final_duration, status}>}
 */
export async function reapplyVideoEdit(taskId, keptSegments) {
  const body = await request(`/api/v1/media/video-edit/${taskId}/reapply`, {
    method: 'POST',
    body: { kept_segments: keptSegments },
  })
  return body.data
}

/**
 * 获取剪辑片段详情
 */
export async function getVideoEditSegments(taskId) {
  const body = await request(`/api/v1/media/video-edit/${taskId}/segments`)
  return body.data
}

/**
 * 轮询任务直到完成/失败
 */
export async function pollVideoEditTask(taskId, { onProgress, intervalMs = 2000, maxAttempts = 300 } = {}) {
  for (let i = 0; i < maxAttempts; i++) {
    const data = await getVideoEditTask(taskId)
    if (onProgress) onProgress(data, i)
    if (data.status === 'completed') return data
    if (data.status === 'failed') {
      throw new Error(data.error || '视频剪辑失败')
    }
    await new Promise((r) => setTimeout(r, intervalMs))
  }
  throw new Error('处理超时，请稍后重试')
}

/**
 * 下载剪辑后的视频或字幕文件
 */
export async function downloadVideoEditFile(taskId, fileType, filename) {
  await downloadFile(
    `/api/v1/media/video-edit/${taskId}/download/${fileType}`,
    filename
  )
}

export const videoEditService = {
  uploadVideoEdit,
  getVideoEditTask,
  getVideoEditSegments,
  pollVideoEditTask,
  downloadVideoEditFile,
  listVideoEditTasks,
  reapplyVideoEdit,
}
