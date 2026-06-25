/**
 * 应用头部组件
 *
 * 显示 Logo、用户信息、登录/登出按钮
 */

export default function Header({ currentUser, onLoginClick, onLogout, onLogoClick }) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="logo" onClick={onLogoClick}>
          <span style={{ fontSize: '24px' }}>🚀</span>
          <h1 style={{
            fontSize: '18px',
            fontWeight: '600',
            letterSpacing: '-0.02em',
          }}>
            MediaPilot
          </h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {currentUser ? (
            <>
              <span style={{
                fontSize: '13px',
                color: 'var(--text-secondary)',
              }}>
                {currentUser.username || currentUser.name}
              </span>
              <button
                onClick={onLogout}
                className="btn btn-ghost"
                style={{ padding: '6px 12px', fontSize: '13px' }}
              >
                登出
              </button>
            </>
          ) : (
            <button
              onClick={onLoginClick}
              className="btn btn-primary"
              style={{ padding: '6px 16px', fontSize: '13px' }}
            >
              登录
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
