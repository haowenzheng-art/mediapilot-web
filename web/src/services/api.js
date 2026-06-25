/**
 * API 通用基础模块
 * 提供 API_BASE_URL、配置管理、通用 request 封装
 */

import { getToken, refreshToken, logout } from './auth'

const isDev = import.meta.env.DEV
const AI_ENABLED = isDev || import.meta.env.VITE_AI_ENABLED === 'true'

const DEFAULT_CONFIG = {
  provider: 'openai',
  apiKey: import.meta.env.VITE_API_KEY || '',
  baseUrl: import.meta.env.VITE_BASE_URL || 'https://apihub.agnes-ai.com/v1',
  model: import.meta.env.VITE_MODEL || 'agnes-2.0-flash',
}

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// AI 开关
export const isAIEnabled = () => {
  if (typeof window.__AI_ENABLED_OVERRIDE__ !== 'undefined') {
    return window.__AI_ENABLED_OVERRIDE__
  }
  return AI_ENABLED
}

export const setAIEnabled = (enabled) => {
  window.__AI_ENABLED_OVERRIDE__ = enabled
}

// 配置管理
export const getConfig = () => {
  const saved = localStorage.getItem('mediapilot-api-config')
  if (saved) {
    try {
      return JSON.parse(saved)
    } catch (e) {
      return DEFAULT_CONFIG
    }
  }
  return DEFAULT_CONFIG
}

let currentConfig = getConfig()

export const saveConfig = (config) => {
  localStorage.setItem('mediapilot-api-config', JSON.stringify(config))
}

export const updateConfig = (newConfig) => {
  currentConfig = { ...currentConfig, ...newConfig }
  saveConfig(currentConfig)
}

export { currentConfig }

/**
 * 通用 request 封装
 * 统一处理认证 token、401 自动刷新、错误解析
 */
export async function request(path, options = {}) {
  const token = getToken()

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  // 401 → 尝试刷新 token 后重试一次
  if (response.status === 401) {
    const refreshed = await refreshToken()
    if (refreshed) {
      const retryHeaders = {
        ...headers,
        Authorization: `Bearer ${refreshed.token}`,
      }
      const retryResponse = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers: retryHeaders,
      })
      if (!retryResponse.ok) {
        const error = await retryResponse.json().catch(() => ({}))
        throw new Error(error.error?.message || error.detail?.message || error.message || `请求失败: ${retryResponse.status}`)
      }
      return retryResponse.json()
    }

    // 刷新失败，跳转登录
    logout()
    window.location.href = '/login'
    throw new Error('登录已过期，请重新登录')
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.error?.message || error.detail?.message || error.message || `请求失败: ${response.status}`)
  }

  return response.json()
}

/**
 * 通用文件下载封装
 */
export async function downloadFile(path, filename, options = {}) {
  const token = getToken()

  const headers = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })

  if (!response.ok) {
    throw new Error('导出失败')
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}
