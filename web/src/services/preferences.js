/**
 * Preferences API - 用户偏好（主题/语言/通知）
 * 与后端 /api/v1/user/preferences 同步，并镜像到 localStorage 以便首屏快速渲染
 */
import { request } from './api'

const LS_KEY = 'mediapilot:preferences'

export const DEFAULT_PREFERENCES = {
  theme: 'dark',
  language: 'zh-CN',
  notifications: true,
  auto_save: true,
  default_platform: 'douyin',
}

/** 读取本地缓存（首屏用，不需要等网络） */
export function getLocalPreferences() {
  try {
    const cached = localStorage.getItem(LS_KEY)
    if (cached) {
      return { ...DEFAULT_PREFERENCES, ...JSON.parse(cached) }
    }
  } catch {
    /* ignore */
  }
  return { ...DEFAULT_PREFERENCES }
}

function persistLocal(prefs) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(prefs))
  } catch {
    /* ignore quota errors */
  }
}

/** 从后端拉取（覆盖本地缓存） */
export async function fetchPreferences() {
  const res = await request('/api/v1/user/preferences')
  const prefs = res?.data?.preferences || DEFAULT_PREFERENCES
  persistLocal(prefs)
  return prefs
}

/** 部分更新，未传字段保持原值 */
export async function updatePreferences(patch) {
  const res = await request('/api/v1/user/preferences', {
    method: 'PUT',
    body: JSON.stringify(patch),
  })
  const prefs = res?.data?.preferences || DEFAULT_PREFERENCES
  persistLocal(prefs)
  return prefs
}

/** 重置为后端默认值 */
export async function resetPreferences() {
  const res = await request('/api/v1/user/preferences/reset', { method: 'POST' })
  const prefs = res?.data?.preferences || DEFAULT_PREFERENCES
  persistLocal(prefs)
  return prefs
}
