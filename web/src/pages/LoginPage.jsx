import { useState } from 'react'
import { login, register } from '../services/auth'

function LoginPage({ onLogin, onClose }) {
  const [mode, setMode] = useState('login') // 'login' or 'register'
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (mode === 'register') {
        if (password !== confirmPassword) {
          setError('两次输入的密码不一致')
          setLoading(false)
          return
        }
        if (password.length < 6) {
          setError('密码长度至少6位')
          setLoading(false)
          return
        }
        if (!email.includes('@')) {
          setError('请输入有效的邮箱地址')
          setLoading(false)
          return
        }
        const result = await register(username, password, email)
        if (result.success) {
          onLogin(result.user)
        } else {
          setError(result.error)
        }
      } else {
        const result = await login(username, password)
        if (result.success) {
          onLogin(result.user)
        } else {
          setError(result.error)
        }
      }
    } catch (err) {
      setError(`操作失败: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const isModal = !!onClose

  return (
    <div style={{
      minHeight: isModal ? 'auto' : '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: isModal ? 'transparent' : 'var(--bg-primary)',
      padding: '24px',
    }}>
      <div className="card" style={{
        width: '100%',
        maxWidth: '400px',
        padding: '40px',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <span style={{ fontSize: '48px', marginBottom: '16px', display: 'block' }}>🚀</span>
          <h1 style={{
            fontSize: '24px',
            fontWeight: '700',
            marginBottom: '8px',
          }}>
            MediaPilot
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
            {mode === 'login' ? '登录继续使用' : '创建新账户'}
          </p>
        </div>

        {/* 模式切换 */}
        <div style={{
          display: 'flex',
          gap: '4px',
          marginBottom: '24px',
          padding: '4px',
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-md)',
        }}>
          <button
            onClick={() => { setMode('login'); setError('') }}
            style={{
              flex: 1,
              padding: '8px',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              background: mode === 'login' ? 'var(--bg-primary)' : 'transparent',
              color: mode === 'login' ? 'var(--text-primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
            }}
          >
            登录
          </button>
          <button
            onClick={() => { setMode('register'); setError('') }}
            style={{
              flex: 1,
              padding: '8px',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              background: mode === 'register' ? 'var(--bg-primary)' : 'transparent',
              color: mode === 'register' ? 'var(--text-primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
            }}
          >
            注册
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* 用户名 */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '13px',
              fontWeight: '500',
              color: 'var(--text-primary)',
            }}>
              用户名
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="输入用户名"
              className="notion-input"
              required
              disabled={loading}
            />
          </div>

          {/* 邮箱（仅注册时显示） */}
          {mode === 'register' && (
            <div style={{ marginBottom: '16px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '13px',
                fontWeight: '500',
                color: 'var(--text-primary)',
              }}>
                邮箱
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="输入邮箱地址"
                className="notion-input"
                required
                disabled={loading}
              />
            </div>
          )}

          {/* 密码 */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '13px',
              fontWeight: '500',
              color: 'var(--text-primary)',
            }}>
              密码
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="输入密码"
              className="notion-input"
              required
              disabled={loading}
            />
          </div>

          {/* 确认密码（仅注册时显示） */}
          {mode === 'register' && (
            <div style={{ marginBottom: '16px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '13px',
                fontWeight: '500',
                color: 'var(--text-primary)',
              }}>
                确认密码
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="再次输入密码"
                className="notion-input"
                required
                disabled={loading}
              />
            </div>
          )}

          {/* 错误信息 */}
          {error && (
            <div className="alert alert-error" style={{ marginBottom: '16px', textAlign: 'center' }}>
              {error}
            </div>
          )}

          {/* 提交按钮 */}
          <button
            type="submit"
            className="btn btn-primary btn-full btn-lg"
            disabled={loading}
          >
            {loading ? '处理中...' : (mode === 'login' ? '登录' : '注册')}
          </button>
        </form>
      </div>
    </div>
  )
}

export default LoginPage
