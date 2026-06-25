// MediaPilot 认证服务
// 调用后端 API 进行认证

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const AUTH_BASE = `${API_BASE_URL}/api/v1/auth`

// 检查登录状态
export const getCurrentUser = () => {
  const saved = localStorage.getItem('mediapilot-user')
  if (saved) {
    try {
      return JSON.parse(saved)
    } catch (e) {
      return null
    }
  }
  return null
}

// 获取用户 token
export const getToken = () => {
  const user = getCurrentUser()
  return user ? user.token : null
}

// 获取 refresh token
export const getRefreshToken = () => {
  const user = getCurrentUser()
  return user ? user.refreshToken : null
}

// 保存用户信息到 localStorage
function saveUser(userData) {
  localStorage.setItem('mediapilot-user', JSON.stringify(userData))
}

// 解析后端统一响应格式
function parseAuthResponse(data) {
  return {
    id: data.user.id,
    username: data.user.username,
    email: data.user.email,
    quota_balance: data.user.quota_balance,
    isAdmin: false,
    token: data.token,
    refreshToken: data.refresh_token,
  }
}

// 注册
export const register = async (username, password, email) => {
  try {
    const response = await fetch(`${AUTH_BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, email })
    })

    const result = await response.json()

    if (response.ok && result.success) {
      const userData = parseAuthResponse(result.data)
      saveUser(userData)
      return { success: true, user: userData }
    } else {
      const errorMsg = result.error?.message || result.message || '注册失败'
      return { success: false, error: errorMsg }
    }
  } catch (error) {
    return { success: false, error: `网络错误: ${error.message}` }
  }
}

// 登录
export const login = async (username, password) => {
  try {
    const response = await fetch(`${AUTH_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })

    const result = await response.json()

    if (response.ok && result.success) {
      const userData = parseAuthResponse(result.data)
      saveUser(userData)
      return { success: true, user: userData }
    } else {
      const errorMsg = result.error?.message || result.message || '用户名或密码错误'
      return { success: false, error: errorMsg }
    }
  } catch (error) {
    return { success: false, error: `网络错误: ${error.message}` }
  }
}

// 刷新 token
let refreshPromise = null

export const refreshToken = async () => {
  // 防止并发刷新
  if (refreshPromise) return refreshPromise

  const rt = getRefreshToken()
  if (!rt) {
    logout()
    return null
  }

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${AUTH_BASE}/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt })
      })

      const result = await response.json()

      if (response.ok && result.success) {
        const user = getCurrentUser()
        if (user) {
          user.token = result.data.token
          user.refreshToken = result.data.refresh_token
          saveUser(user)
        }
        return user
      } else {
        logout()
        return null
      }
    } catch (error) {
      logout()
      return null
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

// 登出
export const logout = () => {
  localStorage.removeItem('mediapilot-user')
}

// 判断当前用户是否是管理员
export const isAdmin = () => {
  const user = getCurrentUser()
  return user && user.isAdmin === true
}

// 判断是否已登录
export const isLoggedIn = () => {
  return getCurrentUser() !== null
}
