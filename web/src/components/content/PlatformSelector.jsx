/**
 * 平台选择器组件
 */

function PlatformSelector({ platform, setPlatform, platforms, disabled = false }) {
  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{
        fontSize: '12px',
        color: 'var(--text-tertiary)',
        marginBottom: '12px'
      }}>
        目标平台
      </div>
      <div style={{
        display: 'flex',
        gap: '12px',
        flexWrap: 'wrap'
      }}>
        {platforms.map((p) => (
          <button
            key={p.id}
            onClick={() => setPlatform(p.id)}
            disabled={disabled}
            style={{
              padding: '16px 24px',
              fontSize: '14px',
              background: platform === p.id ? 'var(--accent-primary)' : 'var(--bg-secondary)',
              color: platform === p.id ? 'white' : 'var(--text-primary)',
              border: platform === p.id ? 'none' : '1px solid var(--border-color)',
              borderRadius: '10px',
              cursor: disabled ? 'not-allowed' : 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
              opacity: disabled ? 0.5 : 1,
              transition: 'all 0.2s'
            }}
          >
            <span style={{ fontSize: '28px' }}>{p.icon}</span>
            <span style={{
              fontSize: '16px',
              fontWeight: '600'
            }}>
              {p.name}
            </span>
            <span style={{
              fontSize: '11px',
              color: platform === p.id ? 'rgba(255,255,255,0.8)' : 'var(--text-tertiary)'
            }}>
              {p.description}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

export default PlatformSelector
