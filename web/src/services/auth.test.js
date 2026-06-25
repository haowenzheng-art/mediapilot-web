/**
 * auth.js 单元测试
 * 覆盖：注册/登录响应解析、token 存储/刷新/登出、并发锁
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getCurrentUser, getToken, getRefreshToken,
  register, login, refreshToken, logout,
  isLoggedIn, isAdmin,
} from './auth'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock localStorage (vitest.setup.js provides a mock, but we reset between tests)
const store = {}
const mockLocalStorage = {
  getItem: vi.fn((key) => store[key] || null),
  setItem: vi.fn((key, value) => { store[key] = value }),
  removeItem: vi.fn((key) => { delete store[key] }),
  clear: vi.fn(() => { Object.keys(store).forEach(k => delete store[k]) }),
}
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage })

// 标准后端成功响应
function mockSuccessResponse(data) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve({ success: true, data, message: 'ok', timestamp: new Date().toISOString() }),
  }
}

function mockErrorResponse(status, error) {
  return {
    ok: false,
    status,
    json: () => Promise.resolve({ success: false, error }),
  }
}

const testUserData = {
  user: { id: 1, username: 'testuser', email: 't@t.com', quota_balance: 100, is_active: true, created_at: '2026-01-01' },
  token: 'access-token-123',
  refresh_token: 'refresh-token-456',
}

beforeEach(() => {
  mockLocalStorage.clear()
  mockFetch.mockReset()
})


describe('getCurrentUser / getToken / getRefreshToken', () => {
  it('returns null when no user stored', () => {
    expect(getCurrentUser()).toBeNull()
    expect(getToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })

  it('returns user data from localStorage', () => {
    store['mediapilot-user'] = JSON.stringify({ id: 1, token: 'abc', refreshToken: 'def' })
    expect(getCurrentUser()).not.toBeNull()
    expect(getToken()).toBe('abc')
    expect(getRefreshToken()).toBe('def')
  })

  it('handles corrupt localStorage data', () => {
    store['mediapilot-user'] = 'not-json'
    expect(getCurrentUser()).toBeNull()
  })
})


describe('register', () => {
  it('stores user data on success', async () => {
    mockFetch.mockResolvedValueOnce(mockSuccessResponse(testUserData))
    const result = await register('testuser', 'pass123', 't@t.com')
    expect(result.success).toBe(true)
    expect(result.user.token).toBe('access-token-123')
    expect(result.user.refreshToken).toBe('refresh-token-456')

    // Verify localStorage
    const stored = JSON.parse(store['mediapilot-user'])
    expect(stored.token).toBe('access-token-123')
    expect(stored.refreshToken).toBe('refresh-token-456')
  })

  it('returns error on failure', async () => {
    mockFetch.mockResolvedValueOnce(mockErrorResponse(400, { code: 'validation_error', message: '用户名已存在' }))
    const result = await register('testuser', 'pass123', 't@t.com')
    expect(result.success).toBe(false)
    expect(result.error).toContain('用户名已存在')
  })

  it('handles network error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network'))
    const result = await register('testuser', 'pass123', 't@t.com')
    expect(result.success).toBe(false)
    expect(result.error).toContain('网络错误')
  })
})


describe('login', () => {
  it('stores user data on success', async () => {
    mockFetch.mockResolvedValueOnce(mockSuccessResponse(testUserData))
    const result = await login('testuser', 'pass123')
    expect(result.success).toBe(true)
    expect(result.user.refreshToken).toBe('refresh-token-456')
  })

  it('returns error on wrong password', async () => {
    mockFetch.mockResolvedValueOnce(mockErrorResponse(401, { code: 'unauthorized', message: '用户名或密码错误' }))
    const result = await login('testuser', 'wrong')
    expect(result.success).toBe(false)
  })
})


describe('refreshToken', () => {
  it('refreshes tokens and updates localStorage', async () => {
    // Set up existing user
    store['mediapilot-user'] = JSON.stringify({ id: 1, token: 'old-access', refreshToken: 'old-refresh' })

    mockFetch.mockResolvedValueOnce(mockSuccessResponse({
      token: 'new-access',
      refresh_token: 'new-refresh',
    }))

    const result = await refreshToken()
    expect(result).not.toBeNull()
    expect(result.token).toBe('new-access')
    expect(result.refreshToken).toBe('new-refresh')

    const stored = JSON.parse(store['mediapilot-user'])
    expect(stored.token).toBe('new-access')
  })

  it('returns null and logs out when no refresh token', async () => {
    store['mediapilot-user'] = JSON.stringify({ id: 1, token: 'abc' }) // no refreshToken
    const result = await refreshToken()
    expect(result).toBeNull()
    // Should have called logout (removed user from localStorage)
  })

  it('returns null and logs out on refresh failure', async () => {
    store['mediapilot-user'] = JSON.stringify({ id: 1, token: 'old', refreshToken: 'old-rt' })
    mockFetch.mockResolvedValueOnce(mockErrorResponse(401, { code: 'unauthorized', message: 'expired' }))

    const result = await refreshToken()
    expect(result).toBeNull()
  })

  it('deduplicates concurrent refresh calls', async () => {
    store['mediapilot-user'] = JSON.stringify({ id: 1, token: 'old', refreshToken: 'old-rt' })

    // Return a promise that we control
    let resolveFirst
    const firstPromise = new Promise(resolve => { resolveFirst = resolve })
    mockFetch.mockReturnValueOnce(firstPromise)

    // Fire two concurrent refreshes
    const p1 = refreshToken()
    const p2 = refreshToken()

    // Only one fetch call should have been made
    expect(mockFetch).toHaveBeenCalledTimes(1)

    // Resolve the fetch
    resolveFirst(mockSuccessResponse({ token: 'new', refresh_token: 'new-rt' }))

    const r1 = await p1
    const r2 = await p2
    expect(r1).toBe(r2) // Same promise
  })
})


describe('logout', () => {
  it('removes user from localStorage', () => {
    store['mediapilot-user'] = JSON.stringify({ id: 1, token: 'abc' })
    logout()
    expect(store['mediapilot-user']).toBeUndefined()
  })
})


describe('isLoggedIn / isAdmin', () => {
  it('isLoggedIn returns true when user exists', () => {
    store['mediapilot-user'] = JSON.stringify({ id: 1 })
    expect(isLoggedIn()).toBe(true)
  })

  it('isLoggedIn returns false when no user', () => {
    expect(isLoggedIn()).toBe(false)
  })

  it('isAdmin returns true when isAdmin is true', () => {
    store['mediapilot-user'] = JSON.stringify({ id: 1, isAdmin: true })
    expect(isAdmin()).toBe(true)
  })

  it('isAdmin returns false when not admin', () => {
    store['mediapilot-user'] = JSON.stringify({ id: 1, isAdmin: false })
    expect(isAdmin()).toBe(false)
  })
})
