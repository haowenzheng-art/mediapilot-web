// 简单的登录认证系统
// 这是一个前端演示版本，真实生产环境需要后端验证

// 用户数据（用户名 -> 密码和权限）
// 你可以在这里添加更多账号给朋友
const USERS = {
  'admin': {
    password: 'media2024',
    role: 'admin',  // admin = 超级管理员，可以调用 AI
    name: '管理员'
  },
  'friend1': {
    password: 'friend123',
    role: 'user',   // user = 普通用户，不能调用 AI
    name: '朋友A'
  }
}

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

// 登录
export const login = (username, password) => {
  const user = USERS[username]
  if (user && user.password === password) {
    const userData = {
      username,
      name: user.name,
      role: user.role,
      isAdmin: user.role === 'admin'
    }
    localStorage.setItem('mediapilot-user', JSON.stringify(userData))
    return { success: true, user: userData }
  }
  return { success: false, error: '用户名或密码错误' }
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