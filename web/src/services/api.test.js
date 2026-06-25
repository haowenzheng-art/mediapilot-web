/**
 * api.js 单元测试
 * 覆盖：request() 的 401 自动刷新重试逻辑、AI 配置
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { request, API_BASE_URL, isAIEnabled, setAIEnabled } from './api'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock auth module
vi.mock('./auth', () => ({
  getToken: vi.fn(() => 'test-access-token'),
  refreshToken: vi.fn(() => Promise.resolve({ token: 'new-access-token', refreshToken: 'new-rt' })),
  logout: vi.fn(),
}))

import { getToken, refreshToken, logout } from './auth'

// Mock window.location
const originalLocation = window.location
delete window.location
window.location = { href: '' }

function mockResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  window.location.href = ''
  delete window.__AI_ENABLED_OVERRIDE__
})


describe('request', () => {
  it('sends Authorization header when token exists', async () => {
    getToken.mockReturnValue('my-token')
    mockFetch.mockResolvedValueOnce(mockResponse(200, { success: true, data: {} }))

    await request('/api/v1/test')
    expect(mockFetch).toHaveBeenCalledTimes(1)
    const callOpts = mockFetch.mock.calls[0][1]
    expect(callOpts.headers.Authorization).toBe('Bearer my-token')
  })

  it('parses successful response', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse(200, { success: true, data: { key: 'val' } }))

    const result = await request('/api/v1/test')
    expect(result.data.key).toBe('val')
  })

  it('throws on non-401 error', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse(400, {
      success: false,
      error: { message: 'Bad request' },
    }))

    await expect(request('/api/v1/test')).rejects.toThrow('Bad request')
  })

  it('auto-refreshes on 401 and retries', async () => {
    getToken.mockReturnValue('expired-token')

    // First call returns 401
    mockFetch.mockResolvedValueOnce(mockResponse(401, {
      success: false,
      error: { code: 'invalid_token', message: 'expired' },
    }))

    // Refresh succeeds
    refreshToken.mockResolvedValueOnce({ token: 'new-token', refreshToken: 'new-rt' })

    // Retry succeeds
    mockFetch.mockResolvedValueOnce(mockResponse(200, { success: true, data: { ok: true } }))

    const result = await request('/api/v1/test')
    expect(result.data.ok).toBe(true)
    expect(refreshToken).toHaveBeenCalledTimes(1)
    expect(mockFetch).toHaveBeenCalledTimes(2)
  })

  it('logs out and redirects when refresh fails', async () => {
    getToken.mockReturnValue('expired-token')

    // First call returns 401
    mockFetch.mockResolvedValueOnce(mockResponse(401, {
      success: false,
      error: { code: 'invalid_token', message: 'expired' },
    }))

    // Refresh fails
    refreshToken.mockResolvedValueOnce(null)

    await expect(request('/api/v1/test')).rejects.toThrow('登录已过期')
    expect(logout).toHaveBeenCalled()
  })
})


describe('AI config', () => {
  it('isAIEnabled returns a boolean', () => {
    expect(typeof isAIEnabled()).toBe('boolean')
  })

  it('setAIEnabled overrides the value', () => {
    setAIEnabled(false)
    expect(isAIEnabled()).toBe(false)
    setAIEnabled(true)
    expect(isAIEnabled()).toBe(true)
    delete window.__AI_ENABLED_OVERRIDE__
  })
})
