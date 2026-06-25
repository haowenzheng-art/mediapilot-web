/**
 * Hero 页面头部组件
 *
 * 显示 Logo、登录/注册按钮
 */
export default function HeroHeader({ currentUser, onLoginClick }) {
  return (
    <div
      className="hero-theme-switcher"
      style={{ display: 'flex', alignItems: 'center', gap: '12px' }}
    >
      {!currentUser && (
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={onLoginClick}
            style={{
              padding: '8px 20px',
              background: 'transparent',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: '500',
            }}
          >
            Sign In
          </button>
          <button
            onClick={onLoginClick}
            style={{
              padding: '8px 20px',
              background: 'var(--primary)',
              border: 'none',
              borderRadius: '6px',
              color: 'var(--bg-primary)',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: '600',
            }}
          >
            Sign Up
          </button>
        </div>
      )}
    </div>
  )
}
