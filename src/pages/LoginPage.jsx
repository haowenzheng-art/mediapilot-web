import { useState } from 'react'
import { login, register } from '../services/auth'

function LoginPage({ onLogin, onClose }) {
  const [mode, setMode] = useState('login') // 'login' or 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (mode === 'register') {
      if (password !== confirmPassword) {
        setError('两次输入的密码不一致')
        return
      }
      if (password.length < 6) {
        setError('密码长度至少6位')
        return
      }
      const result = register(username, password)
      if (result.success) {
        setSuccess('注册成功！请登录')
        setMode('login')
        setPassword('')
        setConfirmPassword('')
      } else {
        setError(result.error)
      }
    } else {
      const result = login(username, password)
      if (result.success) {
        onLogin(result.user)
      } else {
        setError(result.error)
      }
    }
  }

  const isModal = !!onClose

  return (
    <div className="login-page" style={{
      minHeight: isModal ? 'auto' : '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: isModal ? 'transparent' : 'var(--bg-gradient)',
      padding: '20px'
    }}>
      <div className="card" style={{
        width: '100%',
        maxWidth: '400px',
        padding: '40px'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '30px', position: 'relative' }}>
          {isModal && onClose && (
            <button
              onClick={onClose}
              style={{
                position: 'absolute',
                right: '-10px',
                top: '-10px',
                background: 'none',
                border: 'none',
                fontSize: '1.5rem',
                cursor: 'pointer',
                color: 'var(--text-secondary)'
              }}
            >
              ×
            </button>
          )}
          <span style={{ fontSize: '3rem' }}>🚀</span>
          <h1 style={{
            fontSize: '1.5rem',
            marginTop: '10px',
            color: 'var(--text-primary)'
          }}>
            MediaPilot
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '5px' }}>
            {mode === 'login' ? 'Sign In to continue' : 'Create your account'}
          </p>
        </div>

        {/* Sign In / Sign Up 切换 */}
        <div style={{
          display: 'flex',
          marginBottom: '24px',
          borderRadius: '8px',
          background: 'var(--bg-primary)',
          padding: '4px'
        }}>
          <button
            onClick={() => { setMode('login'); setError(''); setSuccess('') }}
            style={{
              flex: 1,
              padding: '10px',
              border: 'none',
              borderRadius: '6px',
              background: mode === 'login' ? 'var(--accent-primary)' : 'transparent',
              color: mode === 'login' ? 'var(--bg-primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '0.9rem'
            }}
          >
            Sign In
          </button>
          <button
            onClick={() => { setMode('register'); setError(''); setSuccess('') }}
            style={{
              flex: 1,
              padding: '10px',
              border: 'none',
              borderRadius: '6px',
              background: mode === 'register' ? 'var(--accent-primary)' : 'transparent',
              color: mode === 'register' ? 'var(--bg-primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '0.9rem'
            }}
          >
            Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              color: 'var(--text-primary)'
            }}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
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
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
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

          {mode === 'register' && (
            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                color: 'var(--text-primary)'
              }}>
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm password"
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
          )}

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

          {success && (
            <div style={{
              padding: '10px',
              borderRadius: '8px',
              background: 'rgba(0, 255, 0, 0.1)',
              border: '1px solid rgba(0, 255, 0, 0.3)',
              color: '#4ade80',
              marginBottom: '20px',
              textAlign: 'center'
            }}>
              {success}
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
            {mode === 'login' ? 'Sign In' : 'Sign Up'}
          </button>
        </form>

        {mode === 'login' && (
          <div style={{
            marginTop: '30px',
            padding: '15px',
            borderRadius: '8px',
            background: 'var(--glass-bg)',
            fontSize: '0.85rem',
            color: 'var(--text-secondary)'
          }}>
            <p style={{ marginBottom: '8px' }}>📋 Demo Accounts:</p>
            <p>Admin: admin / media2024 (AI enabled)</p>
            <p>Guest: friend1 / friend123</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default LoginPage