import { useState } from 'react'
import { login } from '../services/auth'

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    const result = login(username, password)
    if (result.success) {
      onLogin(result.user)
    } else {
      setError(result.error)
    }
  }

  return (
    <div className="login-page" style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-gradient)',
      padding: '20px'
    }}>
      <div className="card" style={{
        width: '100%',
        maxWidth: '400px',
        padding: '40px'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <span style={{ fontSize: '3rem' }}>🚀</span>
          <h1 style={{
            fontSize: '1.5rem',
            marginTop: '10px',
            color: 'var(--text-primary)'
          }}>
            MediaPilot
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '5px' }}>
            登录以继续
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              color: 'var(--text-primary)'
            }}>
              用户名
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="请输入用户名"
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-primary)',
                color: 'var(--text-primary)',
                fontSize: '1rem'
              }}
              required
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              color: 'var(--text-primary)'
            }}>
              密码
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-primary)',
                color: 'var(--text-primary)',
                fontSize: '1rem'
              }}
              required
            />
          </div>

          {error && (
            <div style={{
              padding: '10px',
              borderRadius: '8px',
              background: 'rgba(255, 0, 0, 0.1)',
              border: '1px solid rgba(255, 0, 0, 0.3)',
              color: '#ff6b6b',
              marginBottom: '20px',
              textAlign: 'center'
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            style={{
              width: '100%',
              padding: '14px',
              fontSize: '1rem'
            }}
          >
            登录
          </button>
        </form>

        <div style={{
          marginTop: '30px',
          padding: '15px',
          borderRadius: '8px',
          background: 'var(--glass-bg)',
          fontSize: '0.85rem',
          color: 'var(--text-secondary)'
        }}>
          <p style={{ marginBottom: '8px' }}>📋 测试账号：</p>
          <p>管理员：admin / media2024</p>
          <p>访客：friend1 / friend123</p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage